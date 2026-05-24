import json
from dataclasses import dataclass
from typing import Any, Protocol, cast

import httpx

from app.core.errors import ConfigurationError
from app.features.ai_analysis.openai_client import TokenUsage
from app.features.listing_generation.schemas import ListingContent


@dataclass(frozen=True)
class ListingImprovementResult:
    listing: ListingContent
    token_usage: TokenUsage


class ListingImprovementClient(Protocol):
    model_name: str

    async def improve_listing(self, prompt: str) -> ListingImprovementResult:
        pass


class OpenAIListingImprovementClient:
    def __init__(self, api_key: str, model_name: str, timeout_seconds: float) -> None:
        self.model_name = model_name
        self._api_key = api_key
        self._timeout_seconds = timeout_seconds

    async def improve_listing(self, prompt: str) -> ListingImprovementResult:
        if not self._api_key:
            raise ConfigurationError("OPENAI_API_KEY is required for listing improvement")

        response_payload = await self._create_response(prompt)
        listing = ListingContent.model_validate_json(self._extract_output_text(response_payload))
        usage = response_payload.get("usage") or {}
        return ListingImprovementResult(
            listing=listing,
            token_usage=TokenUsage(
                input_tokens=usage.get("input_tokens"),
                output_tokens=usage.get("output_tokens"),
                total_tokens=usage.get("total_tokens"),
            ),
        )

    async def _create_response(self, prompt: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
            response = await client.post(
                "https://api.openai.com/v1/responses",
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model_name,
                    "input": [{"role": "user", "content": prompt}],
                    "text": {
                        "format": {
                            "type": "json_schema",
                            "name": "improved_listing",
                            "strict": True,
                            "schema": {
                                "type": "object",
                                "additionalProperties": False,
                                "properties": {
                                    "title": {"type": "string"},
                                    "short_description": {"type": "string"},
                                    "long_description": {"type": "string"},
                                    "seo_keywords": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                    },
                                    "product_tags": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                    },
                                },
                                "required": [
                                    "title",
                                    "short_description",
                                    "long_description",
                                    "seo_keywords",
                                    "product_tags",
                                ],
                            },
                        },
                    },
                },
            )
            response.raise_for_status()
            return cast(dict[str, Any], response.json())

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
