import base64
import json
from dataclasses import dataclass
from typing import Any, Protocol, cast

import httpx

from app.core.errors import ConfigurationError
from app.features.ai_analysis.schemas import ProductAttributes


@dataclass(frozen=True)
class TokenUsage:
    input_tokens: int | None
    output_tokens: int | None
    total_tokens: int | None


@dataclass(frozen=True)
class VisionAnalysisResult:
    attributes: ProductAttributes
    token_usage: TokenUsage


class VisionAnalysisClient(Protocol):
    model_name: str

    async def analyze_product_image(
        self,
        image_content: bytes,
        content_type: str,
        prompt: str,
    ) -> VisionAnalysisResult:
        pass


class OpenAIVisionAnalysisClient:
    def __init__(self, api_key: str, model_name: str, timeout_seconds: float) -> None:
        self.model_name = model_name
        self._api_key = api_key
        self._timeout_seconds = timeout_seconds

    async def analyze_product_image(
        self,
        image_content: bytes,
        content_type: str,
        prompt: str,
    ) -> VisionAnalysisResult:
        if not self._api_key:
            raise ConfigurationError("OPENAI_API_KEY is required for product analysis")

        response_payload = await self._create_response(
            image_content=image_content,
            content_type=content_type,
            prompt=prompt,
        )
        attributes = ProductAttributes.model_validate_json(
            self._extract_output_text(response_payload),
        )
        usage = response_payload.get("usage") or {}
        return VisionAnalysisResult(
            attributes=attributes,
            token_usage=TokenUsage(
                input_tokens=usage.get("input_tokens"),
                output_tokens=usage.get("output_tokens"),
                total_tokens=usage.get("total_tokens"),
            ),
        )

    async def _create_response(
        self,
        image_content: bytes,
        content_type: str,
        prompt: str,
    ) -> dict[str, Any]:
        data_url = self._build_data_url(image_content=image_content, content_type=content_type)
        async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
            response = await client.post(
                "https://api.openai.com/v1/responses",
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model_name,
                    "input": [
                        {
                            "role": "user",
                            "content": [
                                {"type": "input_text", "text": prompt},
                                {"type": "input_image", "image_url": data_url},
                            ],
                        },
                    ],
                    "text": {
                        "format": {
                            "type": "json_schema",
                            "name": "product_attributes",
                            "strict": False,
                            "schema": {
                                "type": "object",
                                "additionalProperties": False,
                                "properties": {
                                    "valid_product": {"type": "boolean"},
                                    "confidence": {
                                        "type": "number",
                                        "minimum": 0,
                                        "maximum": 1,
                                    },
                                    "reason": {"type": ["string", "null"]},
                                    "category": {"type": "string"},
                                    "product_type": {"type": "string"},
                                    "color": {"type": "string"},
                                    "material": {"type": "string"},
                                    "style": {"type": "string"},
                                    "visible_text_brand": {
                                        "type": "string",
                                    },
                                    "target_audience": {
                                        "type": "string",
                                    },
                                },
                                "required": [
                                    "valid_product",
                                    "confidence",
                                ],
                            },
                        },
                    },
                },
            )
            response.raise_for_status()
            return cast(dict[str, Any], response.json())

    def _build_data_url(self, image_content: bytes, content_type: str) -> str:
        encoded_image = base64.b64encode(image_content).decode("ascii")
        return f"data:{content_type};base64,{encoded_image}"

    def _extract_output_text(self, payload: dict[str, Any]) -> str:
        if isinstance(payload.get("output_text"), str):
            return cast(str, payload["output_text"])

        for output_item in payload.get("output", []):
            for content_item in output_item.get("content", []):
                if content_item.get("type") == "output_text":
                    text = content_item.get("text")
                    if isinstance(text, str):
                        json.loads(text)
                        return text

        raise ValueError("OpenAI response did not include structured output text")
