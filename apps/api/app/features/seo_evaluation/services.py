import asyncio
from time import perf_counter

from pydantic import ValidationError

from app.core.errors import AppError, NotFoundError
from app.features.ai_analysis.models import AiRequestLog
from app.features.ai_analysis.openai_client import TokenUsage
from app.features.seo_evaluation.openai_client import (
    SeoEvaluationClient,
    SeoEvaluationResult,
)
from app.features.seo_evaluation.prompts import SeoEvaluationPromptBuilder
from app.features.seo_evaluation.repositories import SeoEvaluationRepository
from app.features.seo_evaluation.schemas import SeoAnalysisResponse


class SeoEvaluationService:
    def __init__(
        self,
        repository: SeoEvaluationRepository,
        seo_client: SeoEvaluationClient,
        prompt_builder: SeoEvaluationPromptBuilder,
        retry_attempts: int,
    ) -> None:
        self._repository = repository
        self._seo_client = seo_client
        self._prompt_builder = prompt_builder
        self._retry_attempts = retry_attempts

    async def analyze_listing_seo(
        self,
        user_id: str,
        listing_id: str,
    ) -> SeoAnalysisResponse:
        if not listing_id.strip():
            raise AppError("Listing id is required")

        listing = await self._repository.get_listing_for_user(
            listing_id=listing_id,
            user_id=user_id,
        )
        if listing is None:
            raise NotFoundError("Generated listing was not found")

        prompt = self._prompt_builder.build_prompt(listing)
        started_at = perf_counter()
        token_usage = TokenUsage(input_tokens=None, output_tokens=None, total_tokens=None)
        try:
            evaluation_result = await self._evaluate_with_retries(prompt.content)
            token_usage = evaluation_result.token_usage
            saved_analysis = await self._repository.save_seo_analysis(
                listing=listing,
                analysis=evaluation_result.analysis,
            )
            await self._log_request(
                user_id=user_id,
                product_id=listing.product_id,
                prompt_version=prompt.version,
                token_usage=token_usage,
                latency_ms=self._elapsed_ms(started_at),
                success=True,
                error_message=None,
            )
            return SeoAnalysisResponse.from_model(saved_analysis)
        except (ValidationError, ValueError) as error:
            await self._log_request(
                user_id=user_id,
                product_id=listing.product_id,
                prompt_version=prompt.version,
                token_usage=token_usage,
                latency_ms=self._elapsed_ms(started_at),
                success=False,
                error_message=str(error),
            )
            raise AppError("AI returned an invalid SEO analysis. Please try again.") from error
        except Exception as error:
            await self._log_request(
                user_id=user_id,
                product_id=listing.product_id,
                prompt_version=prompt.version,
                token_usage=token_usage,
                latency_ms=self._elapsed_ms(started_at),
                success=False,
                error_message=str(error),
            )
            raise AppError("SEO analysis failed. Please try again.") from error

    async def _evaluate_with_retries(self, prompt: str) -> SeoEvaluationResult:
        last_error: Exception | None = None
        for attempt in range(self._retry_attempts):
            try:
                return await self._seo_client.evaluate_listing(prompt)
            except Exception as error:
                last_error = error
                if attempt + 1 < self._retry_attempts:
                    await asyncio.sleep(0.25 * (attempt + 1))
        if last_error:
            raise last_error
        raise AppError("SEO analysis failed. Please try again.")

    async def _log_request(
        self,
        user_id: str,
        product_id: str,
        prompt_version: str,
        token_usage: TokenUsage,
        latency_ms: int,
        success: bool,
        error_message: str | None,
    ) -> None:
        await self._repository.create_request_log(
            AiRequestLog(
                user_id=user_id,
                product_id=product_id,
                image_id=None,
                workflow_name="seo_evaluation",
                model_name=self._seo_client.model_name,
                prompt_version=prompt_version,
                input_tokens=token_usage.input_tokens,
                output_tokens=token_usage.output_tokens,
                total_tokens=token_usage.total_tokens,
                latency_ms=latency_ms,
                success=success,
                status="success" if success else "failure",
                error_message=error_message,
            ),
        )

    def _elapsed_ms(self, started_at: float) -> int:
        return round((perf_counter() - started_at) * 1000)
