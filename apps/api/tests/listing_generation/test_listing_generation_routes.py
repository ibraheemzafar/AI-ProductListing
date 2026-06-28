from collections.abc import Iterator
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings, get_settings
from app.core.errors import AuthenticationError
from app.core.rate_limit import ai_rate_limiter
from app.features.auth.dependencies import get_current_user
from app.features.auth.models import User
from app.features.listing_generation.dependencies import get_listing_generation_service
from app.features.listing_generation.models import GeneratedListing
from app.features.listing_generation.schemas import GeneratedListingResponse, ListingContent
from app.main import create_app


class FakeListingGenerationService:
    def __init__(self) -> None:
        self.deleted_listing_id: str | None = None

    async def generate_listing(
        self,
        user_id: str,
        analysis_id: str,
    ) -> GeneratedListingResponse:
        assert user_id == "user-1"
        return GeneratedListingResponse.from_model(
            GeneratedListing(
                id="listing-1",
                product_id="product-1",
                analysis_id=analysis_id,
                title="Modern Ceramic Mug",
                short_description="A modern white ceramic mug.",
                long_description="A modern white ceramic mug for coffee, tea, and daily use.",
                seo_keywords=["ceramic mug", "white mug"],
                product_tags=["mug", "ceramic"],
                raw_output=ListingContent(
                    title="Modern Ceramic Mug",
                    short_description="A modern white ceramic mug.",
                    long_description="A modern white ceramic mug for coffee, tea, and daily use.",
                    seo_keywords=["ceramic mug", "white mug"],
                    product_tags=["mug", "ceramic"],
                ).model_dump(),
                created_at=datetime.now(UTC),
            ),
        )

    async def list_generated_listings(
        self,
        user_id: str,
        limit: int,
        offset: int,
    ) -> dict[str, object]:
        assert user_id == "user-1"
        assert limit == 20
        assert offset == 0
        return {
            "listings": [
                {
                    "id": "listing-1",
                    "product_id": "product-1",
                    "analysis_id": "analysis-1",
                    "title": "Modern Ceramic Mug",
                    "short_description": "A modern white ceramic mug.",
                    "image": build_image_payload(),
                    "status": "generated",
                    "created_at": datetime.now(UTC),
                },
            ],
            "total": 1,
            "limit": limit,
            "offset": offset,
        }

    async def get_generated_listing_detail(
        self,
        user_id: str,
        listing_id: str,
    ) -> dict[str, object]:
        assert user_id == "user-1"
        return {
            "id": listing_id,
            "product_id": "product-1",
            "analysis_id": "analysis-1",
            "image": build_image_payload(),
            "analysis": {
                "category": "Home",
                "product_type": "Mug",
                "color": "White",
                "material": "Ceramic",
                "style": "Modern",
                "visible_text_brand": "ACME",
                "target_audience": "Coffee drinkers",
            },
            "listing": {
                "title": "Modern Ceramic Mug",
                "short_description": "A modern white ceramic mug.",
                "long_description": "A modern white ceramic mug for coffee, tea, and daily use.",
                "seo_keywords": ["ceramic mug", "white mug"],
                "product_tags": ["mug", "ceramic"],
            },
            "status": "generated",
            "created_at": datetime.now(UTC),
        }

    async def delete_generated_listing(self, user_id: str, listing_id: str) -> None:
        assert user_id == "user-1"
        self.deleted_listing_id = listing_id


@pytest.fixture
def client() -> Iterator[TestClient]:
    ai_rate_limiter.reset()
    app = create_app()
    app.dependency_overrides[get_current_user] = lambda: User(
        id="user-1",
        email="seller@example.com",
        name="Test Seller",
        avatar_url=None,
        password_hash="hash",
    )
    app.dependency_overrides[get_listing_generation_service] = (
        lambda: FakeListingGenerationService()
    )
    app.dependency_overrides[get_settings] = lambda: Settings(
        ai_rate_limit_requests_per_minute=1,
    )

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    ai_rate_limiter.reset()


def test_generate_listing_returns_structured_listing(client: TestClient) -> None:
    response = client.post("/api/v1/products/analysis/analysis-1/listing")

    assert response.status_code == 200
    payload = response.json()
    assert payload["analysis_id"] == "analysis-1"
    assert payload["listing"]["title"] == "Modern Ceramic Mug"
    assert payload["listing"]["seo_keywords"] == ["ceramic mug", "white mug"]


def test_generate_listing_rate_limits_ai_requests(client: TestClient) -> None:
    first_response = client.post("/api/v1/products/analysis/analysis-1/listing")
    second_response = client.post("/api/v1/products/analysis/analysis-1/listing")

    assert first_response.status_code == 200
    assert second_response.status_code == 429
    assert second_response.json()["error"]["code"] == "rate_limit_exceeded"


def test_list_generated_listings_returns_history(client: TestClient) -> None:
    response = client.get("/api/v1/products/listings")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["listings"][0]["title"] == "Modern Ceramic Mug"
    assert payload["listings"][0]["image"]["id"] == "image-1"


def test_list_generated_listings_returns_standard_validation_error(client: TestClient) -> None:
    response = client.get("/api/v1/products/listings?limit=0")

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_get_generated_listing_detail_returns_related_data(client: TestClient) -> None:
    response = client.get("/api/v1/products/listings/listing-1")

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == "listing-1"
    assert payload["analysis"]["product_type"] == "Mug"
    assert payload["listing"]["product_tags"] == ["mug", "ceramic"]


def test_delete_generated_listing_returns_no_content(client: TestClient) -> None:
    response = client.delete("/api/v1/products/listings/listing-1")

    assert response.status_code == 204


def test_delete_generated_listing_alias_returns_no_content(client: TestClient) -> None:
    response = client.delete("/api/v1/listings/listing-1")

    assert response.status_code == 204


def test_delete_generated_listing_unversioned_alias_returns_no_content(
    client: TestClient,
) -> None:
    response = client.delete("/api/listings/listing-1")

    assert response.status_code == 204


def test_listing_history_requires_authentication() -> None:
    app = create_app()
    app.dependency_overrides[get_current_user] = lambda: (_ for _ in ()).throw(
        AuthenticationError("Missing session"),
    )
    app.dependency_overrides[get_listing_generation_service] = (
        lambda: FakeListingGenerationService()
    )

    with TestClient(app) as test_client:
        response = test_client.get("/api/v1/products/listings")

    app.dependency_overrides.clear()

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "authentication_failed"


def build_image_payload() -> dict[str, object]:
    return {
        "id": "image-1",
        "product_id": "product-1",
        "original_filename": "mug.jpg",
        "image_url": "http://testserver/uploads/mug.jpg",
        "content_type": "image/jpeg",
        "size_bytes": 1000,
        "created_at": datetime.now(UTC),
    }
