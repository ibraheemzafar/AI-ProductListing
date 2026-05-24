import asyncio
from time import perf_counter

from pydantic import ValidationError

from app.core.errors import AppError, NotFoundError
from app.features.ai_analysis.models import AiRequestLog
from app.features.ai_analysis.openai_client import TokenUsage
from app.features.listing_generation.openai_client import (
    ListingGenerationClient,
    ListingGenerationResult,
)
from app.features.listing_generation.prompts import ListingPromptBuilder
from app.features.listing_generation.repositories import ListingGenerationRepository
from app.features.listing_generation.schemas import (
    GeneratedListingResponse,
    ListingDetailResponse,
    ListingHistoryItem,
    ListingHistoryResponse,
)

MAX_LISTINGS_PAGE_SIZE = 50


class ListingGenerationService:
    def __init__(
        self,
        repository: ListingGenerationRepository,
        listing_client: ListingGenerationClient,
        prompt_builder: ListingPromptBuilder,
        retry_attempts: int,
    ) -> None:
        self._repository = repository
        self._listing_client = listing_client
        self._prompt_builder = prompt_builder
        self._retry_attempts = retry_attempts

    async def generate_listing(
        self,
        user_id: str,
        analysis_id: str,
    ) -> GeneratedListingResponse:
        if not analysis_id.strip():
            raise AppError("Analysis id is required")

        analysis = await self._repository.get_analysis_for_user(
            analysis_id=analysis_id,
            user_id=user_id,
        )
        if analysis is None:
            raise AppError("Product analysis was not found")

        prompt = self._prompt_builder.build_prompt(analysis)
        started_at = perf_counter()
        token_usage = TokenUsage(input_tokens=None, output_tokens=None, total_tokens=None)
        try:
            generation_result = await self._generate_with_retries(prompt.content)
            token_usage = generation_result.token_usage
            saved_listing = await self._repository.save_generated_listing(
                analysis=analysis,
                listing=generation_result.listing,
            )
            await self._log_request(
                user_id=user_id,
                product_id=analysis.product_id,
                image_id=analysis.image_id,
                prompt_version=prompt.version,
                token_usage=token_usage,
                latency_ms=self._elapsed_ms(started_at),
                success=True,
                error_message=None,
            )
            return GeneratedListingResponse.from_model(saved_listing)
        except (ValidationError, ValueError) as error:
            await self._log_request(
                user_id=user_id,
                product_id=analysis.product_id,
                image_id=analysis.image_id,
                prompt_version=prompt.version,
                token_usage=token_usage,
                latency_ms=self._elapsed_ms(started_at),
                success=False,
                error_message=str(error),
            )
            raise AppError("AI returned an invalid listing. Please try again.") from error
        except Exception as error:
            await self._log_request(
                user_id=user_id,
                product_id=analysis.product_id,
                image_id=analysis.image_id,
                prompt_version=prompt.version,
                token_usage=token_usage,
                latency_ms=self._elapsed_ms(started_at),
                success=False,
                error_message=str(error),
            )
            raise AppError("Listing generation failed. Please try again.") from error

    async def list_generated_listings(
        self,
        user_id: str,
        limit: int,
        offset: int,
    ) -> ListingHistoryResponse:
        if limit <= 0 or limit > MAX_LISTINGS_PAGE_SIZE:
            raise AppError(f"Limit must be between 1 and {MAX_LISTINGS_PAGE_SIZE}")
        if offset < 0:
            raise AppError("Offset must be zero or greater")

        rows, total = await self._repository.list_generated_listings_for_user(
            user_id=user_id,
            limit=limit,
            offset=offset,
        )
        return ListingHistoryResponse(
            listings=[
                ListingHistoryItem.from_models(listing, image)
                for listing, image in rows
            ],
            total=total,
            limit=limit,
            offset=offset,
        )

    async def get_generated_listing_detail(
        self,
        user_id: str,
        listing_id: str,
    ) -> ListingDetailResponse:
        if not listing_id.strip():
            raise AppError("Listing id is required")

        row = await self._repository.get_generated_listing_detail_for_user(
            listing_id=listing_id,
            user_id=user_id,
        )
        if row is None:
            raise NotFoundError("Generated listing was not found")

        listing, analysis, image = row
        return ListingDetailResponse.from_models(
            listing=listing,
            analysis=analysis,
            image=image,
        )

    async def _generate_with_retries(self, prompt: str) -> ListingGenerationResult:
        last_error: Exception | None = None
        for attempt in range(self._retry_attempts):
            try:
                return await self._listing_client.generate_listing(prompt)
            except Exception as error:
                last_error = error
                if attempt + 1 < self._retry_attempts:
                    await asyncio.sleep(0.25 * (attempt + 1))
        if last_error:
            raise last_error
        raise AppError("Listing generation failed. Please try again.")

    async def _log_request(
        self,
        user_id: str,
        product_id: str,
        image_id: str,
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
                image_id=image_id,
                workflow_name="listing_generation",
                model_name=self._listing_client.model_name,
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
