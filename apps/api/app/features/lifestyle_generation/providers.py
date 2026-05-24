from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ImageGenerationInput:
    prompt: str
    source_image: bytes
    source_content_type: str
    source_filename: str


@dataclass(frozen=True)
class ImageGenerationOutput:
    content: bytes
    content_type: str
    file_extension: str


class ImageGenerationProvider(Protocol):
    provider_name: str
    model_name: str

    async def generate_scene(self, image: ImageGenerationInput) -> ImageGenerationOutput:
        pass
