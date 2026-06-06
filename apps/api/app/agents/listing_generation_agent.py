from typing import Any

from app.agents.base_agent import BaseAgent
from app.agents.schemas import (
    ListingGenerationAgentInput,
    ListingResult,
    OpenAIAgentSpec,
    WorkflowState,
)
from app.core.errors import AppError
from app.features.listing_generation.services import ListingGenerationService


class ListingGenerationAgent(
    BaseAgent[ListingGenerationAgentInput, ListingResult],
):
    def __init__(self, listing_service: ListingGenerationService) -> None:
        super().__init__(
            "listing_generation",
            OpenAIAgentSpec(
                name="ListingGenerationAgent",
                instructions=(
                    "Generate product title, descriptions, product tags, and SEO keywords by "
                    "calling the existing listing generation service tool."
                ),
            ),
        )
        self._listing_service = listing_service

    async def run(
        self,
        agent_input: ListingGenerationAgentInput,
        state: WorkflowState,
    ) -> ListingResult:
        analysis_id = agent_input.analysis_id or state.analysis_id
        if analysis_id is None:
            raise AppError("Analysis id is required before listing generation")

        listing = await self._listing_service.generate_listing(
            user_id=agent_input.user_id,
            analysis_id=analysis_id,
        )
        state.analysis_id = listing.analysis_id
        state.listing_id = listing.id
        result = ListingResult(listing=listing)
        state.listing_generation = result
        return result

    def _coerce_sdk_output(self, final_output: Any) -> ListingResult:
        if isinstance(final_output, ListingResult):
            return final_output
        return ListingResult.model_validate(final_output)
