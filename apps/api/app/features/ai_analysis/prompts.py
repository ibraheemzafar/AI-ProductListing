from dataclasses import dataclass
from pathlib import Path

from app.core.errors import ConfigurationError


@dataclass(frozen=True)
class PromptTemplate:
    content: str
    version: str


class PromptLoader:
    def __init__(self, prompt_path: Path | None = None) -> None:
        self._prompt_path = prompt_path or self._find_prompt_path()

    def load_product_analysis_prompt(self) -> PromptTemplate:
        if not self._prompt_path.exists():
            raise ConfigurationError("Product analysis prompt is missing")
        content = self._prompt_path.read_text(encoding="utf-8").strip()
        return PromptTemplate(content=content, version="product-analysis-v1")

    def _find_prompt_path(self) -> Path:
        for parent in Path(__file__).resolve().parents:
            prompt_path = parent / "docs" / "prompts" / "product-analysis.md"
            if prompt_path.exists():
                return prompt_path
        return Path("docs/prompts/product-analysis.md")
