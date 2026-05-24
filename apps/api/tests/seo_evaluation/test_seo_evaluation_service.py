from datetime import UTC, datetime

import pytest

from app.core.errors import AppError
from app.features.ai_analysis.models import AiRequestLog
from app.features.ai_analysis.openai_client import TokenUsage
from app.features.listing_generation.models import GeneratedListing
from app.features.seo_evaluation.models import SeoAnalysis
from app.features.seo_evaluation.openai_client import SeoEvaluationResult
from app.features.seo_evaluation.prompts import PromptTemplate, SeoEvaluationPromptBuilder
from app.features.seo_evaluation.repositories import SeoEvaluationRepository
from app.features.seo_evaluation.schemas import SeoEvaluationContent
from app.features.seo_evaluation.services import SeoEvaluationService


class InMemorySeoEvaluationRepository(SeoEvaluationRepository):
    def __init__(self, listing: GeneratedListing | None) -> None:
        self.listing = listing
        self.saved_analysis: SeoAnalysis | None = None
        self.logs: list[AiRequestLog] = []

    async def get_listing_for_user(
        self,
        listing_id: str,
        user_id: str,
    ) -> GeneratedListing | None:
        del user_id
        if self.listing and self.listing.id == listing_id:
            return self.listing
        return None

    async def save_seo_analysis(
        self,
        listing: GeneratedListing,
        analysis: SeoEvaluationContent,
    ) -> SeoAnalysis:
        self.saved_analysis = SeoAnalysis(
            id="seo-analysis-1",
            listing_id=listing.id,
            product_id=listing.product_id,
            seo_score=analysis.seo_score,
            readability_score=analysis.readability_score,
            keyword_optimization_feedback=analysis.keyword_optimization_feedback,
            title_quality_feedback=analysis.title_quality_feedback,
            description_quality_feedback=analysis.description_quality_feedback,
            strengths=analysis.strengths,
            weaknesses=analysis.weaknesses,
            improvement_suggestions=analysis.improvement_suggestions,
            raw_output=analysis.model_dump(),
            created_at=datetime.now(UTC),
        )
        return self.saved_analysis

    async def create_request_log(self, log: AiRequestLog) -> None:
        self.logs.append(log)


class FakeSeoClient:
    model_name = "fake-text"

    def __init__(self, failures_before_success: int = 0) -> None:
        self.failures_before_success = failures_before_success
        self.calls = 0

    async def evaluate_listing(self, prompt: str) -> SeoEvaluationResult:
        del prompt
        self.calls += 1
        if self.calls <= self.failures_before_success:
            raise RuntimeError("temporary OpenAI failure")
        return SeoEvaluationResult(
            analysis=build_seo_content(),
            token_usage=TokenUsage(input_tokens=12, output_tokens=34, total_tokens=46),
        )


class FakePromptBuilder(SeoEvaluationPromptBuilder):
    def __init__(self) -> None:
        pass

    def build_prompt(self, listing: GeneratedListing) -> PromptTemplate:
        del listing
        return PromptTemplate(content="Evaluate SEO.", version="test-seo-v1")


@pytest.mark.asyncio
async def test_seo_evaluation_service_saves_result_and_logs_success() -> None:
    repository = InMemorySeoEvaluationRepository(listing=build_listing())
    service = SeoEvaluationService(
        repository=repository,
        seo_client=FakeSeoClient(),
        prompt_builder=FakePromptBuilder(),
        retry_attempts=3,
    )

    response = await service.analyze_listing_seo(user_id="user-1", listing_id="listing-1")

    assert response.analysis.seo_score == 84
    assert repository.saved_analysis is not None
    assert repository.logs[0].workflow_name == "seo_evaluation"
    assert repository.logs[0].total_tokens == 46
    assert repository.logs[0].success is True


@pytest.mark.asyncio
async def test_seo_evaluation_service_retries_ai_failures() -> None:
    seo_client = FakeSeoClient(failures_before_success=1)
    service = SeoEvaluationService(
        repository=InMemorySeoEvaluationRepository(listing=build_listing()),
        seo_client=seo_client,
        prompt_builder=FakePromptBuilder(),
        retry_attempts=3,
    )

    response = await service.analyze_listing_seo(user_id="user-1", listing_id="listing-1")

    assert response.analysis.readability_score == 91
    assert seo_client.calls == 2


@pytest.mark.asyncio
async def test_seo_evaluation_service_handles_missing_or_unauthorized_listing() -> None:
    service = SeoEvaluationService(
        repository=InMemorySeoEvaluationRepository(listing=None),
        seo_client=FakeSeoClient(),
        prompt_builder=FakePromptBuilder(),
        retry_attempts=3,
    )

    with pytest.raises(AppError, match="Generated listing was not found"):
        await service.analyze_listing_seo(user_id="user-1", listing_id="missing-listing")


@pytest.mark.asyncio
async def test_seo_evaluation_service_logs_ai_failure() -> None:
    repository = InMemorySeoEvaluationRepository(listing=build_listing())
    service = SeoEvaluationService(
        repository=repository,
        seo_client=FakeSeoClient(failures_before_success=3),
        prompt_builder=FakePromptBuilder(),
        retry_attempts=2,
    )

    with pytest.raises(AppError, match="SEO analysis failed"):
        await service.analyze_listing_seo(user_id="user-1", listing_id="listing-1")

    assert repository.logs[0].success is False
    assert repository.logs[0].error_message == "temporary OpenAI failure"


def build_listing() -> GeneratedListing:
    return GeneratedListing(
        id="listing-1",
        product_id="product-1",
        analysis_id="analysis-1",
        title="Minimal Black Cotton T-Shirt",
        short_description="A soft black cotton T-shirt for everyday wear.",
        long_description=(
            "This minimal black cotton T-shirt is designed for comfortable daily wear."
        ),
        seo_keywords=["black cotton t-shirt", "minimal shirt"],
        product_tags=["t-shirt", "cotton", "black"],
        raw_output={},
        created_at=datetime.now(UTC),
    )


def build_seo_content() -> SeoEvaluationContent:
    return SeoEvaluationContent(
        seo_score=84,
        readability_score=91,
        keyword_optimization_feedback="Keywords are relevant but could include buyer intent.",
        title_quality_feedback="Title is clear and under the recommended length.",
        description_quality_feedback=(
            "Description is readable but could mention core benefits earlier."
        ),
        strengths=["Clear product type", "Readable copy"],
        weaknesses=["Limited keyword variety"],
        improvement_suggestions=["Add one intent keyword", "Lead with the main benefit"],
    )
