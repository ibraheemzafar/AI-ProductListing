from datetime import UTC, datetime
from typing import Protocol

from sqlalchemy import desc, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.ai_analysis.models import AiRequestLog
from app.features.listing_generation.models import GeneratedListing
from app.features.listing_generation.schemas import ListingContent
from app.features.listing_improvement.models import ListingVersion
from app.features.product_uploads.models import Product
from app.features.seo_evaluation.models import SeoAnalysis

ImprovementInput = tuple[GeneratedListing, SeoAnalysis]


class ListingImprovementRepository(Protocol):
    async def get_listing_with_latest_seo_for_user(
        self,
        listing_id: str,
        user_id: str,
    ) -> ImprovementInput | None:
        pass

    async def create_listing_version(
        self,
        listing: GeneratedListing,
        content: ListingContent,
    ) -> ListingVersion:
        pass

    async def list_versions_for_user(
        self,
        listing_id: str,
        user_id: str,
    ) -> list[ListingVersion] | None:
        pass

    async def accept_version_for_user(
        self,
        listing_id: str,
        version_id: str,
        user_id: str,
    ) -> tuple[GeneratedListing, ListingVersion] | None:
        pass

    async def create_request_log(self, log: AiRequestLog) -> None:
        pass


class SQLAlchemyListingImprovementRepository:
    def __init__(self, database_session: AsyncSession) -> None:
        self._database_session = database_session

    async def get_listing_with_latest_seo_for_user(
        self,
        listing_id: str,
        user_id: str,
    ) -> ImprovementInput | None:
        listing_result = await self._database_session.execute(
            select(GeneratedListing)
            .join(Product, Product.id == GeneratedListing.product_id)
            .where(
                GeneratedListing.id == listing_id,
                Product.user_id == user_id,
                GeneratedListing.deleted_at.is_(None),
                GeneratedListing.status != "deleted",
            ),
        )
        listing = listing_result.scalar_one_or_none()
        if listing is None:
            return None

        seo_result = await self._database_session.execute(
            select(SeoAnalysis)
            .where(SeoAnalysis.listing_id == listing_id)
            .order_by(desc(SeoAnalysis.created_at))
            .limit(1),
        )
        seo_analysis = seo_result.scalar_one_or_none()
        if seo_analysis is None:
            return None

        return listing, seo_analysis

    async def create_listing_version(
        self,
        listing: GeneratedListing,
        content: ListingContent,
    ) -> ListingVersion:
        version_number_result = await self._database_session.execute(
            select(func.coalesce(func.max(ListingVersion.version_number), 0)).where(
                ListingVersion.listing_id == listing.id,
            ),
        )
        version_number = int(version_number_result.scalar_one()) + 1
        version = ListingVersion(
            listing_id=listing.id,
            product_id=listing.product_id,
            version_number=version_number,
            title=content.title,
            short_description=content.short_description,
            long_description=content.long_description,
            seo_keywords=content.seo_keywords,
            product_tags=content.product_tags,
            source="ai_improvement",
            is_accepted=False,
            raw_output=content.model_dump(),
        )
        self._database_session.add(version)
        await self._database_session.commit()
        await self._database_session.refresh(version)
        return version

    async def list_versions_for_user(
        self,
        listing_id: str,
        user_id: str,
    ) -> list[ListingVersion] | None:
        listing_exists = await self._listing_exists_for_user(
            listing_id=listing_id,
            user_id=user_id,
        )
        if not listing_exists:
            return None

        result = await self._database_session.execute(
            select(ListingVersion)
            .where(ListingVersion.listing_id == listing_id)
            .order_by(desc(ListingVersion.version_number)),
        )
        return list(result.scalars().all())

    async def accept_version_for_user(
        self,
        listing_id: str,
        version_id: str,
        user_id: str,
    ) -> tuple[GeneratedListing, ListingVersion] | None:
        listing_result = await self._database_session.execute(
            select(GeneratedListing)
            .join(Product, Product.id == GeneratedListing.product_id)
            .where(
                GeneratedListing.id == listing_id,
                Product.user_id == user_id,
                GeneratedListing.deleted_at.is_(None),
                GeneratedListing.status != "deleted",
            ),
        )
        listing = listing_result.scalar_one_or_none()
        if listing is None:
            return None

        version = await self._database_session.get(ListingVersion, version_id)
        if version is None or version.listing_id != listing_id:
            return None

        listing.title = version.title
        listing.short_description = version.short_description
        listing.long_description = version.long_description
        listing.seo_keywords = version.seo_keywords
        listing.product_tags = version.product_tags
        listing.raw_output = version.raw_output

        await self._database_session.execute(
            update(ListingVersion)
            .where(ListingVersion.listing_id == listing_id)
            .values(is_accepted=False, accepted_at=None),
        )
        version.is_accepted = True
        version.accepted_at = datetime.now(UTC)

        await self._database_session.commit()
        await self._database_session.refresh(listing)
        await self._database_session.refresh(version)
        return listing, version

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
