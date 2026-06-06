from typing import Protocol

from app.agents.base_agent import BaseAgent
from app.agents.schemas import (
    MarketingAgentInput,
    MarketingAsset,
    MarketingResult,
    OpenAIAgentSpec,
    WorkflowState,
)
from app.core.errors import AppError


class MarketingContentService(Protocol):
    async def generate_marketing_assets(
        self,
        user_id: str,
        listing_id: str,
        channels: list[str],
    ) -> list[MarketingAsset]:
        raise NotImplementedError


class MarketingAgent(BaseAgent[MarketingAgentInput, MarketingResult]):
    def __init__(self, marketing_service: MarketingContentService | None = None) -> None:
        super().__init__(
            "marketing_generation",
            OpenAIAgentSpec(
                name="MarketingAgent",
                instructions=(
                    "Generate ad copy, social captions, and email content by calling the "
                    "configured marketing service tool."
                ),
            ),
        )
        self._marketing_service = marketing_service

    async def run(
        self,
        agent_input: MarketingAgentInput,
        state: WorkflowState,
    ) -> MarketingResult:
        listing_id = agent_input.listing_id or state.listing_id
        if listing_id is None:
            raise AppError("Listing id is required before marketing generation")
        if self._marketing_service is None:
            raise AppError("Marketing content service is not configured")

        assets = await self._marketing_service.generate_marketing_assets(
            user_id=agent_input.user_id,
            listing_id=listing_id,
            channels=agent_input.channels,
        )
        state.listing_id = listing_id
        result = MarketingResult(assets=assets)
        state.marketing = result
        return result

    def _coerce_sdk_output(self, final_output: object) -> MarketingResult:
        if isinstance(final_output, MarketingResult):
            return final_output
        return MarketingResult.model_validate(final_output)
