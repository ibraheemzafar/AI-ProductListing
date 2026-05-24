from collections.abc import Iterator
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from app.features.ai_analysis.schemas import ProductAttributes
from app.features.auth.dependencies import get_current_user
from app.features.auth.models import User
from app.features.listing_exports.dependencies import get_listing_export_service
from app.features.listing_exports.schemas import (
    ExportListingContent,
    ListingCsvExport,
    ListingJsonExportResponse,
)
from app.main import create_app


class FakeListingExportService:
    async def export_listing_as_json(
        self,
        user_id: str,
        listing_id: str,
    ) -> ListingJsonExportResponse:
        assert user_id == "user-1"
        return ListingJsonExportResponse(
            listing_id=listing_id,
            product_id="product-1",
            analysis_id="analysis-1",
            product_image_url="http://testserver/uploads/mug.jpg",
            product_analysis=ProductAttributes(
                category="Home",
                product_type="Mug",
                color="White",
                material="Ceramic",
                style="Modern",
                visible_text_brand="ACME",
                target_audience="Coffee drinkers",
            ),
            generated_listing=ExportListingContent(
                title="Modern Ceramic Mug",
                short_description="A modern white ceramic mug.",
                long_description="A modern white ceramic mug for coffee, tea, and daily use.",
                seo_keywords=["ceramic mug", "white mug"],
                product_tags=["mug", "ceramic"],
            ),
            created_at=datetime.now(UTC),
        )

    async def export_listing_as_shopify_csv(
        self,
        user_id: str,
        listing_id: str,
    ) -> ListingCsvExport:
        assert user_id == "user-1"
        return ListingCsvExport(
            filename=f"{listing_id}-shopify.csv",
            content=(
                "Title,Body (HTML),Tags,Image Src,SEO Title,SEO Description\n"
                "Modern Ceramic Mug,<p>A modern white ceramic mug.</p>,"
                "\"mug, ceramic\",http://testserver/uploads/mug.jpg,"
                "Modern Ceramic Mug,A modern white ceramic mug.\n"
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
    app.dependency_overrides[get_listing_export_service] = lambda: FakeListingExportService()

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def test_export_listing_as_json_returns_saved_listing_data(client: TestClient) -> None:
    response = client.get("/api/v1/products/listings/listing-1/export/json")

    assert response.status_code == 200
    payload = response.json()
    assert payload["listing_id"] == "listing-1"
    assert payload["product_image_url"] == "http://testserver/uploads/mug.jpg"
    assert payload["product_analysis"]["product_type"] == "Mug"
    assert payload["generated_listing"]["title"] == "Modern Ceramic Mug"


def test_export_listing_as_shopify_csv_returns_download(client: TestClient) -> None:
    response = client.get("/api/v1/products/listings/listing-1/export/shopify.csv")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert response.headers["content-disposition"] == 'attachment; filename="listing-1-shopify.csv"'
    assert "Title,Body (HTML),Tags,Image Src,SEO Title,SEO Description" in response.text
    assert "Modern Ceramic Mug" in response.text
