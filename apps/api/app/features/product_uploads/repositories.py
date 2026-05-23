from typing import Protocol

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

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

