from datetime import datetime

from pydantic import BaseModel

from app.features.listing_generation.models import GeneratedListing
from app.features.listing_generation.schemas import ListingContent
from app.features.listing_improvement.models import ListingVersion


class ListingVersionResponse(BaseModel):
    id: str
    listing_id: str
    product_id: str
    version_number: int
    listing: ListingContent
    source: str
    is_accepted: bool
    created_at: datetime
    accepted_at: datetime | None

    @classmethod
    def from_model(cls, version: ListingVersion) -> "ListingVersionResponse":
        return cls(
            id=version.id,
            listing_id=version.listing_id,
            product_id=version.product_id,
            version_number=version.version_number,
            listing=ListingContent(
                title=version.title,
                short_description=version.short_description,
                long_description=version.long_description,
                seo_keywords=version.seo_keywords,
                product_tags=version.product_tags,
            ),
            source=version.source,
            is_accepted=version.is_accepted,
            created_at=version.created_at,
            accepted_at=version.accepted_at,
        )


class ListingImprovementResponse(BaseModel):
    original_listing: ListingContent
    improved_version: ListingVersionResponse

    @classmethod
    def from_models(
        cls,
        original_listing: GeneratedListing,
        version: ListingVersion,
    ) -> "ListingImprovementResponse":
        return cls(
            original_listing=ListingContent(
                title=original_listing.title,
                short_description=original_listing.short_description,
                long_description=original_listing.long_description,
                seo_keywords=original_listing.seo_keywords,
                product_tags=original_listing.product_tags,
            ),
            improved_version=ListingVersionResponse.from_model(version),
        )


class ListingVersionHistoryResponse(BaseModel):
    versions: list[ListingVersionResponse]


class AcceptListingVersionResponse(BaseModel):
    listing_id: str
    accepted_version: ListingVersionResponse
    active_listing: ListingContent

    @classmethod
    def from_models(
        cls,
        listing: GeneratedListing,
        version: ListingVersion,
    ) -> "AcceptListingVersionResponse":
        return cls(
            listing_id=listing.id,
            accepted_version=ListingVersionResponse.from_model(version),
            active_listing=ListingContent(
                title=listing.title,
                short_description=listing.short_description,
                long_description=listing.long_description,
                seo_keywords=listing.seo_keywords,
                product_tags=listing.product_tags,
            ),
        )
