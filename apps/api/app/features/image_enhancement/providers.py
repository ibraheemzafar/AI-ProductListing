from dataclasses import dataclass
from typing import Protocol

from app.features.image_enhancement.schemas import ImageEnhancementOperation


@dataclass(frozen=True)
class ImageEnhancementInput:
    image_url: str
    image_content: bytes
    image_content_type: str
    image_filename: str
    operation: ImageEnhancementOperation


@dataclass(frozen=True)
class ImageEnhancementOutput:
    content: bytes
    content_type: str
    file_extension: str


class ImageProvider(Protocol):
    provider_name: str

    async def enhance_image(self, image: ImageEnhancementInput) -> ImageEnhancementOutput:
        pass
