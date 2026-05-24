from typing import Protocol

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.ai_analysis.models import ProductAnalysisResult
from app.features.listing_generation.models import GeneratedListing
from app.features.product_uploads.models import Product, ProductImage

ListingExportRow = tuple[GeneratedListing, ProductAnalysisResult, ProductImage]


class ListingExportRepository(Protocol):
    async def get_listing_export_for_user(
        self,
        listing_id: str,
        user_id: str,
    ) -> ListingExportRow | None:
        pass


class SQLAlchemyListingExportRepository:
    def __init__(self, database_session: AsyncSession) -> None:
        self._database_session = database_session

    async def get_listing_export_for_user(
        self,
        listing_id: str,
        user_id: str,
    ) -> ListingExportRow | None:
        result = await self._database_session.execute(
            select(GeneratedListing, ProductAnalysisResult, ProductImage)
            .join(Product, Product.id == GeneratedListing.product_id)
            .join(ProductAnalysisResult, ProductAnalysisResult.id == GeneratedListing.analysis_id)
            .join(ProductImage, ProductImage.id == ProductAnalysisResult.image_id)
            .where(GeneratedListing.id == listing_id, Product.user_id == user_id),
        )
        row = result.one_or_none()
        if row is None:
            return None
        return row[0], row[1], row[2]
