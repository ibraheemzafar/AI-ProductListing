from collections.abc import Iterator
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from app.core.errors import AuthenticationError
from app.features.auth.dependencies import get_current_user
from app.features.auth.models import User
from app.features.marketplace_optimization.dependencies import (
    get_marketplace_optimization_service,
)
from app.features.marketplace_optimization.models import MarketplaceOptimization
from app.features.marketplace_optimization.schemas import MarketplaceOptimizationResponse
from app.main import create_app


class FakeMarketplaceOptimizationService:
    async def optimize_listing(
        self,
        user_id: str,
        listing_id: str,
        marketplace: str,
    ) -> MarketplaceOptimizationResponse:
        assert user_id == "user-1"
        return MarketplaceOptimizationResponse.from_model(
            MarketplaceOptimization(
                id="marketplace-1",
                listing_id=listing_id,
                product_id="product-1",
                marketplace=marketplace,
                optimized_title="Amazon-Ready Cotton T-Shirt",
                optimized_description="A marketplace-ready product description.",
                bullet_points=["Soft cotton", "Everyday fit"],
                keywords_tags=["cotton t-shirt", "black tee"],
                platform_notes="Keep claims factual.",
                raw_output={},
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
    app.dependency_overrides[get_marketplace_optimization_service] = (
        lambda: FakeMarketplaceOptimizationService()
    )

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def test_optimize_listing_for_marketplace_returns_structured_content(client: TestClient) -> None:
    response = client.post(
        "/api/v1/products/listings/listing-1/marketplace-optimizations",
        json={"marketplace": "amazon"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["marketplace"] == "amazon"
    assert payload["optimization"]["optimized_title"] == "Amazon-Ready Cotton T-Shirt"
    assert payload["optimization"]["bullet_points"] == ["Soft cotton", "Everyday fit"]


def test_optimize_listing_for_marketplace_validates_marketplace(client: TestClient) -> None:
    response = client.post(
        "/api/v1/products/listings/listing-1/marketplace-optimizations",
        json={"marketplace": "ebay"},
    )

    assert response.status_code == 422


def test_optimize_listing_for_marketplace_requires_authentication() -> None:
    app = create_app()
    app.dependency_overrides[get_current_user] = lambda: (_ for _ in ()).throw(
        AuthenticationError("Authentication required"),
    )
    app.dependency_overrides[get_marketplace_optimization_service] = (
        lambda: FakeMarketplaceOptimizationService()
    )

    with TestClient(app) as test_client:
        response = test_client.post(
            "/api/v1/products/listings/listing-1/marketplace-optimizations",
            json={"marketplace": "shopify"},
        )

    app.dependency_overrides.clear()
    assert response.status_code == 401
