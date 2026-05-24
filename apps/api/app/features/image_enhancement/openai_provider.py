import base64
from typing import Any, cast

import httpx

from app.core.errors import AppError, ConfigurationError
from app.features.image_enhancement.providers import (
    ImageEnhancementInput,
    ImageEnhancementOutput,
    ImageProvider,
)


class OpenAIImageEnhancementProvider(ImageProvider):
    provider_name = "openai"

    def __init__(self, api_key: str, model_name: str, timeout_seconds: float) -> None:
        self._api_key = api_key
        self._model_name = model_name
        self._timeout_seconds = timeout_seconds

    async def enhance_image(self, image: ImageEnhancementInput) -> ImageEnhancementOutput:
        if not self._api_key:
            raise ConfigurationError("OPENAI_API_KEY is required for image enhancement")

        async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
            response = await client.post(
                "https://api.openai.com/v1/images/edits",
                headers={"Authorization": f"Bearer {self._api_key}"},
                data=self._build_request_data(image),
                files={
                    "image": (
                        image.image_filename,
                        image.image_content,
                        image.image_content_type,
                    ),
                },
            )
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as error:
                provider_message = self._extract_error_message(response)
                if "safety system" in provider_message.lower():
                    raise AppError(
                        "OpenAI rejected this image for safety reasons. Try a different product "
                        "image or crop out people, faces, body parts, sensitive text, or symbols.",
                    ) from error
                raise AppError(
                    f"OpenAI image enhancement failed: {provider_message}",
                ) from error

            payload = cast(dict[str, Any], response.json())
            encoded_image = payload.get("data", [{}])[0].get("b64_json")
            if not isinstance(encoded_image, str):
                raise ValueError("OpenAI image response did not include image data")
            return ImageEnhancementOutput(
                content=base64.b64decode(encoded_image),
                content_type="image/png",
                file_extension=".png",
            )

    def _build_request_data(self, image: ImageEnhancementInput) -> dict[str, str]:
        data = {
            "model": self._model_name,
            "prompt": self._prompt_for_operation(image.operation),
            "size": "1024x1024",
        }
        if image.operation == "background_removal":
            data["background"] = "transparent"
            data["output_format"] = "png"
        return data

    def _prompt_for_operation(self, operation: str) -> str:
        prompts = {
            "background_removal": (
                "Remove the background from this product image. Keep the product unchanged, "
                "centered, sharp, and fully visible. Return a transparent PNG."
            ),
            "image_cleanup": (
                "Clean up this product photo by improving clarity, lighting, and small visual "
                "imperfections. Do not change the product design, color, branding, or shape."
            ),
            "image_optimization": (
                "Optimize this product photo for ecommerce. Improve lighting, framing, and "
                "sharpness while preserving the product exactly."
            ),
        }
        return prompts.get(operation, prompts["image_optimization"])

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
