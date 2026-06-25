from typing import Protocol

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.ai_analysis.models import AiRequestLog, ProductAnalysisResult
from app.features.ai_analysis.schemas import ProductAttributes
from app.features.product_uploads.models import Product, ProductImage


class AiAnalysisRepository(Protocol):
    async def get_image_for_user(self, image_id: str, user_id: str) -> ProductImage | None:
        pass

    async def list_analyses_for_image(
        self,
        image_id: str,
        user_id: str,
    ) -> list[ProductAnalysisResult]:
        pass

    async def save_analysis_result(
        self,
        product_id: str,
        image_id: str,
        attributes: ProductAttributes,
    ) -> ProductAnalysisResult:
        pass

    async def create_request_log(self, log: AiRequestLog) -> None:
        pass


class SQLAlchemyAiAnalysisRepository:
    def __init__(self, database_session: AsyncSession) -> None:
        self._database_session = database_session

    async def get_image_for_user(self, image_id: str, user_id: str) -> ProductImage | None:
        result = await self._database_session.execute(
            select(ProductImage)
            .join(Product, Product.id == ProductImage.product_id)
            .where(ProductImage.id == image_id, Product.user_id == user_id),
        )
        return result.scalar_one_or_none()

    async def list_analyses_for_image(
        self,
        image_id: str,
        user_id: str,
    ) -> list[ProductAnalysisResult]:
        result = await self._database_session.execute(
            select(ProductAnalysisResult)
            .join(Product, Product.id == ProductAnalysisResult.product_id)
            .where(ProductAnalysisResult.image_id == image_id, Product.user_id == user_id)
            .order_by(desc(ProductAnalysisResult.created_at)),
        )
        return list(result.scalars().all())

    async def save_analysis_result(
        self,
        product_id: str,
        image_id: str,
        attributes: ProductAttributes,
    ) -> ProductAnalysisResult:
        analysis = ProductAnalysisResult(
            product_id=product_id,
            image_id=image_id,
            category=attributes.category,
            product_type=attributes.product_type,
            color=attributes.color,
            material=attributes.material,
            style=attributes.style,
            visible_text_brand=attributes.visible_text_brand,
            target_audience=attributes.target_audience,
            raw_attributes=attributes.model_dump(),
        )
        self._database_session.add(analysis)

        product = await self._database_session.get(Product, product_id)
        if product:
            product.category = attributes.category

        await self._database_session.commit()
        await self._database_session.refresh(analysis)
        return analysis

    async def create_request_log(self, log: AiRequestLog) -> None:
        self._database_session.add(log)
        await self._database_session.commit()
