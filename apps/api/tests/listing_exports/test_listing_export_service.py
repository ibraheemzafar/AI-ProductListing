import csv
from datetime import UTC, datetime
from io import StringIO

import pytest

from app.core.errors import AppError
from app.features.ai_analysis.models import ProductAnalysisResult
from app.features.listing_exports.repositories import ListingExportRepository
from app.features.listing_exports.services import ListingExportService
from app.features.listing_generation.models import GeneratedListing
from app.features.product_uploads.models import ProductImage


class InMemoryListingExportRepository(ListingExportRepository):
    def __init__(self, row_exists: bool) -> None:
        self.row_exists = row_exists

    async def get_listing_export_for_user(
        self,
        listing_id: str,
        user_id: str,
    ) -> tuple[GeneratedListing, ProductAnalysisResult, ProductImage] | None:
        del user_id
        if not self.row_exists or listing_id != "listing-1":
            return None
        return build_listing(), build_analysis(), build_image()


@pytest.mark.asyncio
async def test_listing_export_service_returns_json_export() -> None:
    service = ListingExportService(repository=InMemoryListingExportRepository(row_exists=True))

    response = await service.export_listing_as_json(user_id="user-1", listing_id="listing-1")

    assert response.listing_id == "listing-1"
    assert response.product_image_url == "http://testserver/uploads/front.jpg"
    assert response.product_analysis.product_type == "T-shirt"
    assert response.generated_listing.product_tags == ["t-shirt", "cotton", "black"]


@pytest.mark.asyncio
async def test_listing_export_service_hides_missing_or_unauthorized_listing() -> None:
    service = ListingExportService(repository=InMemoryListingExportRepository(row_exists=False))

    with pytest.raises(AppError, match="Generated listing was not found"):
        await service.export_listing_as_json(user_id="user-1", listing_id="other-listing")


@pytest.mark.asyncio
async def test_listing_export_service_returns_shopify_csv() -> None:
    service = ListingExportService(repository=InMemoryListingExportRepository(row_exists=True))

    response = await service.export_listing_as_shopify_csv(
        user_id="user-1",
        listing_id="listing-1",
    )
    rows = list(csv.DictReader(StringIO(response.content)))

    assert response.filename == "listing-1-shopify.csv"
    assert rows == [
        {
            "Title": "Minimal Black Cotton T-Shirt",
            "Body (HTML)": (
                "<p>This minimal black cotton T-shirt is designed for comfortable daily wear.</p>"
            ),
            "Tags": "t-shirt, cotton, black",
            "Image Src": "http://testserver/uploads/front.jpg",
            "SEO Title": "Minimal Black Cotton T-Shirt",
            "SEO Description": "A soft black cotton T-shirt for everyday wear.",
        },
    ]


def build_listing() -> GeneratedListing:
    return GeneratedListing(
        id="listing-1",
        product_id="product-1",
        analysis_id="analysis-1",
        title="Minimal Black Cotton T-Shirt",
        short_description="A soft black cotton T-shirt for everyday wear.",
        long_description=(
            "This minimal black cotton T-shirt is designed for comfortable daily wear."
        ),
        seo_keywords=["black cotton t-shirt", "minimal shirt"],
        product_tags=["t-shirt", "cotton", "black"],
        raw_output={},
        created_at=datetime.now(UTC),
    )


def build_analysis() -> ProductAnalysisResult:
    return ProductAnalysisResult(
        id="analysis-1",
        product_id="product-1",
        image_id="image-1",
        category="Apparel",
        product_type="T-shirt",
        color="Black",
        material="Cotton",
        style="Minimal",
        visible_text_brand="unknown",
        target_audience="Adults",
        raw_attributes={},
        created_at=datetime.now(UTC),
    )


def build_image() -> ProductImage:
    return ProductImage(
        id="image-1",
        product_id="product-1",
        original_filename="front.jpg",
        storage_filename="front.jpg",
        image_url="http://testserver/uploads/front.jpg",
        content_type="image/jpeg",
        size_bytes=1024,
        created_at=datetime.now(UTC),
    )
