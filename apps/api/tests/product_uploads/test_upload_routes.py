from collections.abc import Iterator
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from app.features.auth.dependencies import get_current_user
from app.features.auth.models import User
from app.features.product_uploads.dependencies import get_product_upload_service
from app.features.product_uploads.models import Product, ProductImage
from app.features.product_uploads.repositories import ProductUploadRepository
from app.features.product_uploads.services import ProductUploadService
from app.main import create_app
from app.shared.storage.provider import StorageProvider

JPEG_BYTES = b"\xff\xd8\xff\xe0fake-jpeg"
PNG_BYTES = b"\x89PNG\r\n\x1a\nfake-png"
WEBP_BYTES = b"RIFFxxxxWEBPfake-webp"


class InMemoryStorageProvider(StorageProvider):
    def __init__(self) -> None:
        self.files: dict[str, bytes] = {}

    async def upload(self, file_name: str, content: bytes, content_type: str) -> str:
        del content_type
        self.files[file_name] = content
        return f"http://testserver/uploads/{file_name}"

    async def read(self, file_name: str) -> bytes:
        return self.files[file_name]

    async def delete(self, file_name: str) -> None:
        self.files.pop(file_name, None)


class InMemoryProductUploadRepository(ProductUploadRepository):
    def __init__(self) -> None:
        self.images: list[ProductImage] = []

    async def create_product_with_images(
        self,
        user_id: str,
        images: list[ProductImage],
    ) -> tuple[Product, list[ProductImage]]:
        product = Product(
            id="product-1",
            user_id=user_id,
            title=None,
            category=None,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        for index, image in enumerate(images, start=1):
            image.id = f"image-{index}"
            image.product_id = product.id
            image.created_at = datetime.now(UTC)
            self.images.append(image)

        return product, images

    async def list_images_for_user(self, user_id: str) -> list[ProductImage]:
        del user_id
        return self.images


@pytest.fixture
def client() -> Iterator[TestClient]:
    repository = InMemoryProductUploadRepository()
    storage_provider = InMemoryStorageProvider()
    upload_service = ProductUploadService(repository=repository, storage_provider=storage_provider)
    app = create_app()
    app.dependency_overrides[get_current_user] = lambda: User(
        id="user-1",
        email="seller@example.com",
        name="Test Seller",
        avatar_url=None,
        password_hash="hash",
    )
    app.dependency_overrides[get_product_upload_service] = lambda: upload_service

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def test_upload_product_images_accepts_supported_files(client: TestClient) -> None:
    response = client.post(
        "/api/v1/products/images",
        files=[
            ("files", ("front.jpg", JPEG_BYTES, "image/jpeg")),
            ("files", ("side.png", PNG_BYTES, "image/png")),
        ],
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["product_id"] == "product-1"
    assert len(payload["images"]) == 2
    assert payload["images"][0]["image_url"].startswith("http://testserver/uploads/")


def test_upload_product_images_rejects_invalid_file_type(client: TestClient) -> None:
    response = client.post(
        "/api/v1/products/images",
        files=[("files", ("notes.txt", b"not-image", "text/plain"))],
    )

    assert response.status_code == 400
    assert response.json()["error"]["message"] == "Only JPG, PNG, and WEBP images are supported"


def test_upload_product_images_rejects_large_files(client: TestClient) -> None:
    response = client.post(
        "/api/v1/products/images",
        files=[
            ("files", ("large.jpg", b"\xff\xd8\xff" + b"x" * (10 * 1024 * 1024), "image/jpeg")),
        ],
    )

    assert response.status_code == 400
    assert response.json()["error"]["message"] == "Image must be 10MB or smaller"


def test_list_product_images_returns_uploaded_images(client: TestClient) -> None:
    client.post(
        "/api/v1/products/images",
        files=[("files", ("front.webp", WEBP_BYTES, "image/webp"))],
    )

    response = client.get("/api/v1/products/images")

    assert response.status_code == 200
    assert response.json()["images"][0]["original_filename"] == "front.webp"


def test_upload_product_images_rejects_mismatched_content(client: TestClient) -> None:
    response = client.post(
        "/api/v1/products/images",
        files=[("files", ("front.jpg", b"not-really-a-jpeg", "image/jpeg"))],
    )

    assert response.status_code == 400
    assert (
        response.json()["error"]["message"]
        == "Uploaded file content does not match a supported image format"
    )
