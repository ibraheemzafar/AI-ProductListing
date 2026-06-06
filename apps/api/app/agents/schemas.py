from datetime import UTC, datetime
from uuid import uuid4

from pydantic import BaseModel, Field

from app.features.ai_analysis.schemas import ProductAnalysisResponse
from app.features.image_enhancement.schemas import (
    EnhancedImageResponse,
    ImageEnhancementOperation,
)
from app.features.lifestyle_generation.schemas import (
    GeneratedImageResponse,
    ImageGenerationCategory,
)
from app.features.listing_generation.schemas import GeneratedListingResponse
from app.features.listing_improvement.schemas import (
    AcceptListingVersionResponse,
    ListingImprovementResponse,
)
from app.features.marketplace_optimization.schemas import (
    Marketplace,
    MarketplaceOptimizationResponse,
)
from app.features.seo_evaluation.schemas import SeoAnalysisResponse


class AgentTokenUsage(BaseModel):
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None


class AgentExecutionRecord(BaseModel):
    workflow_id: str
    agent_name: str
    execution_time_ms: int
    success: bool
    token_usage: AgentTokenUsage = Field(default_factory=AgentTokenUsage)
    error_message: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class AgentError(BaseModel):
    agent_name: str
    message: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ProductAnalysisResult(BaseModel):
    analysis: ProductAnalysisResponse


class ListingResult(BaseModel):
    listing: GeneratedListingResponse


class SEOResult(BaseModel):
    seo_analysis: SeoAnalysisResponse


class ListingImprovementResult(BaseModel):
    improvement: ListingImprovementResponse
    accepted_version: AcceptListingVersionResponse | None = None


class MarketplaceResult(BaseModel):
    optimization: MarketplaceOptimizationResponse


class ImageResult(BaseModel):
    enhanced_image: EnhancedImageResponse | None = None
    generated_image: GeneratedImageResponse | None = None


class MarketingAsset(BaseModel):
    channel: str
    content: str


class MarketingResult(BaseModel):
    assets: list[MarketingAsset]


class WorkflowState(BaseModel):
    workflow_id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    image_id: str | None = None
    analysis_id: str | None = None
    listing_id: str | None = None
    seo_analysis_id: str | None = None
    listing_version_id: str | None = None
    marketplace_optimization_id: str | None = None
    enhanced_image_id: str | None = None
    generated_image_id: str | None = None
    product_analysis: ProductAnalysisResult | None = None
    listing_generation: ListingResult | None = None
    seo_evaluation: SEOResult | None = None
    listing_improvement: ListingImprovementResult | None = None
    marketplace_optimization: MarketplaceResult | None = None
    image_generation: ImageResult | None = None
    marketing: MarketingResult | None = None
    completed_steps: list[str] = Field(default_factory=list)
    execution_log: list[AgentExecutionRecord] = Field(default_factory=list)
    errors: list[AgentError] = Field(default_factory=list)

    def mark_completed(self, step_name: str) -> None:
        if step_name not in self.completed_steps:
            self.completed_steps.append(step_name)

    def record_error(self, agent_name: str, message: str) -> None:
        self.errors.append(AgentError(agent_name=agent_name, message=message))

    def record_execution(self, record: AgentExecutionRecord) -> None:
        self.execution_log.append(record)


class OpenAIAgentSpec(BaseModel):
    name: str
    instructions: str


class ProductAnalysisAgentInput(BaseModel):
    user_id: str = Field(min_length=1)
    image_id: str = Field(min_length=1)


class ListingGenerationAgentInput(BaseModel):
    user_id: str = Field(min_length=1)
    analysis_id: str | None = Field(default=None)


class SEOEvaluationAgentInput(BaseModel):
    user_id: str = Field(min_length=1)
    listing_id: str | None = Field(default=None)


class ListingImprovementAgentInput(BaseModel):
    user_id: str = Field(min_length=1)
    listing_id: str | None = Field(default=None)
    accept_improved_version: bool = True


class MarketplaceAgentInput(BaseModel):
    user_id: str = Field(min_length=1)
    marketplace: Marketplace = "shopify"
    listing_id: str | None = Field(default=None)


class ImageGenerationAgentInput(BaseModel):
    user_id: str = Field(min_length=1)
    listing_id: str | None = Field(default=None)
    enhancement_operation: ImageEnhancementOperation | None = None
    generation_category: ImageGenerationCategory | None = None
    custom_prompt: str | None = Field(default=None, max_length=800)


class MarketingAgentInput(BaseModel):
    user_id: str = Field(min_length=1)
    listing_id: str | None = Field(default=None)
    channels: list[str] = Field(default_factory=lambda: ["facebook_ads", "instagram_captions"])


class FullListingWorkflowInput(BaseModel):
    user_id: str = Field(min_length=1)
    image_id: str = Field(min_length=1)
    marketplace: Marketplace = "shopify"
    accept_improved_version: bool = True


class FullListingWorkflowOutput(BaseModel):
    state: WorkflowState
    product_analysis: ProductAnalysisResult
    listing_generation: ListingResult
    seo_evaluation: SEOResult
    listing_improvement: ListingImprovementResult
    marketplace_optimization: MarketplaceResult
