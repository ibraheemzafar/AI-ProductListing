from collections.abc import Iterator
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from app.core.errors import AuthenticationError
from app.features.auth.dependencies import get_current_user
from app.features.auth.models import User
from app.features.image_enhancement.dependencies import get_image_enhancement_service
from app.features.image_enhancement.models import EnhancedImage
from app.features.image_enhancement.schemas import EnhancedImageResponse
from app.main import create_app


class FakeImageEnhancementService:
    async def enhance_listing_image(
        self,
        user_id: str,
        listing_id: str,
        operation: str,
    ) -> EnhancedImageResponse:
        assert user_id == "user-1"
        del listing_id
        return EnhancedImageResponse.from_model(
            EnhancedImage(
                id="enhanced-1",
                product_id="product-1",
                original_image_id="image-1",
                operation=operation,
                provider_name="fake-provider",
                storage_filename="enhanced.png",
                enhanced_image_url="http://testserver/uploads/enhanced.png",
                content_type="image/png",
                size_bytes=12,
                created_at=datetime.now(UTC),
            ),
        )


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
    app.dependency_overrides[get_image_enhancement_service] = (
        lambda: FakeImageEnhancementService()
    )

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def test_enhance_listing_image_returns_enhanced_image(client: TestClient) -> None:
    response = client.post(
        "/api/v1/products/listings/listing-1/image-enhancements",
        json={"operation": "background_removal"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["operation"] == "background_removal"
    assert payload["enhanced_image_url"] == "http://testserver/uploads/enhanced.png"


def test_enhance_listing_image_validates_operation(client: TestClient) -> None:
    response = client.post(
        "/api/v1/products/listings/listing-1/image-enhancements",
        json={"operation": "watermark"},
    )

    assert response.status_code == 422


def test_enhance_listing_image_requires_authentication() -> None:
    app = create_app()
    app.dependency_overrides[get_current_user] = lambda: (_ for _ in ()).throw(
        AuthenticationError("Authentication required"),
    )
    app.dependency_overrides[get_image_enhancement_service] = lambda: FakeImageEnhancementService()

    with TestClient(app) as test_client:
        response = test_client.post(
            "/api/v1/products/listings/listing-1/image-enhancements",
            json={"operation": "background_removal"},
        )

    app.dependency_overrides.clear()
    assert response.status_code == 401
