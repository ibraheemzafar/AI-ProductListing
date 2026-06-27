from datetime import UTC, datetime

import pytest

from app.core.errors import AppError
from app.features.ai_analysis.models import AiRequestLog, ProductAnalysisResult
from app.features.ai_analysis.openai_client import TokenUsage
from app.features.listing_generation.models import GeneratedListing
from app.features.listing_generation.openai_client import ListingGenerationResult
from app.features.listing_generation.prompts import ListingPromptBuilder, PromptTemplate
from app.features.listing_generation.repositories import ListingGenerationRepository
from app.features.listing_generation.schemas import ListingContent
from app.features.listing_generation.services import ListingGenerationService
from app.features.product_uploads.models import ProductImage


class InMemoryListingGenerationRepository(ListingGenerationRepository):
    def __init__(self, analysis: ProductAnalysisResult | None) -> None:
        self.analysis = analysis
        self.saved_listing: GeneratedListing | None = None
        self.logs: list[AiRequestLog] = []

    async def get_analysis_for_user(
        self,
        analysis_id: str,
        user_id: str,
    ) -> ProductAnalysisResult | None:
        del user_id
        if self.analysis and self.analysis.id == analysis_id:
            return self.analysis
        return None

    async def save_generated_listing(
        self,
        analysis: ProductAnalysisResult,
        listing: ListingContent,
    ) -> GeneratedListing:
        self.saved_listing = GeneratedListing(
            id="listing-1",
            product_id=analysis.product_id,
            analysis_id=analysis.id,
            title=listing.title,
            short_description=listing.short_description,
            long_description=listing.long_description,
            seo_keywords=listing.seo_keywords,
            product_tags=listing.product_tags,
            raw_output=listing.model_dump(),
            created_at=datetime.now(UTC),
        )
        return self.saved_listing

    async def create_request_log(self, log: AiRequestLog) -> None:
        self.logs.append(log)

    async def list_generated_listings_for_user(
        self,
        user_id: str,
        limit: int,
        offset: int,
    ) -> tuple[list[tuple[GeneratedListing, ProductImage]], int]:
        del user_id, limit, offset
        return [(build_listing(), build_image())], 1

    async def get_generated_listing_detail_for_user(
        self,
        listing_id: str,
        user_id: str,
    ) -> tuple[GeneratedListing, ProductAnalysisResult, ProductImage] | None:
        del user_id
        if listing_id != "listing-1" or self.analysis is None:
            return None
        return build_listing(), self.analysis, build_image()


class FakeListingClient:
    model_name = "fake-text"

    def __init__(self, failures_before_success: int = 0) -> None:
        self.failures_before_success = failures_before_success
        self.calls = 0

    async def generate_listing(self, prompt: str) -> ListingGenerationResult:
        del prompt
        self.calls += 1
        if self.calls <= self.failures_before_success:
            raise RuntimeError("temporary OpenAI failure")
        return ListingGenerationResult(
            listing=ListingContent(
                title="Minimal Black Cotton T-Shirt",
                short_description="A soft black cotton T-shirt for everyday wear.",
                long_description=(
                    "This minimal black cotton T-shirt is designed for comfortable daily wear."
                ),
                seo_keywords=["black cotton t-shirt", "minimal shirt"],
                product_tags=["t-shirt", "cotton", "black"],
            ),
            token_usage=TokenUsage(input_tokens=15, output_tokens=40, total_tokens=55),
        )


class FakePromptBuilder(ListingPromptBuilder):
    def __init__(self) -> None:
        pass

    def build_prompt(self, analysis: ProductAnalysisResult) -> PromptTemplate:
        del analysis
        return PromptTemplate(content="Generate a listing.", version="test-listing-v1")


@pytest.mark.asyncio
async def test_listing_generation_service_saves_result_and_logs_success() -> None:
    repository = InMemoryListingGenerationRepository(analysis=build_analysis())
    service = ListingGenerationService(
        repository=repository,
        listing_client=FakeListingClient(),
        prompt_builder=FakePromptBuilder(),
        retry_attempts=3,
    )

    response = await service.generate_listing(user_id="user-1", analysis_id="analysis-1")

    assert response.listing.title == "Minimal Black Cotton T-Shirt"
    assert repository.saved_listing is not None
    assert repository.logs[0].success is True
    assert repository.logs[0].workflow_name == "listing_generation"
    assert repository.logs[0].total_tokens == 55


@pytest.mark.asyncio
async def test_listing_generation_service_retries_openai_failures() -> None:
    listing_client = FakeListingClient(failures_before_success=1)
    service = ListingGenerationService(
        repository=InMemoryListingGenerationRepository(analysis=build_analysis()),
        listing_client=listing_client,
        prompt_builder=FakePromptBuilder(),
        retry_attempts=3,
    )

    response = await service.generate_listing(user_id="user-1", analysis_id="analysis-1")

    assert response.listing.product_tags == ["t-shirt", "cotton", "black"]
    assert listing_client.calls == 2


@pytest.mark.asyncio
async def test_listing_generation_service_handles_missing_analysis() -> None:
    service = ListingGenerationService(
        repository=InMemoryListingGenerationRepository(analysis=None),
        listing_client=FakeListingClient(),
        prompt_builder=FakePromptBuilder(),
        retry_attempts=3,
    )

    with pytest.raises(AppError, match="Product analysis was not found"):
        await service.generate_listing(user_id="user-1", analysis_id="missing-analysis")


@pytest.mark.asyncio
async def test_listing_generation_service_stops_for_invalid_product_analysis() -> None:
    repository = InMemoryListingGenerationRepository(analysis=build_analysis(valid_product=False))
    listing_client = FakeListingClient()
    service = ListingGenerationService(
        repository=repository,
        listing_client=listing_client,
        prompt_builder=FakePromptBuilder(),
        retry_attempts=3,
    )

    with pytest.raises(AppError, match="No clear product was detected"):
        await service.generate_listing(user_id="user-1", analysis_id="analysis-1")

    assert listing_client.calls == 0
    assert repository.saved_listing is None


@pytest.mark.asyncio
async def test_listing_generation_service_stops_for_low_confidence_analysis() -> None:
    repository = InMemoryListingGenerationRepository(analysis=build_analysis(confidence=0.42))
    listing_client = FakeListingClient()
    service = ListingGenerationService(
        repository=repository,
        listing_client=listing_client,
        prompt_builder=FakePromptBuilder(),
        retry_attempts=3,
    )

    with pytest.raises(AppError, match="No clear product was detected"):
        await service.generate_listing(user_id="user-1", analysis_id="analysis-1")

    assert listing_client.calls == 0
    assert repository.saved_listing is None


@pytest.mark.asyncio
async def test_listing_generation_service_logs_openai_failure() -> None:
    repository = InMemoryListingGenerationRepository(analysis=build_analysis())
    service = ListingGenerationService(
        repository=repository,
        listing_client=FakeListingClient(failures_before_success=3),
        prompt_builder=FakePromptBuilder(),
        retry_attempts=2,
    )

    with pytest.raises(AppError, match="Listing generation failed"):
        await service.generate_listing(user_id="user-1", analysis_id="analysis-1")

    assert repository.logs[0].success is False
    assert repository.logs[0].error_message == "temporary OpenAI failure"


@pytest.mark.asyncio
async def test_listing_generation_service_lists_history() -> None:
    service = ListingGenerationService(
        repository=InMemoryListingGenerationRepository(analysis=build_analysis()),
        listing_client=FakeListingClient(),
        prompt_builder=FakePromptBuilder(),
        retry_attempts=3,
    )

    response = await service.list_generated_listings(user_id="user-1", limit=20, offset=0)

    assert response.total == 1
    assert response.listings[0].id == "listing-1"
    assert response.listings[0].image.id == "image-1"


@pytest.mark.asyncio
async def test_listing_generation_service_gets_detail() -> None:
    service = ListingGenerationService(
        repository=InMemoryListingGenerationRepository(analysis=build_analysis()),
        listing_client=FakeListingClient(),
        prompt_builder=FakePromptBuilder(),
        retry_attempts=3,
    )

    response = await service.get_generated_listing_detail(user_id="user-1", listing_id="listing-1")

    assert response.id == "listing-1"
    assert response.analysis.product_type == "T-shirt"


@pytest.mark.asyncio
async def test_listing_generation_service_hides_missing_or_unauthorized_detail() -> None:
    service = ListingGenerationService(
        repository=InMemoryListingGenerationRepository(analysis=build_analysis()),
        listing_client=FakeListingClient(),
        prompt_builder=FakePromptBuilder(),
        retry_attempts=3,
    )

    with pytest.raises(AppError, match="Generated listing was not found"):
        await service.get_generated_listing_detail(user_id="user-1", listing_id="other-listing")


def build_analysis(valid_product: bool = True, confidence: float = 0.92) -> ProductAnalysisResult:
    return ProductAnalysisResult(
        id="analysis-1",
        product_id="product-1",
        image_id="image-1",
        valid_product=valid_product,
        confidence=confidence,
        reason=None if valid_product else "No recognizable product detected.",
        category="Apparel",
        product_type="T-shirt",
        color="Black",
        material="Cotton",
        style="Minimal",
        visible_text_brand="unknown",
        target_audience="Adults",
        raw_attributes={},
        created_at=datetime.now(UTC),
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


def build_image() -> ProductImage:
    return ProductImage(
        id="image-1",
        product_id="product-1",
        original_filename="front.jpg",
        storage_filename="front.jpg",
        image_url="http://testserver/uploads/front.jpg",
        content_type="image/jpeg",
        size_bytes=1024,
        created_at=datetime.now(UTC),
    )
