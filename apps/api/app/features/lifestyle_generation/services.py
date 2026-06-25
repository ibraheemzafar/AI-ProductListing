import asyncio
from time import perf_counter
from uuid import uuid4

from app.core.errors import AppError, NotFoundError
from app.features.ai_analysis.models import AiRequestLog
from app.features.ai_analysis.openai_client import TokenUsage
from app.features.billing_meter.pricing import UsageInput
from app.features.billing_meter.service import RequestMeter
from app.features.lifestyle_generation.models import GeneratedImage
from app.features.lifestyle_generation.prompts import LifestyleScenePromptBuilder
from app.features.lifestyle_generation.providers import (
    ImageGenerationInput,
    ImageGenerationOutput,
    ImageGenerationProvider,
)
from app.features.lifestyle_generation.repositories import (
    LifestyleGenerationRepository,
    LifestyleGenerationSource,
)
from app.features.lifestyle_generation.schemas import (
    GeneratedImageGalleryResponse,
    GeneratedImageResponse,
    ImageGenerationCategory,
)
from app.shared.storage.provider import StorageProvider


class LifestyleGenerationService:
    def __init__(
        self,
        repository: LifestyleGenerationRepository,
        generation_provider: ImageGenerationProvider,
        storage_provider: StorageProvider,
        prompt_builder: LifestyleScenePromptBuilder,
        retry_attempts: int,
        billing_meter: RequestMeter,
    ) -> None:
        self._repository = repository
        self._generation_provider = generation_provider
        self._storage_provider = storage_provider
        self._prompt_builder = prompt_builder
        self._retry_attempts = retry_attempts
        self._billing_meter = billing_meter

    async def generate_lifestyle_scene(
        self,
        user_id: str,
        listing_id: str,
        category: ImageGenerationCategory,
        custom_prompt: str | None,
    ) -> GeneratedImageResponse:
        if not listing_id.strip():
            raise AppError("Listing id is required")

        source = await self._repository.get_generation_source_for_user(
            listing_id=listing_id,
            user_id=user_id,
        )
        if source is None:
            raise NotFoundError("Generated listing image was not found")

        await self._billing_meter.authorize(user_id)

        prompt = self._prompt_builder.build_prompt(
            category=category,
            custom_prompt=custom_prompt,
        )
        started_at = perf_counter()
        token_usage = TokenUsage(input_tokens=None, output_tokens=None, total_tokens=None)
        try:
            source_bytes = await self._storage_provider.read(self._source_storage_filename(source))
            generated_output = await self._generate_with_retries(
                ImageGenerationInput(
                    prompt=prompt.content,
                    source_image=source_bytes,
                    source_content_type=self._source_content_type(source),
                    source_filename=self._source_storage_filename(source),
                ),
            )
            generation_time_ms = self._elapsed_ms(started_at)
            storage_filename = f"{uuid4()}{generated_output.file_extension}"
            generated_url = await self._storage_provider.upload(
                file_name=storage_filename,
                content=generated_output.content,
                content_type=generated_output.content_type,
            )
            saved_image = await self._repository.save_generated_image(
                GeneratedImage(
                    user_id=user_id,
                    product_id=source.listing.product_id,
                    listing_id=source.listing.id,
                    source_product_image_id=source.product_image.id,
                    source_enhanced_image_id=(
                        source.enhanced_image.id if source.enhanced_image else None
                    ),
                    category=category,
                    custom_prompt=custom_prompt.strip() if custom_prompt else None,
                    prompt=prompt.content,
                    provider=self._generation_provider.provider_name,
                    storage_filename=storage_filename,
                    generated_image_url=generated_url,
                    content_type=generated_output.content_type,
                    size_bytes=len(generated_output.content),
                    generation_time_ms=generation_time_ms,
                    status="success",
                ),
            )
            request_log_id = str(uuid4())
            charge = await self._billing_meter.charge(
                user_id=user_id,
                workflow="lifestyle_scene_generation",
                usage=UsageInput(),
                request_log_id=request_log_id,
            )
            await self._log_request(
                user_id=user_id,
                product_id=source.listing.product_id,
                image_id=source.product_image.id,
                prompt_version=prompt.version,
                token_usage=token_usage,
                latency_ms=generation_time_ms,
                success=True,
                error_message=None,
                request_log_id=request_log_id,
                credits_charged=charge.credits_charged,
                wallet_transaction_id=charge.transaction_id,
            )
            return GeneratedImageResponse.from_model(saved_image)
        except Exception as error:
            await self._log_request(
                user_id=user_id,
                product_id=source.listing.product_id,
                image_id=source.product_image.id,
                prompt_version=prompt.version,
                token_usage=token_usage,
                latency_ms=self._elapsed_ms(started_at),
                success=False,
                error_message=str(error),
            )
            if isinstance(error, AppError):
                raise
            raise AppError("Lifestyle scene generation failed. Please try again.") from error

    async def list_generated_images(
        self,
        user_id: str,
        listing_id: str,
    ) -> GeneratedImageGalleryResponse:
        if not listing_id.strip():
            raise AppError("Listing id is required")

        images = await self._repository.list_generated_images_for_user(
            listing_id=listing_id,
            user_id=user_id,
        )
        if images is None:
            raise NotFoundError("Generated listing was not found")

        return GeneratedImageGalleryResponse(
            images=[GeneratedImageResponse.from_model(image) for image in images],
        )

    async def download_generated_image(
        self,
        user_id: str,
        listing_id: str,
        image_id: str,
    ) -> tuple[bytes, str, str]:
        image = await self._repository.get_generated_image_for_user(
            listing_id=listing_id,
            image_id=image_id,
            user_id=user_id,
        )
        if image is None:
            raise NotFoundError("Generated image was not found")

        content = await self._storage_provider.read(image.storage_filename)
        return content, image.content_type, self._download_filename(image)

    async def delete_generated_image(
        self,
        user_id: str,
        listing_id: str,
        image_id: str,
    ) -> None:
        image = await self._repository.get_generated_image_for_user(
            listing_id=listing_id,
            image_id=image_id,
            user_id=user_id,
        )
        if image is None:
            raise NotFoundError("Generated image was not found")

        try:
            await self._storage_provider.delete(image.storage_filename)
        finally:
            await self._repository.delete_generated_image(image)

    async def _generate_with_retries(
        self,
        image: ImageGenerationInput,
    ) -> ImageGenerationOutput:
        last_error: Exception | None = None
        for attempt in range(self._retry_attempts):
            try:
                return await self._generation_provider.generate_scene(image)
            except Exception as error:
                last_error = error
                if attempt + 1 < self._retry_attempts:
                    await asyncio.sleep(0.25 * (attempt + 1))
        if last_error:
            raise last_error
        raise AppError("Lifestyle scene generation failed. Please try again.")

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
                workflow_name="lifestyle_scene_generation",
                model_name=(
                    f"{self._generation_provider.provider_name}:"
                    f"{self._generation_provider.model_name}"
                ),
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

    def _source_storage_filename(self, source: LifestyleGenerationSource) -> str:
        if source.enhanced_image is not None:
            return source.enhanced_image.storage_filename
        return source.product_image.storage_filename

    def _source_content_type(self, source: LifestyleGenerationSource) -> str:
        if source.enhanced_image is not None:
            return source.enhanced_image.content_type
        return source.product_image.content_type

    def _elapsed_ms(self, started_at: float) -> int:
        return round((perf_counter() - started_at) * 1000)

    def _download_filename(self, image: GeneratedImage) -> str:
        extension = image.storage_filename.rsplit(".", 1)[-1]
        return f"{image.listing_id}-{image.category}.{extension}"
