from collections.abc import Iterator
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from app.features.auth.dependencies import get_current_user
from app.features.auth.models import User
from app.features.listing_generation.models import GeneratedListing
from app.features.listing_generation.schemas import ListingContent
from app.features.listing_improvement.dependencies import get_listing_improvement_service
from app.features.listing_improvement.models import ListingVersion
from app.features.listing_improvement.schemas import (
    AcceptListingVersionResponse,
    ListingImprovementResponse,
    ListingVersionHistoryResponse,
)
from app.main import create_app


class FakeListingImprovementService:
    async def improve_listing(
        self,
        user_id: str,
        listing_id: str,
    ) -> ListingImprovementResponse:
        assert user_id == "user-1"
        return ListingImprovementResponse(
            original_listing=build_original_content(),
            improved_version=ListingImprovementResponse.from_models(
                original_listing=build_fake_generated_listing(listing_id),
                version=build_version(listing_id),
            ).improved_version,
        )

    async def list_versions(
        self,
        user_id: str,
        listing_id: str,
    ) -> ListingVersionHistoryResponse:
        assert user_id == "user-1"
        return ListingVersionHistoryResponse(
            versions=[
                ListingImprovementResponse.from_models(
                    original_listing=build_fake_generated_listing(listing_id),
                    version=build_version(listing_id),
                ).improved_version,
            ],
        )

    async def accept_version(
        self,
        user_id: str,
        listing_id: str,
        version_id: str,
    ) -> AcceptListingVersionResponse:
        assert user_id == "user-1"
        version = build_version(listing_id, version_id=version_id, accepted=True)
        return AcceptListingVersionResponse(
            listing_id=listing_id,
            accepted_version=ListingImprovementResponse.from_models(
                original_listing=build_fake_generated_listing(listing_id),
                version=version,
            ).improved_version,
            active_listing=build_improved_content(),
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
    app.dependency_overrides[get_listing_improvement_service] = (
        lambda: FakeListingImprovementService()
    )

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def test_improve_listing_returns_before_after(client: TestClient) -> None:
    response = client.post("/api/v1/products/listings/listing-1/improvements")

    assert response.status_code == 200
    payload = response.json()
    assert payload["original_listing"]["title"] == "Minimal Black Cotton T-Shirt"
    assert payload["improved_version"]["listing"]["title"] == "Black Cotton T-Shirt"


def test_list_versions_returns_version_history(client: TestClient) -> None:
    response = client.get("/api/v1/products/listings/listing-1/versions")

    assert response.status_code == 200
    payload = response.json()
    assert payload["versions"][0]["version_number"] == 1


def test_accept_version_returns_active_listing(client: TestClient) -> None:
    response = client.post("/api/v1/products/listings/listing-1/versions/version-1/accept")

    assert response.status_code == 200
    payload = response.json()
    assert payload["accepted_version"]["is_accepted"] is True
    assert payload["active_listing"]["title"] == "Black Cotton T-Shirt"


def build_original_content() -> ListingContent:
    return ListingContent(
        title="Minimal Black Cotton T-Shirt",
        short_description="A soft black cotton T-shirt.",
        long_description="A simple black cotton T-shirt.",
        seo_keywords=["black cotton t-shirt"],
        product_tags=["t-shirt"],
    )


def build_improved_content() -> ListingContent:
    return ListingContent(
        title="Black Cotton T-Shirt",
        short_description="A breathable black cotton tee.",
        long_description="A soft black cotton T-shirt made for everyday wear.",
        seo_keywords=["black cotton t-shirt", "everyday tee"],
        product_tags=["black t-shirt", "cotton tee"],
    )


def build_fake_generated_listing(listing_id: str) -> GeneratedListing:
    return GeneratedListing(
        id=listing_id,
        product_id="product-1",
        analysis_id="analysis-1",
        title="Minimal Black Cotton T-Shirt",
        short_description="A soft black cotton T-shirt.",
        long_description="A simple black cotton T-shirt.",
        seo_keywords=["black cotton t-shirt"],
        product_tags=["t-shirt"],
        raw_output={},
        created_at=datetime.now(UTC),
    )


def build_version(
    listing_id: str,
    version_id: str = "version-1",
    accepted: bool = False,
) -> ListingVersion:
    content = build_improved_content()
    return ListingVersion(
        id=version_id,
        listing_id=listing_id,
        product_id="product-1",
        version_number=1,
        title=content.title,
        short_description=content.short_description,
        long_description=content.long_description,
        seo_keywords=content.seo_keywords,
        product_tags=content.product_tags,
        source="ai_improvement",
        is_accepted=accepted,
        raw_output=content.model_dump(),
        created_at=datetime.now(UTC),
        accepted_at=datetime.now(UTC) if accepted else None,
    )
