import asyncio
from time import perf_counter
from uuid import uuid4

from pydantic import ValidationError

from app.core.errors import AppError, NotFoundError
from app.features.ai_analysis.models import AiRequestLog
from app.features.ai_analysis.openai_client import TokenUsage
from app.features.billing_meter.pricing import UsageInput
from app.features.billing_meter.service import RequestMeter
from app.features.marketplace_optimization.openai_client import (
    MarketplaceOptimizationClient,
    MarketplaceOptimizationResult,
)
from app.features.marketplace_optimization.prompts import MarketplaceOptimizationPromptBuilder
from app.features.marketplace_optimization.repositories import MarketplaceOptimizationRepository
from app.features.marketplace_optimization.schemas import (
    Marketplace,
    MarketplaceOptimizationListResponse,
    MarketplaceOptimizationResponse,
)


class MarketplaceOptimizationService:
    def __init__(
        self,
        repository: MarketplaceOptimizationRepository,
        optimization_client: MarketplaceOptimizationClient,
        prompt_builder: MarketplaceOptimizationPromptBuilder,
        retry_attempts: int,
        billing_meter: RequestMeter,
    ) -> None:
        self._repository = repository
        self._optimization_client = optimization_client
        self._prompt_builder = prompt_builder
        self._retry_attempts = retry_attempts
        self._billing_meter = billing_meter

    async def list_optimizations(
        self,
        user_id: str,
        listing_id: str,
    ) -> MarketplaceOptimizationListResponse:
        if not listing_id.strip():
            raise AppError("Listing id is required")

        listing = await self._repository.get_listing_for_user(
            listing_id=listing_id,
            user_id=user_id,
        )
        if listing is None:
            raise NotFoundError("Generated listing was not found")

        optimizations = await self._repository.list_optimizations(listing_id=listing_id)
        # Rows are ordered newest-first; keep only the latest per marketplace.
        latest_by_marketplace: dict[str, MarketplaceOptimizationResponse] = {}
        for optimization in optimizations:
            latest_by_marketplace.setdefault(
                optimization.marketplace,
                MarketplaceOptimizationResponse.from_model(optimization),
            )
        return MarketplaceOptimizationListResponse(
            optimizations=list(latest_by_marketplace.values()),
        )

    async def optimize_listing(
        self,
        user_id: str,
        listing_id: str,
        marketplace: Marketplace,
        force: bool = False,
    ) -> MarketplaceOptimizationResponse:
        if not listing_id.strip():
            raise AppError("Listing id is required")

        listing = await self._repository.get_listing_for_user(
            listing_id=listing_id,
            user_id=user_id,
        )
        if listing is None:
            raise NotFoundError("Generated listing was not found")

        if not force:
            # Reuse a stored optimization for this marketplace instead of re-running the AI
            # (saves credits and avoids duplicate rows).
            existing = await self._repository.get_optimization(
                listing_id=listing_id,
                marketplace=marketplace,
            )
            if existing is not None:
                return MarketplaceOptimizationResponse.from_model(existing)

        await self._billing_meter.authorize(user_id)

        prompt = self._prompt_builder.build_prompt(listing=listing, marketplace=marketplace)
        started_at = perf_counter()
        token_usage = TokenUsage(input_tokens=None, output_tokens=None, total_tokens=None)
        try:
            optimization_result = await self._optimize_with_retries(prompt.content)
            token_usage = optimization_result.token_usage
            saved_optimization = await self._repository.save_optimization(
                listing=listing,
                marketplace=marketplace,
                content=optimization_result.optimization,
            )
            request_log_id = str(uuid4())
            charge = await self._billing_meter.charge(
                user_id=user_id,
                workflow="marketplace_optimization",
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
            return MarketplaceOptimizationResponse.from_model(saved_optimization)
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
            raise AppError(
                "AI returned an invalid marketplace optimization. Please try again.",
            ) from error
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
            raise AppError("Marketplace optimization failed. Please try again.") from error

    async def _optimize_with_retries(self, prompt: str) -> MarketplaceOptimizationResult:
        last_error: Exception | None = None
        for attempt in range(self._retry_attempts):
            try:
                return await self._optimization_client.optimize_listing(prompt)
            except Exception as error:
                last_error = error
                if attempt + 1 < self._retry_attempts:
                    await asyncio.sleep(0.25 * (attempt + 1))
        if last_error:
            raise last_error
        raise AppError("Marketplace optimization failed. Please try again.")

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
                workflow_name="marketplace_optimization",
                model_name=self._optimization_client.model_name,
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
