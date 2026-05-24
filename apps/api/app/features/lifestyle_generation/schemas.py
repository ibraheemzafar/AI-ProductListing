from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.features.lifestyle_generation.models import GeneratedImage

ImageGenerationCategory = Literal[
    "studio_white_background",
    "luxury_product_shot",
    "wooden_table_setup",
    "minimal_ecommerce_background",
    "lifestyle_home_setup",
    "social_media_banner",
    "marketplace_hero_image",
    "custom_prompt",
]
ScenePreset = ImageGenerationCategory


class LifestyleGenerationRequest(BaseModel):
    category: ImageGenerationCategory = "marketplace_hero_image"
    custom_prompt: str | None = Field(default=None, max_length=800)


class GeneratedImageResponse(BaseModel):
    id: str
    user_id: str
    product_id: str
    listing_id: str
    source_product_image_id: str
    source_enhanced_image_id: str | None
    category: ImageGenerationCategory
    custom_prompt: str | None
    prompt: str
    provider: str
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
            user_id=image.user_id,
            product_id=image.product_id,
            listing_id=image.listing_id,
            source_product_image_id=image.source_product_image_id,
            source_enhanced_image_id=image.source_enhanced_image_id,
            category=image.category,  # type: ignore[arg-type]
            custom_prompt=image.custom_prompt,
            prompt=image.prompt,
            provider=image.provider,
            generated_image_url=image.generated_image_url,
            content_type=image.content_type,
            size_bytes=image.size_bytes,
            generation_time_ms=image.generation_time_ms,
            status=image.status,
            created_at=image.created_at,
        )


class GeneratedImageGalleryResponse(BaseModel):
    images: list[GeneratedImageResponse]
