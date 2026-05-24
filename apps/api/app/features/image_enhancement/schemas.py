from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from app.features.image_enhancement.models import EnhancedImage

ImageEnhancementOperation = Literal["background_removal", "image_cleanup", "image_optimization"]


class ImageEnhancementRequest(BaseModel):
    operation: ImageEnhancementOperation = "background_removal"


class EnhancedImageResponse(BaseModel):
    id: str
    product_id: str
    original_image_id: str
    operation: ImageEnhancementOperation
    provider_name: str
    enhanced_image_url: str
    content_type: str
    size_bytes: int
    created_at: datetime

    @classmethod
    def from_model(cls, image: EnhancedImage) -> "EnhancedImageResponse":
        return cls(
            id=image.id,
            product_id=image.product_id,
            original_image_id=image.original_image_id,
            operation=image.operation,  # type: ignore[arg-type]
            provider_name=image.provider_name,
            enhanced_image_url=image.enhanced_image_url,
            content_type=image.content_type,
            size_bytes=image.size_bytes,
            created_at=image.created_at,
        )
