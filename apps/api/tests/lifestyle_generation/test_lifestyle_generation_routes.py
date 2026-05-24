from collections.abc import Iterator
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from app.core.errors import AuthenticationError
from app.features.auth.dependencies import get_current_user
from app.features.auth.models import User
from app.features.lifestyle_generation.dependencies import get_lifestyle_generation_service
from app.features.lifestyle_generation.models import GeneratedImage
from app.features.lifestyle_generation.schemas import (
    GeneratedImageGalleryResponse,
    GeneratedImageResponse,
)
from app.main import create_app


class FakeLifestyleGenerationService:
    async def generate_lifestyle_scene(
        self,
        user_id: str,
        listing_id: str,
        category: str,
        custom_prompt: str | None,
    ) -> GeneratedImageResponse:
        assert user_id == "user-1"
        return GeneratedImageResponse.from_model(
            build_generated_image(
                listing_id=listing_id,
                category=category,
                custom_prompt=custom_prompt,
            ),
        )

    async def list_generated_images(
        self,
        user_id: str,
        listing_id: str,
    ) -> GeneratedImageGalleryResponse:
        assert user_id == "user-1"
        return GeneratedImageGalleryResponse(
            images=[
                GeneratedImageResponse.from_model(
                    build_generated_image(listing_id=listing_id),
                ),
            ],
        )

    async def download_generated_image(
        self,
        user_id: str,
        listing_id: str,
        image_id: str,
    ) -> tuple[bytes, str, str]:
        assert user_id == "user-1"
        assert listing_id == "listing-1"
        assert image_id == "generated-1"
        return b"generated-png", "image/png", "listing-1-marketplace_hero_image.png"

    async def delete_generated_image(
        self,
        user_id: str,
        listing_id: str,
        image_id: str,
    ) -> None:
        assert user_id == "user-1"
        assert listing_id == "listing-1"
        assert image_id == "generated-1"


@pytest.fixture
def client() -> Iterator[TestClient]:
    app = create_app()
    app.dependency_overrides[get_current_user] = lambda: User(
        id="user-1",
        email="seller@example.com",
        name="Test Seller",
        avatar_url=None,
        password_hash="hash",
    )
    app.dependency_overrides[get_lifestyle_generation_service] = (
        lambda: FakeLifestyleGenerationService()
    )

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def test_generate_lifestyle_scene_returns_generated_image(client: TestClient) -> None:
    response = client.post(
        "/api/v1/products/listings/listing-1/generated-images",
        json={
            "category": "wooden_table_setup",
            "custom_prompt": "Use warm window light",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["category"] == "wooden_table_setup"
    assert payload["generated_image_url"] == "http://testserver/uploads/generated.png"


def test_list_lifestyle_scenes_returns_gallery(client: TestClient) -> None:
    response = client.get("/api/v1/products/listings/listing-1/generated-images")

    assert response.status_code == 200
    payload = response.json()
    assert payload["images"][0]["category"] == "marketplace_hero_image"


def test_download_lifestyle_scene_returns_image(client: TestClient) -> None:
    response = client.get(
        "/api/v1/products/listings/listing-1/generated-images/generated-1/download",
    )

    assert response.status_code == 200
    assert response.content == b"generated-png"
    assert response.headers["content-type"] == "image/png"


def test_delete_lifestyle_scene_returns_no_content(client: TestClient) -> None:
    response = client.delete("/api/v1/products/listings/listing-1/generated-images/generated-1")

    assert response.status_code == 204


def test_generate_lifestyle_scene_validates_preset(client: TestClient) -> None:
    response = client.post(
        "/api/v1/products/listings/listing-1/generated-images",
        json={"category": "rainforest"},
    )

    assert response.status_code == 422


def test_generate_lifestyle_scene_requires_authentication() -> None:
    app = create_app()
    app.dependency_overrides[get_current_user] = lambda: (_ for _ in ()).throw(
        AuthenticationError("Authentication required"),
    )
    app.dependency_overrides[get_lifestyle_generation_service] = (
        lambda: FakeLifestyleGenerationService()
    )

    with TestClient(app) as test_client:
        response = test_client.post(
            "/api/v1/products/listings/listing-1/generated-images",
            json={"category": "luxury_product_shot"},
        )

    app.dependency_overrides.clear()
    assert response.status_code == 401


def build_generated_image(
    listing_id: str,
    category: str = "marketplace_hero_image",
    custom_prompt: str | None = None,
) -> GeneratedImage:
    return GeneratedImage(
        id="generated-1",
        user_id="user-1",
        product_id="product-1",
        listing_id=listing_id,
        source_product_image_id="image-1",
        source_enhanced_image_id=None,
        category=category,
        custom_prompt=custom_prompt,
        prompt="Generate a product lifestyle scene.",
        provider="fake-images",
        storage_filename="generated.png",
        generated_image_url="http://testserver/uploads/generated.png",
        content_type="image/png",
        size_bytes=12,
        generation_time_ms=100,
        status="success",
        created_at=datetime.now(UTC),
    )
