from typing import Protocol

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.ai_analysis.models import ProductAnalysisResult
from app.features.image_enhancement.models import EnhancedImage
from app.features.lifestyle_generation.models import GeneratedImage
from app.features.product_uploads.models import Product, ProductImage


class ProductUploadRepository(Protocol):
    async def create_product_with_images(
        self,
        user_id: str,
        images: list[ProductImage],
    ) -> tuple[Product, list[ProductImage]]:
        pass

    async def list_images_for_user(self, user_id: str) -> list[ProductImage]:
        pass

    async def get_image_for_user(self, image_id: str, user_id: str) -> ProductImage | None:
        pass

    async def image_has_linked_workspace_assets(self, image_id: str) -> bool:
        pass

    async def delete_image(self, image: ProductImage) -> None:
        pass


class SQLAlchemyProductUploadRepository:
    def __init__(self, database_session: AsyncSession) -> None:
        self._database_session = database_session

    async def create_product_with_images(
        self,
        user_id: str,
        images: list[ProductImage],
    ) -> tuple[Product, list[ProductImage]]:
        product = Product(user_id=user_id, title=None, category=None)
        self._database_session.add(product)
        await self._database_session.flush()

        for image in images:
            image.product_id = product.id
            self._database_session.add(image)

        await self._database_session.commit()
        await self._database_session.refresh(product)
        for image in images:
            await self._database_session.refresh(image)

        return product, images

    async def list_images_for_user(self, user_id: str) -> list[ProductImage]:
        result = await self._database_session.execute(
            select(ProductImage)
            .join(Product, Product.id == ProductImage.product_id)
            .where(Product.user_id == user_id)
            .order_by(desc(ProductImage.created_at)),
        )
        return list(result.scalars().all())

    async def get_image_for_user(self, image_id: str, user_id: str) -> ProductImage | None:
        result = await self._database_session.execute(
            select(ProductImage)
            .join(Product, Product.id == ProductImage.product_id)
            .where(ProductImage.id == image_id, Product.user_id == user_id),
        )
        return result.scalar_one_or_none()

    async def image_has_linked_workspace_assets(self, image_id: str) -> bool:
        linked_checks = (
            select(ProductAnalysisResult.id).where(ProductAnalysisResult.image_id == image_id),
            select(EnhancedImage.id).where(EnhancedImage.original_image_id == image_id),
            select(GeneratedImage.id).where(GeneratedImage.source_product_image_id == image_id),
        )

        for statement in linked_checks:
            result = await self._database_session.execute(statement.limit(1))
            if result.scalar_one_or_none() is not None:
                return True
        return False

    async def delete_image(self, image: ProductImage) -> None:
        await self._database_session.delete(image)
        await self._database_session.commit()
