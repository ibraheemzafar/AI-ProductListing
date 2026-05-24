from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.features.ai_analysis.models import ProductAnalysisResult
from app.features.ai_analysis.schemas import ProductAttributes
from app.features.listing_generation.models import GeneratedListing
from app.features.product_uploads.models import ProductImage
from app.features.product_uploads.schemas import UploadedImageResponse


class ListingContent(BaseModel):
    title: str = Field(min_length=1, max_length=70)
    short_description: str = Field(min_length=1, max_length=500)
    long_description: str = Field(min_length=1, max_length=4000)
    seo_keywords: list[str] = Field(min_length=1, max_length=20)
    product_tags: list[str] = Field(min_length=1, max_length=20)

    @field_validator("seo_keywords", "product_tags")
    @classmethod
    def validate_non_empty_values(cls, values: list[str]) -> list[str]:
        cleaned_values = [value.strip() for value in values if value.strip()]
        if not cleaned_values:
            msg = "At least one non-empty value is required"
            raise ValueError(msg)
        return cleaned_values


class GeneratedListingResponse(BaseModel):
    id: str
    product_id: str
    analysis_id: str
    listing: ListingContent
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_model(cls, listing: GeneratedListing) -> "GeneratedListingResponse":
        return cls(
            id=listing.id,
            product_id=listing.product_id,
            analysis_id=listing.analysis_id,
            listing=ListingContent(
                title=listing.title,
                short_description=listing.short_description,
                long_description=listing.long_description,
                seo_keywords=listing.seo_keywords,
                product_tags=listing.product_tags,
            ),
            created_at=listing.created_at,
        )


class ListingHistoryItem(BaseModel):
    id: str
    product_id: str
    analysis_id: str
    title: str
    short_description: str
    image: UploadedImageResponse
    status: str
    created_at: datetime

    @classmethod
    def from_models(
        cls,
        listing: GeneratedListing,
        image: ProductImage,
    ) -> "ListingHistoryItem":
        return cls(
            id=listing.id,
            product_id=listing.product_id,
            analysis_id=listing.analysis_id,
            title=listing.title,
            short_description=listing.short_description,
            image=UploadedImageResponse.from_model(image),
            status="generated",
            created_at=listing.created_at,
        )


class ListingHistoryResponse(BaseModel):
    listings: list[ListingHistoryItem]
    total: int
    limit: int
    offset: int


class ListingDetailResponse(BaseModel):
    id: str
    product_id: str
    analysis_id: str
    image: UploadedImageResponse
    analysis: ProductAttributes
    listing: ListingContent
    status: str
    created_at: datetime

    @classmethod
    def from_models(
        cls,
        listing: GeneratedListing,
        analysis: ProductAnalysisResult,
        image: ProductImage,
    ) -> "ListingDetailResponse":
        return cls(
            id=listing.id,
            product_id=listing.product_id,
            analysis_id=listing.analysis_id,
            image=UploadedImageResponse.from_model(image),
            analysis=ProductAttributes(
                category=analysis.category,
                product_type=analysis.product_type,
                color=analysis.color,
                material=analysis.material,
                style=analysis.style,
                visible_text_brand=analysis.visible_text_brand,
                target_audience=analysis.target_audience,
            ),
            listing=ListingContent(
                title=listing.title,
                short_description=listing.short_description,
                long_description=listing.long_description,
                seo_keywords=listing.seo_keywords,
                product_tags=listing.product_tags,
            ),
            status="generated",
            created_at=listing.created_at,
        )
