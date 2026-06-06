from typing import Any

from app.agents.base_agent import BaseAgent
from app.agents.listing_generation_agent import (
    ListingGenerationAgent,
)
from app.agents.listing_improvement_agent import (
    ListingImprovementAgent,
)
from app.agents.marketplace_agent import MarketplaceAgent
from app.agents.product_analysis_agent import ProductAnalysisAgent
from app.agents.schemas import (
    FullListingWorkflowInput,
    FullListingWorkflowOutput,
    ListingGenerationAgentInput,
    ListingImprovementAgentInput,
    MarketplaceAgentInput,
    OpenAIAgentSpec,
    ProductAnalysisAgentInput,
    SEOEvaluationAgentInput,
    WorkflowState,
)
from app.agents.seo_evaluation_agent import SEOEvaluationAgent


class WorkflowOrchestratorAgent(
    BaseAgent[FullListingWorkflowInput, FullListingWorkflowOutput],
):
    def __init__(
        self,
        product_analysis_agent: ProductAnalysisAgent,
        listing_generation_agent: ListingGenerationAgent,
        seo_evaluation_agent: SEOEvaluationAgent,
        listing_improvement_agent: ListingImprovementAgent,
        marketplace_agent: MarketplaceAgent,
    ) -> None:
        super().__init__(
            "workflow_orchestrator",
            OpenAIAgentSpec(
                name="WorkflowOrchestratorAgent",
                instructions=(
                    "Coordinate the full product listing workflow. Manage state, call each "
                    "service-backed agent in order, stop on failures, and preserve execution "
                    "records for observability."
                ),
            ),
        )
        self._product_analysis_agent = product_analysis_agent
        self._listing_generation_agent = listing_generation_agent
        self._seo_evaluation_agent = seo_evaluation_agent
        self._listing_improvement_agent = listing_improvement_agent
        self._marketplace_agent = marketplace_agent

    async def run(
        self,
        agent_input: FullListingWorkflowInput,
        state: WorkflowState,
    ) -> FullListingWorkflowOutput:
        state.user_id = agent_input.user_id
        state.image_id = agent_input.image_id

        product_analysis = await self._product_analysis_agent.execute(
            ProductAnalysisAgentInput(
                user_id=agent_input.user_id,
                image_id=agent_input.image_id,
            ),
            state,
        )
        listing_generation = await self._listing_generation_agent.execute(
            ListingGenerationAgentInput(
                user_id=agent_input.user_id,
                analysis_id=product_analysis.analysis.id,
            ),
            state,
        )
        seo_evaluation = await self._seo_agent.execute(
            SEOEvaluationAgentInput(
                user_id=agent_input.user_id,
                listing_id=listing_generation.listing.id,
            ),
            state,
        )
        listing_improvement = await self._listing_improvement_agent.execute(
            ListingImprovementAgentInput(
                user_id=agent_input.user_id,
                listing_id=listing_generation.listing.id,
                accept_improved_version=agent_input.accept_improved_version,
            ),
            state,
        )
        marketplace_optimization = await self._marketplace_agent.execute(
            MarketplaceAgentInput(
                user_id=agent_input.user_id,
                listing_id=listing_generation.listing.id,
                marketplace=agent_input.marketplace,
            ),
            state,
        )

        return FullListingWorkflowOutput(
            state=state,
            product_analysis=product_analysis,
            listing_generation=listing_generation,
            seo_evaluation=seo_evaluation,
            listing_improvement=listing_improvement,
            marketplace_optimization=marketplace_optimization,
        )

    async def run_full_workflow(
        self,
        agent_input: FullListingWorkflowInput,
    ) -> FullListingWorkflowOutput:
        state = WorkflowState(user_id=agent_input.user_id, image_id=agent_input.image_id)
        return await self.execute(agent_input, state)

    @property
    def _seo_agent(self) -> SEOEvaluationAgent:
        return self._seo_evaluation_agent

    def _coerce_sdk_output(self, final_output: Any) -> FullListingWorkflowOutput:
        if isinstance(final_output, FullListingWorkflowOutput):
            return final_output
        return FullListingWorkflowOutput.model_validate(final_output)


OrchestratorAgent = WorkflowOrchestratorAgent
