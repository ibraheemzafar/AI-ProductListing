import asyncio
from time import perf_counter
from uuid import uuid4

from app.core.errors import AppError, NotFoundError
from app.features.ai_analysis.models import AiRequestLog
from app.features.ai_analysis.openai_client import TokenUsage
from app.features.billing_meter.pricing import UsageInput
from app.features.billing_meter.service import RequestMeter
from app.features.image_enhancement.models import EnhancedImage
from app.features.image_enhancement.providers import (
    ImageEnhancementInput,
    ImageEnhancementOutput,
    ImageProvider,
)
from app.features.image_enhancement.repositories import ImageEnhancementRepository
from app.features.image_enhancement.schemas import (
    EnhancedImageResponse,
    ImageEnhancementOperation,
)
from app.shared.storage.provider import StorageProvider


class ImageEnhancementService:
    def __init__(
        self,
        repository: ImageEnhancementRepository,
        image_provider: ImageProvider,
        storage_provider: StorageProvider,
        retry_attempts: int,
        billing_meter: RequestMeter,
    ) -> None:
        self._repository = repository
        self._image_provider = image_provider
        self._storage_provider = storage_provider
        self._retry_attempts = retry_attempts
        self._billing_meter = billing_meter

    async def enhance_listing_image(
        self,
        user_id: str,
        listing_id: str,
        operation: ImageEnhancementOperation,
    ) -> EnhancedImageResponse:
        if not listing_id.strip():
            raise AppError("Listing id is required")

        source = await self._repository.get_listing_image_for_user(
            listing_id=listing_id,
            user_id=user_id,
        )
        if source is None:
            raise NotFoundError("Generated listing image was not found")

        listing, image = source

        await self._billing_meter.authorize(user_id)

        started_at = perf_counter()
        token_usage = TokenUsage(input_tokens=None, output_tokens=None, total_tokens=None)
        try:
            image_content = await self._storage_provider.read(image.storage_filename)
            enhanced = await self._enhance_with_retries(
                ImageEnhancementInput(
                    image_url=image.image_url,
                    image_content=image_content,
                    image_content_type=image.content_type,
                    image_filename=image.storage_filename,
                    operation=operation,
                ),
            )
            storage_filename = f"{uuid4()}{enhanced.file_extension}"
            enhanced_url = await self._storage_provider.upload(
                file_name=storage_filename,
                content=enhanced.content,
                content_type=enhanced.content_type,
            )
            saved_image = await self._repository.save_enhanced_image(
                EnhancedImage(
                    product_id=listing.product_id,
                    original_image_id=image.id,
                    operation=operation,
                    provider_name=self._image_provider.provider_name,
                    storage_filename=storage_filename,
                    enhanced_image_url=enhanced_url,
                    content_type=enhanced.content_type,
                    size_bytes=len(enhanced.content),
                ),
            )
            request_log_id = str(uuid4())
            charge = await self._billing_meter.charge(
                user_id=user_id,
                workflow="image_enhancement",
                usage=UsageInput(),
                request_log_id=request_log_id,
            )
            await self._log_request(
                user_id=user_id,
                product_id=listing.product_id,
                image_id=image.id,
                token_usage=token_usage,
                latency_ms=self._elapsed_ms(started_at),
                success=True,
                error_message=None,
                request_log_id=request_log_id,
                credits_charged=charge.credits_charged,
                wallet_transaction_id=charge.transaction_id,
            )
            return EnhancedImageResponse.from_model(saved_image)
        except Exception as error:
            await self._log_request(
                user_id=user_id,
                product_id=listing.product_id,
                image_id=image.id,
                token_usage=token_usage,
                latency_ms=self._elapsed_ms(started_at),
                success=False,
                error_message=str(error),
            )
            if isinstance(error, AppError):
                raise
            raise AppError("Image enhancement failed. Please try again.") from error

    async def _enhance_with_retries(
        self,
        image: ImageEnhancementInput,
    ) -> ImageEnhancementOutput:
        last_error: Exception | None = None
        for attempt in range(self._retry_attempts):
            try:
                return await self._image_provider.enhance_image(image)
            except Exception as error:
                last_error = error
                if attempt + 1 < self._retry_attempts:
                    await asyncio.sleep(0.25 * (attempt + 1))
        if last_error:
            raise last_error
        raise AppError("Image enhancement failed. Please try again.")

    async def _log_request(
        self,
        user_id: str,
        product_id: str,
        image_id: str,
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
                image_id=image_id,
                workflow_name="image_enhancement",
                model_name=self._image_provider.provider_name,
                prompt_version="image-provider-v1",
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
