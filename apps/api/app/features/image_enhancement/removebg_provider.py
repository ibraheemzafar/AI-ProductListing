from typing import Any

import httpx

from app.core.errors import AppError, ConfigurationError
from app.features.image_enhancement.providers import (
    ImageEnhancementInput,
    ImageEnhancementOutput,
    ImageProvider,
)


class RemoveBgImageProvider(ImageProvider):
    provider_name = "remove.bg"

    def __init__(self, api_key: str, timeout_seconds: float) -> None:
        self._api_key = api_key
        self._timeout_seconds = timeout_seconds

    async def enhance_image(self, image: ImageEnhancementInput) -> ImageEnhancementOutput:
        if image.operation != "background_removal":
            raise AppError("Configured image provider only supports background removal")
        if not self._api_key:
            raise ConfigurationError("REMOVE_BG_API_KEY is required for image enhancement")

        async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
            response = await client.post(
                "https://api.remove.bg/v1.0/removebg",
                headers={"X-Api-Key": self._api_key},
                data={
                    "image_url": image.image_url,
                    "size": "auto",
                    "type": "product",
                    "format": "png",
                },
            )
            response.raise_for_status()
            content_type = response.headers.get("content-type", "image/png").split(";")[0]
            return ImageEnhancementOutput(
                content=response.content,
                content_type=self._normalize_content_type(content_type),
                file_extension=".png",
            )

    def _normalize_content_type(self, content_type: str) -> str:
        supported: dict[str, Any] = {"image/png": None}
        if content_type in supported:
            return content_type
        return "image/png"
