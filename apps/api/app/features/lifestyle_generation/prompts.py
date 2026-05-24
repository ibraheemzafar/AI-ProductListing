import json
from dataclasses import dataclass
from pathlib import Path

from app.core.errors import ConfigurationError
from app.features.lifestyle_generation.schemas import ScenePreset


@dataclass(frozen=True)
class PromptTemplate:
    content: str
    version: str


class LifestyleScenePromptBuilder:
    def __init__(self, prompt_path: Path | None = None) -> None:
        self._prompt_path = prompt_path or self._find_prompt_path()

    def build_prompt(
        self,
        scene_preset: ScenePreset,
        custom_prompt: str | None,
    ) -> PromptTemplate:
        if not self._prompt_path.exists():
            raise ConfigurationError("Lifestyle scene generator prompt is missing")

        scene_context = {
            "scene_preset": scene_preset,
            "preset_guidance": self._preset_guidance(scene_preset),
            "custom_prompt": custom_prompt.strip() if custom_prompt else None,
        }
        content = self._prompt_path.read_text(encoding="utf-8").strip()
        return PromptTemplate(
            content=content.replace(
                "{{scene_context}}",
                json.dumps(scene_context, sort_keys=True),
            ),
            version="lifestyle-scene-generator-v1",
        )

    def _preset_guidance(self, scene_preset: ScenePreset) -> str:
        guidance = {
            "luxury_setup": "Premium lighting, refined props, elegant retail composition.",
            "wooden_table_setup": "Natural wood surface, warm lighting, simple product styling.",
            "studio_white_background": "Clean white studio scene with soft shadows and no clutter.",
            "cozy_home_environment": "Warm home setting with soft textures and realistic ambience.",
            "modern_ecommerce_hero_shot": "Polished hero image with modern ecommerce composition.",
        }
        return guidance[scene_preset]

    def _find_prompt_path(self) -> Path:
        for parent in Path(__file__).resolve().parents:
            prompt_path = parent / "docs" / "prompts" / "lifestyle-scene-generator.md"
            if prompt_path.exists():
                return prompt_path
        return Path("docs/prompts/lifestyle-scene-generator.md")
