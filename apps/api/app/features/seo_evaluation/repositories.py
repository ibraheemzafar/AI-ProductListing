from typing import Protocol

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.ai_analysis.models import AiRequestLog
from app.features.listing_generation.models import GeneratedListing
from app.features.product_uploads.models import Product
from app.features.seo_evaluation.models import SeoAnalysis
from app.features.seo_evaluation.schemas import SeoEvaluationContent


class SeoEvaluationRepository(Protocol):
    async def get_listing_for_user(
        self,
        listing_id: str,
        user_id: str,
    ) -> GeneratedListing | None:
        pass

    async def save_seo_analysis(
        self,
        listing: GeneratedListing,
        analysis: SeoEvaluationContent,
    ) -> SeoAnalysis:
        pass

    async def create_request_log(self, log: AiRequestLog) -> None:
        pass


class SQLAlchemySeoEvaluationRepository:
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

    async def save_seo_analysis(
        self,
        listing: GeneratedListing,
        analysis: SeoEvaluationContent,
    ) -> SeoAnalysis:
        seo_analysis = SeoAnalysis(
            listing_id=listing.id,
            product_id=listing.product_id,
            seo_score=analysis.seo_score,
            readability_score=analysis.readability_score,
            keyword_optimization_feedback=analysis.keyword_optimization_feedback,
            title_quality_feedback=analysis.title_quality_feedback,
            description_quality_feedback=analysis.description_quality_feedback,
            strengths=analysis.strengths,
            weaknesses=analysis.weaknesses,
            improvement_suggestions=analysis.improvement_suggestions,
            raw_output=analysis.model_dump(),
        )
        self._database_session.add(seo_analysis)
        await self._database_session.commit()
        await self._database_session.refresh(seo_analysis)
        return seo_analysis

    async def create_request_log(self, log: AiRequestLog) -> None:
        self._database_session.add(log)
        await self._database_session.commit()
