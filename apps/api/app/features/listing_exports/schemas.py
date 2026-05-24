from datetime import datetime

from pydantic import BaseModel

from app.features.ai_analysis.models import ProductAnalysisResult
from app.features.ai_analysis.schemas import ProductAttributes
from app.features.listing_generation.models import GeneratedListing


class ExportListingContent(BaseModel):
    title: str
    short_description: str
    long_description: str
    seo_keywords: list[str]
    product_tags: list[str]


class ListingJsonExportResponse(BaseModel):
    listing_id: str
    product_id: str
    analysis_id: str
    product_image_url: str
    product_analysis: ProductAttributes
    generated_listing: ExportListingContent
    created_at: datetime

    @classmethod
    def from_models(
        cls,
        listing: GeneratedListing,
        analysis: ProductAnalysisResult,
        product_image_url: str,
    ) -> "ListingJsonExportResponse":
        return cls(
            listing_id=listing.id,
            product_id=listing.product_id,
            analysis_id=listing.analysis_id,
            product_image_url=product_image_url,
            product_analysis=ProductAttributes(
                category=analysis.category,
                product_type=analysis.product_type,
                color=analysis.color,
                material=analysis.material,
                style=analysis.style,
                visible_text_brand=analysis.visible_text_brand,
                target_audience=analysis.target_audience,
            ),
            generated_listing=ExportListingContent(
                title=listing.title,
                short_description=listing.short_description,
                long_description=listing.long_description,
                seo_keywords=listing.seo_keywords,
                product_tags=listing.product_tags,
            ),
            created_at=listing.created_at,
        )


class ListingCsvExport(BaseModel):
    filename: str
    content: str
    media_type: str = "text/csv; charset=utf-8"
