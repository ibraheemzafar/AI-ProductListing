import json
from dataclasses import dataclass
from pathlib import Path

from app.core.errors import AppError, ConfigurationError
from app.features.lifestyle_generation.schemas import ImageGenerationCategory


@dataclass(frozen=True)
class PromptTemplate:
    content: str
    version: str


class LifestyleScenePromptBuilder:
    def __init__(self, prompt_path: Path | None = None) -> None:
        self._prompt_path = prompt_path or self._find_prompt_path()

    def build_prompt(
        self,
        category: ImageGenerationCategory,
        custom_prompt: str | None,
    ) -> PromptTemplate:
        if not self._prompt_path.exists():
            raise ConfigurationError("Lifestyle scene generator prompt is missing")

        normalized_custom_prompt = custom_prompt.strip() if custom_prompt else None
        if category == "custom_prompt" and not normalized_custom_prompt:
            raise AppError("Custom prompt is required for custom image generation")

        scene_context = {
            "category": category,
            "preset_guidance": self._preset_guidance(category),
            "custom_prompt": normalized_custom_prompt,
        }
        content = self._prompt_path.read_text(encoding="utf-8").strip()
        return PromptTemplate(
            content=content.replace(
                "{{scene_context}}",
                json.dumps(scene_context, sort_keys=True),
            ),
            version="lifestyle-scene-generator-v1",
        )

    def _preset_guidance(self, category: ImageGenerationCategory) -> str:
        guidance = {
            "studio_white_background": "Clean white studio background, soft shadow, no clutter.",
            "luxury_product_shot": "Premium lighting, refined props, elegant retail composition.",
            "wooden_table_setup": "Natural wood surface, warm lighting, simple product styling.",
            "minimal_ecommerce_background": "Minimal ecommerce background with subtle depth.",
            "lifestyle_home_setup": "Warm home setting with soft textures and realistic ambience.",
            "social_media_banner": (
                "Wide social media banner composition with room for overlay copy."
            ),
            "marketplace_hero_image": "Polished marketplace hero image with clear product focus.",
            "custom_prompt": "Follow the custom prompt while preserving the product accurately.",
        }
        return guidance[category]

    def _find_prompt_path(self) -> Path:
        for parent in Path(__file__).resolve().parents:
            prompt_path = parent / "docs" / "prompts" / "lifestyle-scene-generator.md"
            if prompt_path.exists():
                return prompt_path
        return Path("docs/prompts/lifestyle-scene-generator.md")
