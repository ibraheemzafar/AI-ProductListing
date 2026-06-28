from typing import Protocol

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.ai_analysis.models import AiRequestLog
from app.features.listing_generation.models import GeneratedListing
from app.features.marketplace_optimization.models import MarketplaceOptimization
from app.features.marketplace_optimization.schemas import (
    Marketplace,
    MarketplaceOptimizationContent,
)
from app.features.product_uploads.models import Product


class MarketplaceOptimizationRepository(Protocol):
    async def get_listing_for_user(
        self,
        listing_id: str,
        user_id: str,
    ) -> GeneratedListing | None:
        pass

    async def get_optimization(
        self,
        listing_id: str,
        marketplace: Marketplace,
    ) -> MarketplaceOptimization | None:
        pass

    async def list_optimizations(
        self,
        listing_id: str,
    ) -> list[MarketplaceOptimization]:
        pass

    async def save_optimization(
        self,
        listing: GeneratedListing,
        marketplace: Marketplace,
        content: MarketplaceOptimizationContent,
    ) -> MarketplaceOptimization:
        pass

    async def create_request_log(self, log: AiRequestLog) -> None:
        pass


class SQLAlchemyMarketplaceOptimizationRepository:
    def __init__(self, database_session: AsyncSession) -> None:
        self._database_session = database_session

    async def get_listing_for_user(
        self,
        listing_id: str,
        user_id: str,
    ) -> GeneratedListing | None:
        result = await self._database_session.execute(
            select(GeneratedListing)
            .join(Product, Product.id == GeneratedListing.product_id)
            .where(
                GeneratedListing.id == listing_id,
                Product.user_id == user_id,
                GeneratedListing.deleted_at.is_(None),
                GeneratedListing.status != "deleted",
            ),
        )
        return result.scalar_one_or_none()

    async def get_optimization(
        self,
        listing_id: str,
        marketplace: Marketplace,
    ) -> MarketplaceOptimization | None:
        result = await self._database_session.execute(
            select(MarketplaceOptimization)
            .where(
                MarketplaceOptimization.listing_id == listing_id,
                MarketplaceOptimization.marketplace == marketplace,
            )
            .order_by(desc(MarketplaceOptimization.created_at))
            .limit(1),
        )
        return result.scalar_one_or_none()

    async def list_optimizations(
        self,
        listing_id: str,
    ) -> list[MarketplaceOptimization]:
        result = await self._database_session.execute(
            select(MarketplaceOptimization)
            .where(MarketplaceOptimization.listing_id == listing_id)
            .order_by(desc(MarketplaceOptimization.created_at)),
        )
        return list(result.scalars().all())

    async def save_optimization(
        self,
        listing: GeneratedListing,
        marketplace: Marketplace,
        content: MarketplaceOptimizationContent,
    ) -> MarketplaceOptimization:
        optimization = MarketplaceOptimization(
            listing_id=listing.id,
            product_id=listing.product_id,
            marketplace=marketplace,
            optimized_title=content.optimized_title,
            optimized_description=content.optimized_description,
            bullet_points=content.bullet_points,
            keywords_tags=content.keywords_tags,
            platform_notes=content.platform_notes,
            raw_output=content.model_dump(),
        )
        self._database_session.add(optimization)
        await self._database_session.commit()
        await self._database_session.refresh(optimization)
        return optimization

    async def create_request_log(self, log: AiRequestLog) -> None:
        self._database_session.add(log)
        await self._database_session.commit()
