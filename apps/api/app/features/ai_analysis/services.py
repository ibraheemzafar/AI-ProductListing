import asyncio
from time import perf_counter
from uuid import uuid4

from pydantic import ValidationError

from app.core.errors import AppError
from app.features.ai_analysis.models import AiRequestLog
from app.features.billing_meter.pricing import UsageInput
from app.features.billing_meter.service import RequestMeter
from app.features.ai_analysis.openai_client import (
    TokenUsage,
    VisionAnalysisClient,
    VisionAnalysisResult,
)
from app.features.ai_analysis.prompts import PromptLoader
from app.features.ai_analysis.repositories import AiAnalysisRepository
from app.features.ai_analysis.schemas import ProductAnalysisResponse
from app.shared.storage.provider import StorageProvider

ALLOWED_ANALYSIS_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}


class AiAnalysisService:
    def __init__(
        self,
        repository: AiAnalysisRepository,
        storage_provider: StorageProvider,
        vision_client: VisionAnalysisClient,
        prompt_loader: PromptLoader,
        retry_attempts: int,
        billing_meter: RequestMeter,
    ) -> None:
        self._repository = repository
        self._storage_provider = storage_provider
        self._vision_client = vision_client
        self._prompt_loader = prompt_loader
        self._retry_attempts = retry_attempts
        self._billing_meter = billing_meter

    async def list_existing_analyses(
        self,
        user_id: str,
        image_id: str,
    ) -> list[ProductAnalysisResponse]:
        if not image_id.strip():
            raise AppError("Image id is required")

        analyses = await self._repository.list_analyses_for_image(
            image_id=image_id,
            user_id=user_id,
        )
        return [ProductAnalysisResponse.from_model(analysis) for analysis in analyses]

    async def analyze_uploaded_image(
        self,
        user_id: str,
        image_id: str,
    ) -> ProductAnalysisResponse:
        if not image_id.strip():
            raise AppError("Image id is required")

        image = await self._repository.get_image_for_user(image_id=image_id, user_id=user_id)
        if image is None:
            raise AppError("Uploaded image was not found")
        if image.content_type not in ALLOWED_ANALYSIS_CONTENT_TYPES:
            raise AppError("Only JPG, PNG, and WEBP images can be analyzed")

        prompt = self._prompt_loader.load_product_analysis_prompt()
        image_content = await self._storage_provider.read(image.storage_filename)
        if not image_content:
            raise AppError("Uploaded image file is missing or empty")

        await self._billing_meter.authorize(user_id)

        started_at = perf_counter()
        token_usage = TokenUsage(input_tokens=None, output_tokens=None, total_tokens=None)
        try:
            analysis_result = await self._analyze_with_retries(
                image_content=image_content,
                content_type=image.content_type,
                prompt=prompt.content,
            )
            token_usage = analysis_result.token_usage
            saved_analysis = await self._repository.save_analysis_result(
                product_id=image.product_id,
                image_id=image.id,
                attributes=analysis_result.attributes,
            )
            request_log_id = str(uuid4())
            charge = await self._billing_meter.charge(
                user_id=user_id,
                workflow="product_analysis",
                usage=UsageInput(
                    input_tokens=token_usage.input_tokens,
                    output_tokens=token_usage.output_tokens,
                ),
                request_log_id=request_log_id,
            )
            await self._log_request(
                user_id=user_id,
                product_id=image.product_id,
                image_id=image.id,
                prompt_version=prompt.version,
                token_usage=token_usage,
                latency_ms=self._elapsed_ms(started_at),
                success=True,
                error_message=None,
                request_log_id=request_log_id,
                credits_charged=charge.credits_charged,
                wallet_transaction_id=charge.transaction_id,
            )
            return ProductAnalysisResponse.from_model(saved_analysis)
        except (ValidationError, ValueError) as error:
            await self._log_request(
                user_id=user_id,
                product_id=image.product_id,
                image_id=image.id,
                prompt_version=prompt.version,
                token_usage=token_usage,
                latency_ms=self._elapsed_ms(started_at),
                success=False,
                error_message=str(error),
            )
            raise AppError("AI returned an invalid product analysis. Please try again.") from error
        except Exception as error:
            await self._log_request(
                user_id=user_id,
                product_id=image.product_id,
                image_id=image.id,
                prompt_version=prompt.version,
                token_usage=token_usage,
                latency_ms=self._elapsed_ms(started_at),
                success=False,
                error_message=str(error),
            )
            raise AppError("Product analysis failed. Please try again.") from error

    async def _analyze_with_retries(
        self,
        image_content: bytes,
        content_type: str,
        prompt: str,
    ) -> VisionAnalysisResult:
        last_error: Exception | None = None
        for attempt in range(self._retry_attempts):
            try:
                return await self._vision_client.analyze_product_image(
                    image_content=image_content,
                    content_type=content_type,
                    prompt=prompt,
                )
            except Exception as error:
                last_error = error
                if attempt + 1 < self._retry_attempts:
                    await asyncio.sleep(0.25 * (attempt + 1))
        if last_error:
            raise last_error
        raise AppError("Product analysis failed. Please try again.")

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
                workflow_name="product_analysis",
                model_name=self._vision_client.model_name,
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
