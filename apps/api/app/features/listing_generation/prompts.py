import json
from dataclasses import dataclass
from pathlib import Path

from app.core.errors import ConfigurationError
from app.features.ai_analysis.models import ProductAnalysisResult


@dataclass(frozen=True)
class PromptTemplate:
    content: str
    version: str


class ListingPromptBuilder:
    def __init__(self, prompt_path: Path | None = None) -> None:
        self._prompt_path = prompt_path or self._find_prompt_path()

    def build_prompt(self, analysis: ProductAnalysisResult) -> PromptTemplate:
        if not self._prompt_path.exists():
            raise ConfigurationError("Listing generation prompt is missing")

        product_attributes = {
            "category": analysis.category,
            "product_type": analysis.product_type,
            "color": analysis.color,
            "material": analysis.material,
            "style": analysis.style,
            "visible_text_brand": analysis.visible_text_brand,
            "target_audience": analysis.target_audience,
        }
        content = self._prompt_path.read_text(encoding="utf-8").strip()
        return PromptTemplate(
            content=content.replace(
                "{{product_attributes}}",
                json.dumps(product_attributes, sort_keys=True),
            ),
            version="listing-generator-v1",
        )

    def _find_prompt_path(self) -> Path:
        for parent in Path(__file__).resolve().parents:
            prompt_path = parent / "docs" / "prompts" / "listing-generator.md"
            if prompt_path.exists():
                return prompt_path
        return Path("docs/prompts/listing-generator.md")
