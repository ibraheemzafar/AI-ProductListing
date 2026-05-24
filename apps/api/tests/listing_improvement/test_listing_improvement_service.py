from datetime import UTC, datetime

import pytest

from app.core.errors import AppError
from app.features.ai_analysis.models import AiRequestLog
from app.features.ai_analysis.openai_client import TokenUsage
from app.features.listing_generation.models import GeneratedListing
from app.features.listing_generation.schemas import ListingContent
from app.features.listing_improvement.models import ListingVersion
from app.features.listing_improvement.openai_client import ListingImprovementResult
from app.features.listing_improvement.prompts import ListingImprovementPromptBuilder, PromptTemplate
from app.features.listing_improvement.repositories import ListingImprovementRepository
from app.features.listing_improvement.services import ListingImprovementService
from app.features.seo_evaluation.models import SeoAnalysis


class InMemoryListingImprovementRepository(ListingImprovementRepository):
    def __init__(
        self,
        listing: GeneratedListing | None,
        seo_analysis: SeoAnalysis | None,
    ) -> None:
        self.listing = listing
        self.seo_analysis = seo_analysis
        self.versions: list[ListingVersion] = []
        self.logs: list[AiRequestLog] = []

    async def get_listing_with_latest_seo_for_user(
        self,
        listing_id: str,
        user_id: str,
    ) -> tuple[GeneratedListing, SeoAnalysis] | None:
        del user_id
        if self.listing and self.seo_analysis and self.listing.id == listing_id:
            return self.listing, self.seo_analysis
        return None

    async def create_listing_version(
        self,
        listing: GeneratedListing,
        content: ListingContent,
    ) -> ListingVersion:
        version = build_version(
            version_id=f"version-{len(self.versions) + 1}",
            listing=listing,
            content=content,
            version_number=len(self.versions) + 1,
        )
        self.versions.append(version)
        return version

    async def list_versions_for_user(
        self,
        listing_id: str,
        user_id: str,
    ) -> list[ListingVersion] | None:
        del user_id
        if self.listing is None or self.listing.id != listing_id:
            return None
        return self.versions

    async def accept_version_for_user(
        self,
        listing_id: str,
        version_id: str,
        user_id: str,
    ) -> tuple[GeneratedListing, ListingVersion] | None:
        del user_id
        if self.listing is None or self.listing.id != listing_id:
            return None
        version = next((item for item in self.versions if item.id == version_id), None)
        if version is None:
            return None

        self.listing.title = version.title
        self.listing.short_description = version.short_description
        self.listing.long_description = version.long_description
        self.listing.seo_keywords = version.seo_keywords
        self.listing.product_tags = version.product_tags
        for item in self.versions:
            item.is_accepted = False
            item.accepted_at = None
        version.is_accepted = True
        version.accepted_at = datetime.now(UTC)
        return self.listing, version

    async def create_request_log(self, log: AiRequestLog) -> None:
        self.logs.append(log)


class FakeImprovementClient:
    model_name = "fake-text"

    def __init__(self, failures_before_success: int = 0) -> None:
        self.failures_before_success = failures_before_success
        self.calls = 0

    async def improve_listing(self, prompt: str) -> ListingImprovementResult:
        del prompt
        self.calls += 1
        if self.calls <= self.failures_before_success:
            raise RuntimeError("temporary OpenAI failure")
        return ListingImprovementResult(
            listing=build_improved_content(),
            token_usage=TokenUsage(input_tokens=20, output_tokens=30, total_tokens=50),
        )


class FakePromptBuilder(ListingImprovementPromptBuilder):
    def __init__(self) -> None:
        pass

    def build_prompt(self, listing: GeneratedListing, seo_analysis: SeoAnalysis) -> PromptTemplate:
        del listing, seo_analysis
        return PromptTemplate(content="Improve listing.", version="test-improver-v1")


@pytest.mark.asyncio
async def test_listing_improvement_service_creates_version_and_preserves_original() -> None:
    repository = InMemoryListingImprovementRepository(
        listing=build_listing(),
        seo_analysis=build_seo_analysis(),
    )
    service = build_service(repository)

    response = await service.improve_listing(user_id="user-1", listing_id="listing-1")

    assert response.original_listing.title == "Minimal Black Cotton T-Shirt"
    assert response.improved_version.listing.title == "Black Cotton T-Shirt for Everyday Wear"
    assert repository.listing is not None
    assert repository.listing.title == "Minimal Black Cotton T-Shirt"
    assert repository.logs[0].workflow_name == "listing_improvement"
    assert repository.logs[0].total_tokens == 50


@pytest.mark.asyncio
async def test_listing_improvement_service_accepts_version() -> None:
    repository = InMemoryListingImprovementRepository(
        listing=build_listing(),
        seo_analysis=build_seo_analysis(),
    )
    service = build_service(repository)
    improvement = await service.improve_listing(user_id="user-1", listing_id="listing-1")

    response = await service.accept_version(
        user_id="user-1",
        listing_id="listing-1",
        version_id=improvement.improved_version.id,
    )

    assert response.active_listing.title == "Black Cotton T-Shirt for Everyday Wear"
    assert response.accepted_version.is_accepted is True


@pytest.mark.asyncio
async def test_listing_improvement_service_lists_versions() -> None:
    repository = InMemoryListingImprovementRepository(
        listing=build_listing(),
        seo_analysis=build_seo_analysis(),
    )
    service = build_service(repository)
    await service.improve_listing(user_id="user-1", listing_id="listing-1")

    response = await service.list_versions(user_id="user-1", listing_id="listing-1")

    assert len(response.versions) == 1
    assert response.versions[0].version_number == 1


@pytest.mark.asyncio
async def test_listing_improvement_service_requires_listing_and_seo_analysis() -> None:
    service = build_service(
        InMemoryListingImprovementRepository(listing=build_listing(), seo_analysis=None),
    )

    with pytest.raises(AppError, match="Generated listing or SEO analysis was not found"):
        await service.improve_listing(user_id="user-1", listing_id="listing-1")


@pytest.mark.asyncio
async def test_listing_improvement_service_retries_and_logs_ai_failure() -> None:
    repository = InMemoryListingImprovementRepository(
        listing=build_listing(),
        seo_analysis=build_seo_analysis(),
    )
    service = build_service(repository, improvement_client=FakeImprovementClient(3), attempts=2)

    with pytest.raises(AppError, match="Listing improvement failed"):
        await service.improve_listing(user_id="user-1", listing_id="listing-1")

    assert repository.logs[0].success is False
    assert repository.logs[0].error_message == "temporary OpenAI failure"


def build_service(
    repository: InMemoryListingImprovementRepository,
    improvement_client: FakeImprovementClient | None = None,
    attempts: int = 3,
) -> ListingImprovementService:
    return ListingImprovementService(
        repository=repository,
        improvement_client=improvement_client or FakeImprovementClient(),
        prompt_builder=FakePromptBuilder(),
        retry_attempts=attempts,
    )


def build_listing() -> GeneratedListing:
    return GeneratedListing(
        id="listing-1",
        product_id="product-1",
        analysis_id="analysis-1",
        title="Minimal Black Cotton T-Shirt",
        short_description="A soft black cotton T-shirt for everyday wear.",
        long_description=(
            "This minimal black cotton T-shirt is designed for comfortable daily wear."
        ),
        seo_keywords=["black cotton t-shirt", "minimal shirt"],
        product_tags=["t-shirt", "cotton", "black"],
        raw_output={},
        created_at=datetime.now(UTC),
    )


def build_improved_content() -> ListingContent:
    return ListingContent(
        title="Black Cotton T-Shirt for Everyday Wear",
        short_description="A breathable black cotton tee made for daily comfort.",
        long_description="Soft cotton and a minimal look make this black T-shirt easy to wear.",
        seo_keywords=["black cotton t-shirt", "everyday cotton tee"],
        product_tags=["black t-shirt", "cotton tee"],
    )


def build_seo_analysis() -> SeoAnalysis:
    return SeoAnalysis(
        id="seo-analysis-1",
        listing_id="listing-1",
        product_id="product-1",
        seo_score=70,
        readability_score=85,
        keyword_optimization_feedback="Add buyer-intent keywords.",
        title_quality_feedback="Title is clear but generic.",
        description_quality_feedback="Lead with the main benefit.",
        strengths=["Readable"],
        weaknesses=["Generic title"],
        improvement_suggestions=["Add buyer intent"],
        raw_output={},
        created_at=datetime.now(UTC),
    )


def build_version(
    version_id: str,
    listing: GeneratedListing,
    content: ListingContent,
    version_number: int,
) -> ListingVersion:
    return ListingVersion(
        id=version_id,
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
        created_at=datetime.now(UTC),
        accepted_at=None,
    )
