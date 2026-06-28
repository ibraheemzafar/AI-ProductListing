from dataclasses import dataclass
from typing import Protocol

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.ai_analysis.models import AiRequestLog, ProductAnalysisResult
from app.features.image_enhancement.models import EnhancedImage
from app.features.lifestyle_generation.models import GeneratedImage
from app.features.listing_generation.models import GeneratedListing
from app.features.product_uploads.models import Product, ProductImage


@dataclass(frozen=True)
class LifestyleGenerationSource:
    listing: GeneratedListing
    product_image: ProductImage
    enhanced_image: EnhancedImage | None


class LifestyleGenerationRepository(Protocol):
    async def get_generation_source_for_user(
        self,
        listing_id: str,
        user_id: str,
    ) -> LifestyleGenerationSource | None:
        pass

    async def save_generated_image(self, image: GeneratedImage) -> GeneratedImage:
        pass

    async def list_generated_images_for_user(
        self,
        listing_id: str,
        user_id: str,
    ) -> list[GeneratedImage] | None:
        pass

    async def get_generated_image_for_user(
        self,
        listing_id: str,
        image_id: str,
        user_id: str,
    ) -> GeneratedImage | None:
        pass

    async def delete_generated_image(self, image: GeneratedImage) -> None:
        pass

    async def create_request_log(self, log: AiRequestLog) -> None:
        pass


class SQLAlchemyLifestyleGenerationRepository:
    def __init__(self, database_session: AsyncSession) -> None:
        self._database_session = database_session

    async def get_generation_source_for_user(
        self,
        listing_id: str,
        user_id: str,
    ) -> LifestyleGenerationSource | None:
        result = await self._database_session.execute(
            select(GeneratedListing, ProductImage)
            .join(Product, Product.id == GeneratedListing.product_id)
            .join(ProductAnalysisResult, ProductAnalysisResult.id == GeneratedListing.analysis_id)
            .join(ProductImage, ProductImage.id == ProductAnalysisResult.image_id)
            .where(
                GeneratedListing.id == listing_id,
                Product.user_id == user_id,
                GeneratedListing.deleted_at.is_(None),
                GeneratedListing.status != "deleted",
            ),
        )
        row = result.one_or_none()
        if row is None:
            return None

        listing, product_image = row[0], row[1]
        enhanced_result = await self._database_session.execute(
            select(EnhancedImage)
            .where(EnhancedImage.product_id == listing.product_id)
            .order_by(desc(EnhancedImage.created_at))
            .limit(1),
        )
        return LifestyleGenerationSource(
            listing=listing,
            product_image=product_image,
            enhanced_image=enhanced_result.scalar_one_or_none(),
        )

    async def save_generated_image(self, image: GeneratedImage) -> GeneratedImage:
        self._database_session.add(image)
        await self._database_session.commit()
        await self._database_session.refresh(image)
        return image

    async def list_generated_images_for_user(
        self,
        listing_id: str,
        user_id: str,
    ) -> list[GeneratedImage] | None:
        listing_exists = await self._listing_exists_for_user(listing_id=listing_id, user_id=user_id)
        if not listing_exists:
            return None

        result = await self._database_session.execute(
            select(GeneratedImage)
            .where(GeneratedImage.listing_id == listing_id, GeneratedImage.user_id == user_id)
            .order_by(desc(GeneratedImage.created_at)),
        )
        return list(result.scalars().all())

    async def get_generated_image_for_user(
        self,
        listing_id: str,
        image_id: str,
        user_id: str,
    ) -> GeneratedImage | None:
        result = await self._database_session.execute(
            select(GeneratedImage).where(
                GeneratedImage.id == image_id,
                GeneratedImage.listing_id == listing_id,
                GeneratedImage.user_id == user_id,
            ),
        )
        return result.scalar_one_or_none()

    async def delete_generated_image(self, image: GeneratedImage) -> None:
        await self._database_session.delete(image)
        await self._database_session.commit()

    async def create_request_log(self, log: AiRequestLog) -> None:
        self._database_session.add(log)
        await self._database_session.commit()

    async def _listing_exists_for_user(self, listing_id: str, user_id: str) -> bool:
        result = await self._database_session.execute(
            select(GeneratedListing.id)
            .join(Product, Product.id == GeneratedListing.product_id)
            .where(
                GeneratedListing.id == listing_id,
                Product.user_id == user_id,
                GeneratedListing.deleted_at.is_(None),
                GeneratedListing.status != "deleted",
            ),
        )
        return result.scalar_one_or_none() is not None
