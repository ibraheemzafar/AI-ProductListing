import json
from dataclasses import dataclass
from pathlib import Path

from app.core.errors import ConfigurationError
from app.features.listing_generation.models import GeneratedListing


@dataclass(frozen=True)
class PromptTemplate:
    content: str
    version: str


class SeoEvaluationPromptBuilder:
    def __init__(self, prompt_path: Path | None = None) -> None:
        self._prompt_path = prompt_path or self._find_prompt_path()

    def build_prompt(self, listing: GeneratedListing) -> PromptTemplate:
        if not self._prompt_path.exists():
            raise ConfigurationError("SEO evaluator prompt is missing")

        listing_context = {
            "title": listing.title,
            "short_description": listing.short_description,
            "long_description": listing.long_description,
            "seo_keywords": listing.seo_keywords,
            "product_tags": listing.product_tags,
        }
        content = self._prompt_path.read_text(encoding="utf-8").strip()
        return PromptTemplate(
            content=content.replace(
                "{{listing_context}}",
                json.dumps(listing_context, sort_keys=True),
            ),
            version="seo-evaluator-v1",
        )

    def _find_prompt_path(self) -> Path:
        for parent in Path(__file__).resolve().parents:
            prompt_path = parent / "docs" / "prompts" / "seo-evaluator.md"
            if prompt_path.exists():
                return prompt_path
        return Path("docs/prompts/seo-evaluator.md")
