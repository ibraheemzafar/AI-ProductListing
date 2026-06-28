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
TEST_REPOSITORY: "InMemoryProductUploadRepository | None" = None
TEST_STORAGE_PROVIDER: "InMemoryStorageProvider | None" = None


class InMemoryStorageProvider(StorageProvider):
    def __init__(self) -> None:
        self.files: dict[str, bytes] = {}
        self.deleted_files: list[str] = []
        self.fail_delete = False

    async def upload(self, file_name: str, content: bytes, content_type: str) -> str:
        del content_type
        self.files[file_name] = content
        return f"http://testserver/uploads/{file_name}"

    async def read(self, file_name: str) -> bytes:
        return self.files[file_name]

    async def delete(self, file_name: str) -> None:
        if self.fail_delete:
            raise RuntimeError("storage unavailable")
        self.deleted_files.append(file_name)
        self.files.pop(file_name, None)


class InMemoryProductUploadRepository(ProductUploadRepository):
    def __init__(self) -> None:
        self.images: list[ProductImage] = []
        self.image_owner_by_id: dict[str, str] = {}
        self.linked_image_ids: set[str] = set()
        self.deleted_image_ids: list[str] = []

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
            self.image_owner_by_id[image.id] = user_id

        return product, images

    async def list_images_for_user(self, user_id: str) -> list[ProductImage]:
        return [
            image
            for image in self.images
            if self.image_owner_by_id.get(image.id) == user_id
        ]

    async def get_image_for_user(self, image_id: str, user_id: str) -> ProductImage | None:
        if self.image_owner_by_id.get(image_id) != user_id:
            return None
        return next((image for image in self.images if image.id == image_id), None)

    async def image_has_linked_workspace_assets(self, image_id: str) -> bool:
        return image_id in self.linked_image_ids

    async def delete_image(self, image: ProductImage) -> None:
        self.deleted_image_ids.append(image.id)
        self.images = [item for item in self.images if item.id != image.id]


@pytest.fixture
def client() -> Iterator[TestClient]:
    global TEST_REPOSITORY, TEST_STORAGE_PROVIDER
    repository = InMemoryProductUploadRepository()
    storage_provider = InMemoryStorageProvider()
    TEST_REPOSITORY = repository
    TEST_STORAGE_PROVIDER = storage_provider
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
    TEST_REPOSITORY = None
    TEST_STORAGE_PROVIDER = None


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


def test_unused_image_is_hard_deleted(client: TestClient) -> None:
    client.post(
        "/api/v1/products/images",
        files=[("files", ("front.jpg", JPEG_BYTES, "image/jpeg"))],
    )

    response = client.delete("/api/v1/product-images/image-1")

    assert response.status_code == 204
    list_response = client.get("/api/v1/products/images")
    assert list_response.json()["images"] == []


def test_unused_image_unversioned_alias_is_hard_deleted(client: TestClient) -> None:
    client.post(
        "/api/v1/products/images",
        files=[("files", ("front.jpg", JPEG_BYTES, "image/jpeg"))],
    )

    response = client.delete("/api/product-images/image-1")

    assert response.status_code == 204
    assert client.get("/api/v1/products/images").json()["images"] == []


def test_linked_image_deletion_is_blocked(client: TestClient) -> None:
    assert TEST_REPOSITORY is not None
    TEST_REPOSITORY.linked_image_ids.add("image-1")
    client.post(
        "/api/v1/products/images",
        files=[("files", ("front.jpg", JPEG_BYTES, "image/jpeg"))],
    )

    response = client.delete("/api/v1/product-images/image-1")

    assert response.status_code == 400
    assert (
        response.json()["error"]["message"]
        == "This image is linked to a listing. Delete the listing first."
    )
    assert client.get("/api/v1/products/images").json()["images"][0]["id"] == "image-1"


def test_other_user_cannot_delete_image(client: TestClient) -> None:
    client.post(
        "/api/v1/products/images",
        files=[("files", ("front.jpg", JPEG_BYTES, "image/jpeg"))],
    )
    assert TEST_REPOSITORY is not None
    assert TEST_STORAGE_PROVIDER is not None
    repository = TEST_REPOSITORY
    storage_provider = TEST_STORAGE_PROVIDER
    repository.image_owner_by_id["image-1"] = "user-1"
    app = create_app()
    app.dependency_overrides[get_current_user] = lambda: User(
        id="other-user",
        email="other@example.com",
        name="Other Seller",
        avatar_url=None,
        password_hash="hash",
    )
    app.dependency_overrides[get_product_upload_service] = lambda: ProductUploadService(
        repository=repository,
        storage_provider=storage_provider,
    )

    with TestClient(app) as other_client:
        response = other_client.delete("/api/v1/product-images/image-1")

    app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_storage_delete_failure_keeps_image_record(client: TestClient) -> None:
    assert TEST_STORAGE_PROVIDER is not None
    TEST_STORAGE_PROVIDER.fail_delete = True
    client.post(
        "/api/v1/products/images",
        files=[("files", ("front.jpg", JPEG_BYTES, "image/jpeg"))],
    )

    response = client.delete("/api/v1/product-images/image-1")

    assert response.status_code == 400
    assert (
        response.json()["error"]["message"]
        == "Could not delete image storage. Please try again."
    )
    assert client.get("/api/v1/products/images").json()["images"][0]["id"] == "image-1"
