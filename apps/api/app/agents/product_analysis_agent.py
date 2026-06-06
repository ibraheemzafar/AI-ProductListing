from typing import Any

from app.agents.base_agent import BaseAgent
from app.agents.schemas import (
    OpenAIAgentSpec,
    ProductAnalysisAgentInput,
    ProductAnalysisResult,
    WorkflowState,
)
from app.features.ai_analysis.services import AiAnalysisService


class ProductAnalysisAgent(
    BaseAgent[ProductAnalysisAgentInput, ProductAnalysisResult],
):
    def __init__(self, analysis_service: AiAnalysisService) -> None:
        super().__init__(
            "product_analysis",
            OpenAIAgentSpec(
                name="ProductAnalysisAgent",
                instructions=(
                    "Analyze uploaded product images by calling the existing product analysis "
                    "service tool. Extract category, product type, visible attributes, and "
                    "target audience. Do not infer or persist data outside the service."
                ),
            ),
        )
        self._analysis_service = analysis_service

    async def run(
        self,
        agent_input: ProductAnalysisAgentInput,
        state: WorkflowState,
    ) -> ProductAnalysisResult:
        analysis = await self._analysis_service.analyze_uploaded_image(
            user_id=agent_input.user_id,
            image_id=agent_input.image_id,
        )
        state.image_id = analysis.image_id
        state.analysis_id = analysis.id
        result = ProductAnalysisResult(analysis=analysis)
        state.product_analysis = result
        return result

    def _coerce_sdk_output(self, final_output: Any) -> ProductAnalysisResult:
        if isinstance(final_output, ProductAnalysisResult):
            return final_output
        return ProductAnalysisResult.model_validate(final_output)
