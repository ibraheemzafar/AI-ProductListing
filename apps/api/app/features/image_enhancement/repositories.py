from typing import Protocol

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.ai_analysis.models import AiRequestLog
from app.features.image_enhancement.models import EnhancedImage
from app.features.listing_generation.models import GeneratedListing
from app.features.product_uploads.models import Product, ProductImage

ImageEnhancementSource = tuple[GeneratedListing, ProductImage]


class ImageEnhancementRepository(Protocol):
    async def get_listing_image_for_user(
        self,
        listing_id: str,
        user_id: str,
    ) -> ImageEnhancementSource | None:
        pass

    async def save_enhanced_image(self, image: EnhancedImage) -> EnhancedImage:
        pass

    async def create_request_log(self, log: AiRequestLog) -> None:
        pass


class SQLAlchemyImageEnhancementRepository:
    def __init__(self, database_session: AsyncSession) -> None:
        self._database_session = database_session

    async def get_listing_image_for_user(
        self,
        listing_id: str,
        user_id: str,
    ) -> ImageEnhancementSource | None:
        listing_result = await self._database_session.execute(
            select(GeneratedListing)
            .join(Product, Product.id == GeneratedListing.product_id)
            .where(GeneratedListing.id == listing_id, Product.user_id == user_id),
        )
        listing = listing_result.scalar_one_or_none()
        if listing is None:
            return None

        image_result = await self._database_session.execute(
            select(ProductImage)
            .where(ProductImage.product_id == listing.product_id)
            .order_by(desc(ProductImage.created_at))
            .limit(1),
        )
        image = image_result.scalar_one_or_none()
        if image is None:
            return None

        return listing, image

    async def save_enhanced_image(self, image: EnhancedImage) -> EnhancedImage:
        self._database_session.add(image)
        await self._database_session.commit()
        await self._database_session.refresh(image)
        return image

    async def create_request_log(self, log: AiRequestLog) -> None:
        self._database_session.add(log)
        await self._database_session.commit()
