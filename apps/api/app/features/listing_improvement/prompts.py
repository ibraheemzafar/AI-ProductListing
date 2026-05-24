import json
from dataclasses import dataclass
from pathlib import Path

from app.core.errors import ConfigurationError
from app.features.listing_generation.models import GeneratedListing
from app.features.seo_evaluation.models import SeoAnalysis


@dataclass(frozen=True)
class PromptTemplate:
    content: str
    version: str


class ListingImprovementPromptBuilder:
    def __init__(self, prompt_path: Path | None = None) -> None:
        self._prompt_path = prompt_path or self._find_prompt_path()

    def build_prompt(self, listing: GeneratedListing, seo_analysis: SeoAnalysis) -> PromptTemplate:
        if not self._prompt_path.exists():
            raise ConfigurationError("Listing improver prompt is missing")

        rewrite_context = {
            "current_listing": {
                "title": listing.title,
                "short_description": listing.short_description,
                "long_description": listing.long_description,
                "seo_keywords": listing.seo_keywords,
                "product_tags": listing.product_tags,
            },
            "seo_analysis": {
                "seo_score": seo_analysis.seo_score,
                "readability_score": seo_analysis.readability_score,
                "keyword_optimization_feedback": seo_analysis.keyword_optimization_feedback,
                "title_quality_feedback": seo_analysis.title_quality_feedback,
                "description_quality_feedback": seo_analysis.description_quality_feedback,
                "strengths": seo_analysis.strengths,
                "weaknesses": seo_analysis.weaknesses,
                "improvement_suggestions": seo_analysis.improvement_suggestions,
            },
        }
        content = self._prompt_path.read_text(encoding="utf-8").strip()
        return PromptTemplate(
            content=content.replace(
                "{{rewrite_context}}",
                json.dumps(rewrite_context, sort_keys=True),
            ),
            version="listing-improver-v1",
        )

    def _find_prompt_path(self) -> Path:
        for parent in Path(__file__).resolve().parents:
            prompt_path = parent / "docs" / "prompts" / "listing-improver.md"
            if prompt_path.exists():
                return prompt_path
        return Path("docs/prompts/listing-improver.md")
