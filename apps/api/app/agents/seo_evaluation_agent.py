from typing import Any

from app.agents.base_agent import BaseAgent
from app.agents.schemas import (
    OpenAIAgentSpec,
    SEOEvaluationAgentInput,
    SEOResult,
    WorkflowState,
)
from app.core.errors import AppError
from app.features.seo_evaluation.services import SeoEvaluationService


class SEOEvaluationAgent(BaseAgent[SEOEvaluationAgentInput, SEOResult]):
    def __init__(self, seo_service: SeoEvaluationService) -> None:
        super().__init__(
            "seo_evaluation",
            OpenAIAgentSpec(
                name="SEOEvaluationAgent",
                instructions=(
                    "Score generated listings, identify weaknesses, and produce improvement "
                    "suggestions by calling the existing SEO evaluation service tool."
                ),
            ),
        )
        self._seo_service = seo_service

    async def run(
        self,
        agent_input: SEOEvaluationAgentInput,
        state: WorkflowState,
    ) -> SEOResult:
        listing_id = agent_input.listing_id or state.listing_id
        if listing_id is None:
            raise AppError("Listing id is required before SEO evaluation")

        seo_analysis = await self._seo_service.analyze_listing_seo(
            user_id=agent_input.user_id,
            listing_id=listing_id,
        )
        state.listing_id = seo_analysis.listing_id
        state.seo_analysis_id = seo_analysis.id
        result = SEOResult(seo_analysis=seo_analysis)
        state.seo_evaluation = result
        return result

    def _coerce_sdk_output(self, final_output: Any) -> SEOResult:
        if isinstance(final_output, SEOResult):
            return final_output
        return SEOResult.model_validate(final_output)
