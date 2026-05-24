from datetime import UTC, datetime

import pytest

from app.core.errors import AppError
from app.features.ai_analysis.models import AiRequestLog
from app.features.ai_analysis.openai_client import TokenUsage
from app.features.listing_generation.models import GeneratedListing
from app.features.marketplace_optimization.models import MarketplaceOptimization
from app.features.marketplace_optimization.openai_client import MarketplaceOptimizationResult
from app.features.marketplace_optimization.prompts import (
    MarketplaceOptimizationPromptBuilder,
    PromptTemplate,
)
from app.features.marketplace_optimization.repositories import MarketplaceOptimizationRepository
from app.features.marketplace_optimization.schemas import (
    Marketplace,
    MarketplaceOptimizationContent,
)
from app.features.marketplace_optimization.services import MarketplaceOptimizationService


class InMemoryMarketplaceOptimizationRepository(MarketplaceOptimizationRepository):
    def __init__(self, listing: GeneratedListing | None) -> None:
        self.listing = listing
        self.optimizations: list[MarketplaceOptimization] = []
        self.logs: list[AiRequestLog] = []

    async def get_listing_for_user(
        self,
        listing_id: str,
        user_id: str,
    ) -> GeneratedListing | None:
        del user_id
        if self.listing and self.listing.id == listing_id:
            return self.listing
        return None

    async def save_optimization(
        self,
        listing: GeneratedListing,
        marketplace: Marketplace,
        content: MarketplaceOptimizationContent,
    ) -> MarketplaceOptimization:
        optimization = MarketplaceOptimization(
            id=f"marketplace-{len(self.optimizations) + 1}",
            listing_id=listing.id,
            product_id=listing.product_id,
            marketplace=marketplace,
            optimized_title=content.optimized_title,
            optimized_description=content.optimized_description,
            bullet_points=content.bullet_points,
            keywords_tags=content.keywords_tags,
            platform_notes=content.platform_notes,
            raw_output=content.model_dump(),
            created_at=datetime.now(UTC),
        )
        self.optimizations.append(optimization)
        return optimization

    async def create_request_log(self, log: AiRequestLog) -> None:
        self.logs.append(log)


class FakeMarketplaceOptimizationClient:
    model_name = "fake-text"

    def __init__(self, failures_before_success: int = 0) -> None:
        self.failures_before_success = failures_before_success
        self.calls = 0

    async def optimize_listing(self, prompt: str) -> MarketplaceOptimizationResult:
        del prompt
        self.calls += 1
        if self.calls <= self.failures_before_success:
            raise RuntimeError("temporary OpenAI failure")
        return MarketplaceOptimizationResult(
            optimization=build_optimization_content(),
            token_usage=TokenUsage(input_tokens=25, output_tokens=35, total_tokens=60),
        )


class FakePromptBuilder(MarketplaceOptimizationPromptBuilder):
    def __init__(self) -> None:
        pass

    def build_prompt(
        self,
        listing: GeneratedListing,
        marketplace: Marketplace,
    ) -> PromptTemplate:
        del listing
        return PromptTemplate(
            content=f"Optimize for {marketplace}.",
            version="test-marketplace-v1",
        )


@pytest.mark.asyncio
@pytest.mark.parametrize("marketplace", ["shopify", "amazon", "etsy", "daraz"])
async def test_marketplace_optimization_service_saves_each_marketplace(
    marketplace: Marketplace,
) -> None:
    repository = InMemoryMarketplaceOptimizationRepository(listing=build_listing())
    service = build_service(repository)

    response = await service.optimize_listing(
        user_id="user-1",
        listing_id="listing-1",
        marketplace=marketplace,
    )

    assert response.marketplace == marketplace
    assert response.optimization.optimized_title == "Optimized Cotton T-Shirt"
    assert repository.optimizations[0].marketplace == marketplace
    assert repository.logs[0].workflow_name == "marketplace_optimization"
    assert repository.logs[0].total_tokens == 60


@pytest.mark.asyncio
async def test_marketplace_optimization_service_requires_owned_listing() -> None:
    service = build_service(InMemoryMarketplaceOptimizationRepository(listing=None))

    with pytest.raises(AppError, match="Generated listing was not found"):
        await service.optimize_listing(
            user_id="user-1",
            listing_id="listing-1",
            marketplace="shopify",
        )


@pytest.mark.asyncio
async def test_marketplace_optimization_service_retries_and_logs_ai_failure() -> None:
    repository = InMemoryMarketplaceOptimizationRepository(listing=build_listing())
    service = build_service(
        repository,
        optimization_client=FakeMarketplaceOptimizationClient(3),
        attempts=2,
    )

    with pytest.raises(AppError, match="Marketplace optimization failed"):
        await service.optimize_listing(
            user_id="user-1",
            listing_id="listing-1",
            marketplace="amazon",
        )

    assert repository.logs[0].success is False
    assert repository.logs[0].error_message == "temporary OpenAI failure"


def build_service(
    repository: InMemoryMarketplaceOptimizationRepository,
    optimization_client: FakeMarketplaceOptimizationClient | None = None,
    attempts: int = 3,
) -> MarketplaceOptimizationService:
    return MarketplaceOptimizationService(
        repository=repository,
        optimization_client=optimization_client or FakeMarketplaceOptimizationClient(),
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
        long_description="This minimal black cotton T-shirt is comfortable for daily wear.",
        seo_keywords=["black cotton t-shirt", "minimal shirt"],
        product_tags=["t-shirt", "cotton", "black"],
        raw_output={},
        created_at=datetime.now(UTC),
    )


def build_optimization_content() -> MarketplaceOptimizationContent:
    return MarketplaceOptimizationContent(
        optimized_title="Optimized Cotton T-Shirt",
        optimized_description="A platform-ready cotton T-shirt description.",
        bullet_points=["Soft cotton feel", "Minimal everyday style"],
        keywords_tags=["cotton t-shirt", "black tee"],
        platform_notes="Use concise search terms for this marketplace.",
    )
