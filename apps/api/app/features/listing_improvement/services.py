import asyncio
from time import perf_counter
from uuid import uuid4

from pydantic import ValidationError

from app.core.errors import AppError, NotFoundError
from app.features.ai_analysis.models import AiRequestLog
from app.features.ai_analysis.openai_client import TokenUsage
from app.features.billing_meter.pricing import UsageInput
from app.features.billing_meter.service import RequestMeter
from app.features.listing_improvement.openai_client import (
    ListingImprovementClient,
    ListingImprovementResult,
)
from app.features.listing_improvement.prompts import ListingImprovementPromptBuilder
from app.features.listing_improvement.repositories import ListingImprovementRepository
from app.features.listing_improvement.schemas import (
    AcceptListingVersionResponse,
    ListingImprovementResponse,
    ListingVersionHistoryResponse,
    ListingVersionResponse,
)


class ListingImprovementService:
    def __init__(
        self,
        repository: ListingImprovementRepository,
        improvement_client: ListingImprovementClient,
        prompt_builder: ListingImprovementPromptBuilder,
        retry_attempts: int,
        billing_meter: RequestMeter,
    ) -> None:
        self._repository = repository
        self._improvement_client = improvement_client
        self._prompt_builder = prompt_builder
        self._retry_attempts = retry_attempts
        self._billing_meter = billing_meter

    async def improve_listing(
        self,
        user_id: str,
        listing_id: str,
    ) -> ListingImprovementResponse:
        if not listing_id.strip():
            raise AppError("Listing id is required")

        row = await self._repository.get_listing_with_latest_seo_for_user(
            listing_id=listing_id,
            user_id=user_id,
        )
        if row is None:
            raise NotFoundError("Generated listing or SEO analysis was not found")

        listing, seo_analysis = row

        await self._billing_meter.authorize(user_id)

        prompt = self._prompt_builder.build_prompt(listing=listing, seo_analysis=seo_analysis)
        started_at = perf_counter()
        token_usage = TokenUsage(input_tokens=None, output_tokens=None, total_tokens=None)
        try:
            improvement_result = await self._improve_with_retries(prompt.content)
            token_usage = improvement_result.token_usage
            version = await self._repository.create_listing_version(
                listing=listing,
                content=improvement_result.listing,
            )
            request_log_id = str(uuid4())
            charge = await self._billing_meter.charge(
                user_id=user_id,
                workflow="listing_improvement",
                usage=UsageInput(
                    input_tokens=token_usage.input_tokens,
                    output_tokens=token_usage.output_tokens,
                ),
                request_log_id=request_log_id,
            )
            await self._log_request(
                user_id=user_id,
                product_id=listing.product_id,
                prompt_version=prompt.version,
                token_usage=token_usage,
                latency_ms=self._elapsed_ms(started_at),
                success=True,
                error_message=None,
                request_log_id=request_log_id,
                credits_charged=charge.credits_charged,
                wallet_transaction_id=charge.transaction_id,
            )
            return ListingImprovementResponse.from_models(
                original_listing=listing,
                version=version,
            )
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
            raise AppError("AI returned an invalid improved listing. Please try again.") from error
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
            raise AppError("Listing improvement failed. Please try again.") from error

    async def list_versions(
        self,
        user_id: str,
        listing_id: str,
    ) -> ListingVersionHistoryResponse:
        versions = await self._repository.list_versions_for_user(
            listing_id=listing_id,
            user_id=user_id,
        )
        if versions is None:
            raise NotFoundError("Generated listing was not found")
        return ListingVersionHistoryResponse(
            versions=[ListingVersionResponse.from_model(version) for version in versions],
        )

    async def accept_version(
        self,
        user_id: str,
        listing_id: str,
        version_id: str,
    ) -> AcceptListingVersionResponse:
        if not version_id.strip():
            raise AppError("Version id is required")

        row = await self._repository.accept_version_for_user(
            listing_id=listing_id,
            version_id=version_id,
            user_id=user_id,
        )
        if row is None:
            raise NotFoundError("Listing version was not found")

        listing, version = row
        return AcceptListingVersionResponse.from_models(listing=listing, version=version)

    async def _improve_with_retries(self, prompt: str) -> ListingImprovementResult:
        last_error: Exception | None = None
        for attempt in range(self._retry_attempts):
            try:
                return await self._improvement_client.improve_listing(prompt)
            except Exception as error:
                last_error = error
                if attempt + 1 < self._retry_attempts:
                    await asyncio.sleep(0.25 * (attempt + 1))
        if last_error:
            raise last_error
        raise AppError("Listing improvement failed. Please try again.")

    async def _log_request(
        self,
        user_id: str,
        product_id: str,
        prompt_version: str,
        token_usage: TokenUsage,
        latency_ms: int,
        success: bool,
        error_message: str | None,
        request_log_id: str | None = None,
        credits_charged: int | None = None,
        wallet_transaction_id: str | None = None,
    ) -> None:
        await self._repository.create_request_log(
            AiRequestLog(
                id=request_log_id or str(uuid4()),
                user_id=user_id,
                product_id=product_id,
                image_id=None,
                workflow_name="listing_improvement",
                model_name=self._improvement_client.model_name,
                prompt_version=prompt_version,
                input_tokens=token_usage.input_tokens,
                output_tokens=token_usage.output_tokens,
                total_tokens=token_usage.total_tokens,
                latency_ms=latency_ms,
                success=success,
                status="success" if success else "failure",
                error_message=error_message,
                credits_charged=credits_charged,
                wallet_transaction_id=wallet_transaction_id,
            ),
        )

    def _elapsed_ms(self, started_at: float) -> int:
        return round((perf_counter() - started_at) * 1000)
