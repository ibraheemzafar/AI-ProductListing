import json
from dataclasses import dataclass
from pathlib import Path

from app.core.errors import ConfigurationError
from app.features.listing_generation.models import GeneratedListing
from app.features.marketplace_optimization.schemas import Marketplace


@dataclass(frozen=True)
class PromptTemplate:
    content: str
    version: str


class MarketplaceOptimizationPromptBuilder:
    def __init__(self, prompt_path: Path | None = None) -> None:
        self._prompt_path = prompt_path or self._find_prompt_path()

    def build_prompt(self, listing: GeneratedListing, marketplace: Marketplace) -> PromptTemplate:
        if not self._prompt_path.exists():
            raise ConfigurationError("Marketplace optimizer prompt is missing")

        marketplace_context = {
            "marketplace": marketplace,
            "platform_guidance": self._platform_guidance(marketplace),
            "current_listing": {
                "title": listing.title,
                "short_description": listing.short_description,
                "long_description": listing.long_description,
                "seo_keywords": listing.seo_keywords,
                "product_tags": listing.product_tags,
            },
        }
        content = self._prompt_path.read_text(encoding="utf-8").strip()
        return PromptTemplate(
            content=content.replace(
                "{{marketplace_context}}",
                json.dumps(marketplace_context, sort_keys=True),
            ),
            version="marketplace-optimizer-v1",
        )

    def _platform_guidance(self, marketplace: Marketplace) -> str:
        guidance = {
            "shopify": "Use brand-friendly ecommerce copy with SEO title and clean tags.",
            "amazon": "Use search-rich title phrasing, scannable bullets, and concise claims.",
            "etsy": "Use handmade/gift-oriented discovery language and descriptive tags.",
            "daraz": (
                "Use clear regional marketplace phrasing, practical benefits, and search terms."
            ),
            "woocommerce": (
                "Use flexible storefront copy with SEO-friendly title, readable description, "
                "and practical product tags."
            ),
            "ebay": (
                "Use direct marketplace language, search-oriented title terms, condition-neutral "
                "benefits, and concise buyer-focused bullets."
            ),
            "generic_store": (
                "Use broadly reusable ecommerce copy suitable for an independent online store."
            ),
        }
        return guidance[marketplace]

    def _find_prompt_path(self) -> Path:
        for parent in Path(__file__).resolve().parents:
            prompt_path = parent / "docs" / "prompts" / "marketplace-optimizer.md"
            if prompt_path.exists():
                return prompt_path
        return Path("docs/prompts/marketplace-optimizer.md")
