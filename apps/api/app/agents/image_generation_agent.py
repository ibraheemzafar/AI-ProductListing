from typing import Any

from app.agents.base_agent import BaseAgent
from app.agents.schemas import (
    ImageGenerationAgentInput,
    ImageResult,
    OpenAIAgentSpec,
    WorkflowState,
)
from app.core.errors import AppError
from app.features.image_enhancement.services import ImageEnhancementService
from app.features.lifestyle_generation.services import LifestyleGenerationService


class ImageGenerationAgent(BaseAgent[ImageGenerationAgentInput, ImageResult]):
    def __init__(
        self,
        enhancement_service: ImageEnhancementService | None = None,
        lifestyle_service: LifestyleGenerationService | None = None,
    ) -> None:
        super().__init__(
            "image_generation",
            OpenAIAgentSpec(
                name="ImageGenerationAgent",
                instructions=(
                    "Generate lifestyle images and ecommerce hero images by calling existing "
                    "image enhancement and lifestyle generation service tools."
                ),
            ),
        )
        self._enhancement_service = enhancement_service
        self._lifestyle_service = lifestyle_service

    async def run(
        self,
        agent_input: ImageGenerationAgentInput,
        state: WorkflowState,
    ) -> ImageResult:
        listing_id = agent_input.listing_id or state.listing_id
        if listing_id is None:
            raise AppError("Listing id is required before image workflows")

        enhanced_image = None
        if agent_input.enhancement_operation is not None:
            if self._enhancement_service is None:
                raise AppError("Image enhancement service is not configured")
            enhanced_image = await self._enhancement_service.enhance_listing_image(
                user_id=agent_input.user_id,
                listing_id=listing_id,
                operation=agent_input.enhancement_operation,
            )
            state.enhanced_image_id = enhanced_image.id

        generated_image = None
        if agent_input.generation_category is not None:
            if self._lifestyle_service is None:
                raise AppError("Lifestyle generation service is not configured")
            generated_image = await self._lifestyle_service.generate_lifestyle_scene(
                user_id=agent_input.user_id,
                listing_id=listing_id,
                category=agent_input.generation_category,
                custom_prompt=agent_input.custom_prompt,
            )
            state.generated_image_id = generated_image.id

        if enhanced_image is None and generated_image is None:
            raise AppError("At least one image workflow operation is required")

        state.listing_id = listing_id
        result = ImageResult(
            enhanced_image=enhanced_image,
            generated_image=generated_image,
        )
        state.image_generation = result
        return result

    def _coerce_sdk_output(self, final_output: Any) -> ImageResult:
        if isinstance(final_output, ImageResult):
            return final_output
        return ImageResult.model_validate(final_output)
