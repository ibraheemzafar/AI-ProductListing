import base64
from typing import Any, cast

import httpx

from app.core.errors import AppError, ConfigurationError
from app.features.lifestyle_generation.providers import (
    ImageGenerationInput,
    ImageGenerationOutput,
    ImageGenerationProvider,
)


class OpenAIImageGenerationProvider(ImageGenerationProvider):
    provider_name = "openai"

    def __init__(self, api_key: str, model_name: str, timeout_seconds: float) -> None:
        self.model_name = model_name
        self._api_key = api_key
        self._timeout_seconds = timeout_seconds

    async def generate_scene(self, image: ImageGenerationInput) -> ImageGenerationOutput:
        if not self._api_key:
            raise ConfigurationError("OPENAI_API_KEY is required for lifestyle scene generation")

        async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
            response = await client.post(
                "https://api.openai.com/v1/images/edits",
                headers={"Authorization": f"Bearer {self._api_key}"},
                data={
                    "model": self.model_name,
                    "prompt": image.prompt,
                    "size": "1024x1024",
                },
                files={
                    "image": (
                        image.source_filename,
                        image.source_image,
                        image.source_content_type,
                    ),
                },
            )
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as error:
                provider_message = self._extract_error_message(response)
                if "safety system" in provider_message.lower():
                    raise AppError(
                        "OpenAI rejected this scene request for safety reasons. Try a different "
                        "product-only image, crop out people, faces, body parts, sensitive text, "
                        "or symbols, and use a simple ecommerce scene prompt.",
                    ) from error
                raise AppError(
                    f"OpenAI image generation failed: {provider_message}",
                ) from error
            payload = cast(dict[str, Any], response.json())
            encoded_image = payload.get("data", [{}])[0].get("b64_json")
            if not isinstance(encoded_image, str):
                raise ValueError("OpenAI image response did not include image data")
            return ImageGenerationOutput(
                content=base64.b64decode(encoded_image),
                content_type="image/png",
                file_extension=".png",
            )

    def _extract_error_message(self, response: httpx.Response) -> str:
        try:
            payload = response.json()
        except ValueError:
            return response.text[:300] or "provider returned an error"

        if isinstance(payload, dict):
            error = payload.get("error")
            if isinstance(error, dict) and isinstance(error.get("message"), str):
                return cast(str, error["message"])[:300]
            if isinstance(payload.get("message"), str):
                return cast(str, payload["message"])[:300]
        return "provider returned an error"
