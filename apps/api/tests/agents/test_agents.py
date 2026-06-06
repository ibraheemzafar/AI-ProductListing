from datetime import UTC, datetime

import pytest

from app.agents.listing_generation_agent import ListingGenerationAgent
from app.agents.listing_improvement_agent import ListingImprovementAgent
from app.agents.marketplace_agent import MarketplaceAgent
from app.agents.orchestrator_agent import WorkflowOrchestratorAgent
from app.agents.product_analysis_agent import ProductAnalysisAgent
from app.agents.schemas import (
    FullListingWorkflowInput,
    ListingGenerationAgentInput,
    MarketplaceAgentInput,
    ProductAnalysisAgentInput,
    WorkflowState,
)
from app.agents.seo_evaluation_agent import SEOEvaluationAgent
from app.features.ai_analysis.schemas import ProductAnalysisResponse, ProductAttributes
from app.features.listing_generation.schemas import GeneratedListingResponse, ListingContent
from app.features.listing_improvement.schemas import (
    AcceptListingVersionResponse,
    ListingImprovementResponse,
    ListingVersionResponse,
)
from app.features.marketplace_optimization.schemas import (
    MarketplaceOptimizationContent,
    MarketplaceOptimizationResponse,
)
from app.features.seo_evaluation.schemas import SeoAnalysisResponse, SeoEvaluationContent

NOW = datetime.now(UTC)


def _analysis_response() -> ProductAnalysisResponse:
    return ProductAnalysisResponse(
        id="analysis-1",
        product_id="product-1",
        image_id="image-1",
        attributes=ProductAttributes(
            category="home decor",
            product_type="desk lamp",
            color="white",
            material="ceramic",
            style="minimal",
            visible_text_brand="none",
            target_audience="home office shoppers",
        ),
        created_at=NOW,
    )


def _listing_content(title: str = "Minimal Ceramic Desk Lamp") -> ListingContent:
    return ListingContent(
        title=title,
        short_description="A warm ceramic desk lamp.",
        long_description="A warm ceramic desk lamp for modern workspaces.",
        seo_keywords=["ceramic lamp", "desk lamp"],
        product_tags=["lamp", "home decor"],
    )


def _listing_response() -> GeneratedListingResponse:
    return GeneratedListingResponse(
        id="listing-1",
        product_id="product-1",
        analysis_id="analysis-1",
        listing=_listing_content(),
        created_at=NOW,
    )


def _seo_response() -> SeoAnalysisResponse:
    return SeoAnalysisResponse(
        id="seo-1",
        listing_id="listing-1",
        product_id="product-1",
        analysis=SeoEvaluationContent(
            seo_score=82,
            readability_score=90,
            keyword_optimization_feedback="Add more long-tail keywords.",
            title_quality_feedback="Strong title.",
            description_quality_feedback="Good description.",
            strengths=["Clear category"],
            weaknesses=["Could add material keyword"],
            improvement_suggestions=["Add ceramic desk lamp keyword"],
        ),
        created_at=NOW,
    )


def _improvement_response() -> ListingImprovementResponse:
    version = ListingVersionResponse(
        id="version-1",
        listing_id="listing-1",
        product_id="product-1",
        version_number=2,
        listing=_listing_content("SEO Ceramic Desk Lamp for Modern Offices"),
        source="ai_improvement",
        is_accepted=False,
        created_at=NOW,
        accepted_at=None,
    )
    return ListingImprovementResponse(
        original_listing=_listing_content(),
        improved_version=version,
    )


def _accepted_response() -> AcceptListingVersionResponse:
    version = ListingVersionResponse(
        id="version-1",
        listing_id="listing-1",
        product_id="product-1",
        version_number=2,
        listing=_listing_content("SEO Ceramic Desk Lamp for Modern Offices"),
        source="ai_improvement",
        is_accepted=True,
        created_at=NOW,
        accepted_at=NOW,
    )
    return AcceptListingVersionResponse(
        listing_id="listing-1",
        accepted_version=version,
        active_listing=version.listing,
    )


def _marketplace_response() -> MarketplaceOptimizationResponse:
    return MarketplaceOptimizationResponse(
        id="marketplace-1",
        listing_id="listing-1",
        product_id="product-1",
        marketplace="shopify",
        optimization=MarketplaceOptimizationContent(
            optimized_title="Shopify Ceramic Desk Lamp",
            optimized_description="A polished Shopify listing description.",
            bullet_points=["Warm light", "Ceramic body"],
            keywords_tags=["shopify lamp", "desk lamp"],
            platform_notes="Ready for Shopify import.",
        ),
        created_at=NOW,
    )


class FakeAnalysisService:
    async def analyze_uploaded_image(
        self,
        user_id: str,
        image_id: str,
    ) -> ProductAnalysisResponse:
        assert user_id == "user-1"
        assert image_id == "image-1"
        return _analysis_response()


class FakeListingService:
    async def generate_listing(
        self,
        user_id: str,
        analysis_id: str,
    ) -> GeneratedListingResponse:
        assert user_id == "user-1"
        assert analysis_id == "analysis-1"
        return _listing_response()


class FakeSeoService:
    async def analyze_listing_seo(
        self,
        user_id: str,
        listing_id: str,
    ) -> SeoAnalysisResponse:
        assert user_id == "user-1"
        assert listing_id == "listing-1"
        return _seo_response()


class FakeImprovementService:
    async def improve_listing(
        self,
        user_id: str,
        listing_id: str,
    ) -> ListingImprovementResponse:
        assert user_id == "user-1"
        assert listing_id == "listing-1"
        return _improvement_response()

    async def accept_version(
        self,
        user_id: str,
        listing_id: str,
        version_id: str,
    ) -> AcceptListingVersionResponse:
        assert user_id == "user-1"
        assert listing_id == "listing-1"
        assert version_id == "version-1"
        return _accepted_response()


class FakeMarketplaceService:
    async def optimize_listing(
        self,
        user_id: str,
        listing_id: str,
        marketplace: str,
    ) -> MarketplaceOptimizationResponse:
        assert user_id == "user-1"
        assert listing_id == "listing-1"
        assert marketplace == "shopify"
        return _marketplace_response()


@pytest.mark.asyncio
async def test_product_analysis_agent_updates_workflow_state() -> None:
    state = WorkflowState(user_id="user-1", image_id="image-1")
    agent = ProductAnalysisAgent(FakeAnalysisService())  # type: ignore[arg-type]

    result = await agent.execute(
        ProductAnalysisAgentInput(user_id="user-1", image_id="image-1"),
        state,
    )

    assert result.analysis.id == "analysis-1"
    assert state.analysis_id == "analysis-1"
    assert state.product_analysis == result
    assert state.execution_log[0].agent_name == "product_analysis"
    assert state.execution_log[0].success is True


@pytest.mark.asyncio
async def test_listing_generation_agent_uses_analysis_from_state() -> None:
    state = WorkflowState(user_id="user-1", image_id="image-1", analysis_id="analysis-1")
    agent = ListingGenerationAgent(FakeListingService())  # type: ignore[arg-type]

    result = await agent.execute(ListingGenerationAgentInput(user_id="user-1"), state)

    assert result.listing.id == "listing-1"
    assert state.listing_id == "listing-1"
    assert "listing_generation" in state.completed_steps


@pytest.mark.asyncio
async def test_marketplace_agent_uses_listing_from_state() -> None:
    state = WorkflowState(user_id="user-1", image_id="image-1", listing_id="listing-1")
    agent = MarketplaceAgent(FakeMarketplaceService())  # type: ignore[arg-type]

    result = await agent.execute(MarketplaceAgentInput(user_id="user-1"), state)

    assert result.optimization.id == "marketplace-1"
    assert state.marketplace_optimization_id == "marketplace-1"


@pytest.mark.asyncio
async def test_workflow_orchestrator_runs_full_listing_workflow() -> None:
    orchestrator = WorkflowOrchestratorAgent(
        product_analysis_agent=ProductAnalysisAgent(FakeAnalysisService()),  # type: ignore[arg-type]
        listing_generation_agent=ListingGenerationAgent(FakeListingService()),  # type: ignore[arg-type]
        seo_evaluation_agent=SEOEvaluationAgent(FakeSeoService()),  # type: ignore[arg-type]
        listing_improvement_agent=ListingImprovementAgent(FakeImprovementService()),  # type: ignore[arg-type]
        marketplace_agent=MarketplaceAgent(FakeMarketplaceService()),  # type: ignore[arg-type]
    )

    result = await orchestrator.run_full_workflow(
        FullListingWorkflowInput(user_id="user-1", image_id="image-1"),
    )

    assert result.product_analysis.analysis.id == "analysis-1"
    assert result.listing_generation.listing.id == "listing-1"
    assert result.seo_evaluation.seo_analysis.id == "seo-1"
    assert result.listing_improvement.improvement.improved_version.id == "version-1"
    assert result.marketplace_optimization.optimization.id == "marketplace-1"
    assert result.state.workflow_id
    assert result.state.completed_steps == [
        "product_analysis",
        "listing_generation",
        "seo_evaluation",
        "listing_improvement",
        "marketplace_optimization",
        "workflow_orchestrator",
    ]
    assert len(result.state.execution_log) == 6
    assert all(record.success for record in result.state.execution_log)
