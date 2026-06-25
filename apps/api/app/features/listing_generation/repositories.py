from typing import Protocol

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.ai_analysis.models import AiRequestLog, ProductAnalysisResult
from app.features.listing_generation.models import GeneratedListing
from app.features.listing_generation.schemas import ListingContent
from app.features.listing_improvement.models import ListingVersion
from app.features.product_uploads.models import Product, ProductImage

ListingHistoryRow = tuple[GeneratedListing, ProductImage]
ListingDetailRow = tuple[GeneratedListing, ProductAnalysisResult, ProductImage]
ListingWithAnalysisRow = tuple[GeneratedListing, ProductAnalysisResult]


class ListingGenerationRepository(Protocol):
    async def get_analysis_for_user(
        self,
        analysis_id: str,
        user_id: str,
    ) -> ProductAnalysisResult | None:
        pass

    async def list_listings_for_analysis(
        self,
        analysis_id: str,
        user_id: str,
    ) -> list[GeneratedListing]:
        pass

    async def save_generated_listing(
        self,
        analysis: ProductAnalysisResult,
        listing: ListingContent,
    ) -> GeneratedListing:
        pass

    async def create_request_log(self, log: AiRequestLog) -> None:
        pass

    async def list_generated_listings_for_user(
        self,
        user_id: str,
        limit: int,
        offset: int,
    ) -> tuple[list[ListingHistoryRow], int]:
        pass

    async def get_generated_listing_detail_for_user(
        self,
        listing_id: str,
        user_id: str,
    ) -> ListingDetailRow | None:
        pass

    async def get_listing_with_analysis_for_user(
        self,
        listing_id: str,
        user_id: str,
    ) -> ListingWithAnalysisRow | None:
        pass

    async def create_listing_version(
        self,
        listing: GeneratedListing,
        content: ListingContent,
        source: str,
    ) -> ListingVersion:
        pass


class SQLAlchemyListingGenerationRepository:
    def __init__(self, database_session: AsyncSession) -> None:
        self._database_session = database_session

    async def get_analysis_for_user(
        self,
        analysis_id: str,
        user_id: str,
    ) -> ProductAnalysisResult | None:
        result = await self._database_session.execute(
            select(ProductAnalysisResult)
            .join(Product, Product.id == ProductAnalysisResult.product_id)
            .where(ProductAnalysisResult.id == analysis_id, Product.user_id == user_id),
        )
        return result.scalar_one_or_none()

    async def list_listings_for_analysis(
        self,
        analysis_id: str,
        user_id: str,
    ) -> list[GeneratedListing]:
        result = await self._database_session.execute(
            select(GeneratedListing)
            .join(Product, Product.id == GeneratedListing.product_id)
            .where(GeneratedListing.analysis_id == analysis_id, Product.user_id == user_id)
            .order_by(desc(GeneratedListing.created_at)),
        )
        return list(result.scalars().all())

    async def save_generated_listing(
        self,
        analysis: ProductAnalysisResult,
        listing: ListingContent,
    ) -> GeneratedListing:
        generated_listing = GeneratedListing(
            product_id=analysis.product_id,
            analysis_id=analysis.id,
            title=listing.title,
            short_description=listing.short_description,
            long_description=listing.long_description,
            seo_keywords=listing.seo_keywords,
            product_tags=listing.product_tags,
            raw_output=listing.model_dump(),
        )
        self._database_session.add(generated_listing)

        product = await self._database_session.get(Product, analysis.product_id)
        if product:
            product.title = listing.title

        await self._database_session.commit()
        await self._database_session.refresh(generated_listing)
        return generated_listing

    async def create_request_log(self, log: AiRequestLog) -> None:
        self._database_session.add(log)
        await self._database_session.commit()

    async def list_generated_listings_for_user(
        self,
        user_id: str,
        limit: int,
        offset: int,
    ) -> tuple[list[ListingHistoryRow], int]:
        base_filters = (Product.user_id == user_id,)
        # The list shows one card per product, so count distinct products (not rows) and
        # keep only the latest listing per product.
        total_result = await self._database_session.execute(
            select(func.count(func.distinct(GeneratedListing.product_id)))
            .join(Product, Product.id == GeneratedListing.product_id)
            .where(*base_filters),
        )
        total = total_result.scalar_one()

        latest_listing_ids = (
            select(GeneratedListing.id)
            .join(Product, Product.id == GeneratedListing.product_id)
            .where(*base_filters)
            .distinct(GeneratedListing.product_id)
            .order_by(GeneratedListing.product_id, desc(GeneratedListing.created_at))
            .subquery()
        )

        result = await self._database_session.execute(
            select(GeneratedListing, ProductImage)
            .join(Product, Product.id == GeneratedListing.product_id)
            .join(ProductAnalysisResult, ProductAnalysisResult.id == GeneratedListing.analysis_id)
            .join(ProductImage, ProductImage.id == ProductAnalysisResult.image_id)
            .where(GeneratedListing.id.in_(select(latest_listing_ids.c.id)))
            .order_by(desc(GeneratedListing.created_at))
            .limit(limit)
            .offset(offset),
        )
        rows = [(row[0], row[1]) for row in result.all()]
        return rows, total

    async def get_generated_listing_detail_for_user(
        self,
        listing_id: str,
        user_id: str,
    ) -> ListingDetailRow | None:
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

    async def get_listing_with_analysis_for_user(
        self,
        listing_id: str,
        user_id: str,
    ) -> ListingWithAnalysisRow | None:
        result = await self._database_session.execute(
            select(GeneratedListing, ProductAnalysisResult)
            .join(Product, Product.id == GeneratedListing.product_id)
            .join(ProductAnalysisResult, ProductAnalysisResult.id == GeneratedListing.analysis_id)
            .where(GeneratedListing.id == listing_id, Product.user_id == user_id),
        )
        row = result.one_or_none()
        if row is None:
            return None
        return row[0], row[1]

    async def create_listing_version(
        self,
        listing: GeneratedListing,
        content: ListingContent,
        source: str,
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
            source=source,
            is_accepted=False,
            raw_output=content.model_dump(),
        )
        self._database_session.add(version)
        await self._database_session.commit()
        await self._database_session.refresh(version)
        return version
