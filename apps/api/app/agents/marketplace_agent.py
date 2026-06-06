from typing import Any

from app.agents.base_agent import BaseAgent
from app.agents.schemas import (
    MarketplaceAgentInput,
    MarketplaceResult,
    OpenAIAgentSpec,
    WorkflowState,
)
from app.core.errors import AppError
from app.features.marketplace_optimization.services import MarketplaceOptimizationService


class MarketplaceAgent(BaseAgent[MarketplaceAgentInput, MarketplaceResult]):
    def __init__(self, marketplace_service: MarketplaceOptimizationService) -> None:
        super().__init__(
            "marketplace_optimization",
            OpenAIAgentSpec(
                name="MarketplaceAgent",
                instructions=(
                    "Optimize listings for Shopify, Amazon, Etsy, or Daraz by calling the "
                    "existing marketplace optimization service tool."
                ),
            ),
        )
        self._marketplace_service = marketplace_service

    async def run(
        self,
        agent_input: MarketplaceAgentInput,
        state: WorkflowState,
    ) -> MarketplaceResult:
        listing_id = agent_input.listing_id or state.listing_id
        if listing_id is None:
            raise AppError("Listing id is required before marketplace optimization")

        optimization = await self._marketplace_service.optimize_listing(
            user_id=agent_input.user_id,
            listing_id=listing_id,
            marketplace=agent_input.marketplace,
        )
        state.listing_id = optimization.listing_id
        state.marketplace_optimization_id = optimization.id
        result = MarketplaceResult(optimization=optimization)
        state.marketplace_optimization = result
        return result

    def _coerce_sdk_output(self, final_output: Any) -> MarketplaceResult:
        if isinstance(final_output, MarketplaceResult):
            return final_output
        return MarketplaceResult.model_validate(final_output)
