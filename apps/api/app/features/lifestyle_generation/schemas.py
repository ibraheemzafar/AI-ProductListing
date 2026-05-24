from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.features.lifestyle_generation.models import GeneratedImage

ScenePreset = Literal[
    "luxury_setup",
    "wooden_table_setup",
    "studio_white_background",
    "cozy_home_environment",
    "modern_ecommerce_hero_shot",
]


class LifestyleGenerationRequest(BaseModel):
    scene_preset: ScenePreset = "modern_ecommerce_hero_shot"
    custom_prompt: str | None = Field(default=None, max_length=800)


class GeneratedImageResponse(BaseModel):
    id: str
    product_id: str
    listing_id: str
    source_image_id: str
    source_enhanced_image_id: str | None
    scene_preset: ScenePreset
    custom_prompt: str | None
    prompt: str
    provider_name: str
    generated_image_url: str
    content_type: str
    size_bytes: int
    generation_time_ms: int
    status: str
    created_at: datetime

    @classmethod
    def from_model(cls, image: GeneratedImage) -> "GeneratedImageResponse":
        return cls(
            id=image.id,
            product_id=image.product_id,
            listing_id=image.listing_id,
            source_image_id=image.source_image_id,
            source_enhanced_image_id=image.source_enhanced_image_id,
            scene_preset=image.scene_preset,  # type: ignore[arg-type]
            custom_prompt=image.custom_prompt,
            prompt=image.prompt,
            provider_name=image.provider_name,
            generated_image_url=image.generated_image_url,
            content_type=image.content_type,
            size_bytes=image.size_bytes,
            generation_time_ms=image.generation_time_ms,
            status=image.status,
            created_at=image.created_at,
        )


class GeneratedImageGalleryResponse(BaseModel):
    images: list[GeneratedImageResponse]
