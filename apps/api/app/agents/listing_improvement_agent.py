from typing import Any

from app.agents.base_agent import BaseAgent
from app.agents.schemas import (
    ListingImprovementAgentInput,
    ListingImprovementResult,
    OpenAIAgentSpec,
    WorkflowState,
)
from app.core.errors import AppError
from app.features.listing_improvement.services import ListingImprovementService


class ListingImprovementAgent(
    BaseAgent[ListingImprovementAgentInput, ListingImprovementResult],
):
    def __init__(self, improvement_service: ListingImprovementService) -> None:
        super().__init__(
            "listing_improvement",
            OpenAIAgentSpec(
                name="ListingImprovementAgent",
                instructions=(
                    "Rewrite generated listings and improve SEO quality by calling the existing "
                    "listing improvement service tool."
                ),
            ),
        )
        self._improvement_service = improvement_service

    async def run(
        self,
        agent_input: ListingImprovementAgentInput,
        state: WorkflowState,
    ) -> ListingImprovementResult:
        listing_id = agent_input.listing_id or state.listing_id
        if listing_id is None:
            raise AppError("Listing id is required before listing improvement")
        if state.seo_analysis_id is None:
            raise AppError("SEO analysis is required before listing improvement")

        improvement = await self._improvement_service.improve_listing(
            user_id=agent_input.user_id,
            listing_id=listing_id,
        )
        version_id = improvement.improved_version.id
        state.listing_version_id = version_id

        accepted_version = None
        if agent_input.accept_improved_version:
            accepted_version = await self._improvement_service.accept_version(
                user_id=agent_input.user_id,
                listing_id=listing_id,
                version_id=version_id,
            )

        state.listing_id = listing_id
        result = ListingImprovementResult(
            improvement=improvement,
            accepted_version=accepted_version,
        )
        state.listing_improvement = result
        return result

    def _coerce_sdk_output(self, final_output: Any) -> ListingImprovementResult:
        if isinstance(final_output, ListingImprovementResult):
            return final_output
        return ListingImprovementResult.model_validate(final_output)
