from datetime import UTC, datetime

import pytest

from app.core.errors import AppError
from app.features.ai_analysis.models import AiRequestLog, ProductAnalysisResult
from app.features.ai_analysis.openai_client import TokenUsage, VisionAnalysisResult
from app.features.ai_analysis.prompts import PromptLoader, PromptTemplate
from app.features.ai_analysis.repositories import AiAnalysisRepository
from app.features.ai_analysis.schemas import ProductAttributes
from app.features.ai_analysis.services import AiAnalysisService
from app.features.product_uploads.models import ProductImage
from app.shared.storage.provider import StorageProvider


class InMemoryAiAnalysisRepository(AiAnalysisRepository):
    def __init__(self, image: ProductImage | None) -> None:
        self.image = image
        self.saved_analysis: ProductAnalysisResult | None = None
        self.logs: list[AiRequestLog] = []

    async def get_image_for_user(self, image_id: str, user_id: str) -> ProductImage | None:
        del user_id
        if self.image and self.image.id == image_id:
            return self.image
        return None

    async def save_analysis_result(
        self,
        product_id: str,
        image_id: str,
        attributes: ProductAttributes,
    ) -> ProductAnalysisResult:
        self.saved_analysis = ProductAnalysisResult(
            id="analysis-1",
            product_id=product_id,
            image_id=image_id,
            valid_product=attributes.valid_product,
            confidence=attributes.confidence,
            reason=attributes.reason,
            category=attributes.category,
            product_type=attributes.product_type,
            color=attributes.color,
            material=attributes.material,
            style=attributes.style,
            visible_text_brand=attributes.visible_text_brand,
            target_audience=attributes.target_audience,
            raw_attributes=attributes.model_dump(),
            created_at=datetime.now(UTC),
        )
        return self.saved_analysis

    async def create_request_log(self, log: AiRequestLog) -> None:
        self.logs.append(log)


class InMemoryStorageProvider(StorageProvider):
    async def upload(self, file_name: str, content: bytes, content_type: str) -> str:
        del file_name, content, content_type
        return "http://testserver/uploads/front.jpg"

    async def read(self, file_name: str) -> bytes:
        del file_name
        return b"image-bytes"

    async def delete(self, file_name: str) -> None:
        del file_name


class FakeVisionClient:
    model_name = "fake-vision"

    def __init__(
        self,
        failures_before_success: int = 0,
        attributes: ProductAttributes | None = None,
    ) -> None:
        self.failures_before_success = failures_before_success
        self.attributes = attributes
        self.calls = 0

    async def analyze_product_image(
        self,
        image_content: bytes,
        content_type: str,
        prompt: str,
    ) -> VisionAnalysisResult:
        del image_content, content_type, prompt
        self.calls += 1
        if self.calls <= self.failures_before_success:
            raise RuntimeError("temporary OpenAI failure")
        return VisionAnalysisResult(
            attributes=self.attributes or build_valid_attributes(),
            token_usage=TokenUsage(input_tokens=10, output_tokens=20, total_tokens=30),
        )


class FakePromptLoader(PromptLoader):
    def __init__(self) -> None:
        pass

    def load_product_analysis_prompt(self) -> PromptTemplate:
        return PromptTemplate(content="Analyze the product image.", version="test-prompt-v1")


@pytest.mark.asyncio
async def test_analysis_service_saves_result_and_logs_success() -> None:
    repository = InMemoryAiAnalysisRepository(image=build_image())
    service = AiAnalysisService(
        repository=repository,
        storage_provider=InMemoryStorageProvider(),
        vision_client=FakeVisionClient(),
        prompt_loader=FakePromptLoader(),
        retry_attempts=3,
    )

    response = await service.analyze_uploaded_image(user_id="user-1", image_id="image-1")

    assert response.attributes.category == "Apparel"
    assert response.valid_product is True
    assert response.confidence == 0.92
    assert repository.saved_analysis is not None
    assert repository.logs[0].success is True
    assert repository.logs[0].model_name == "fake-vision"
    assert repository.logs[0].total_tokens == 30


@pytest.mark.asyncio
async def test_analysis_service_rejects_placeholder_image_response() -> None:
    repository = InMemoryAiAnalysisRepository(image=build_image())
    service = AiAnalysisService(
        repository=repository,
        storage_provider=InMemoryStorageProvider(),
        vision_client=FakeVisionClient(attributes=build_invalid_attributes("Placeholder image")),
        prompt_loader=FakePromptLoader(),
        retry_attempts=3,
    )

    with pytest.raises(AppError, match="No clear product was detected"):
        await service.analyze_uploaded_image(user_id="user-1", image_id="image-1")

    assert repository.saved_analysis is None
    assert repository.logs[0].status == "invalid_image"
    assert repository.logs[0].success is False
    assert "Placeholder image" in (repository.logs[0].error_message or "")


@pytest.mark.asyncio
async def test_analysis_service_rejects_blank_non_product_response() -> None:
    repository = InMemoryAiAnalysisRepository(image=build_image())
    service = AiAnalysisService(
        repository=repository,
        storage_provider=InMemoryStorageProvider(),
        vision_client=FakeVisionClient(attributes=build_invalid_attributes("Blank image")),
        prompt_loader=FakePromptLoader(),
        retry_attempts=3,
    )

    with pytest.raises(AppError, match="No clear product was detected"):
        await service.analyze_uploaded_image(user_id="user-1", image_id="image-1")

    assert repository.saved_analysis is None
    assert repository.logs[0].status == "invalid_image"


@pytest.mark.asyncio
async def test_analysis_service_rejects_low_confidence_product_response() -> None:
    repository = InMemoryAiAnalysisRepository(image=build_image())
    service = AiAnalysisService(
        repository=repository,
        storage_provider=InMemoryStorageProvider(),
        vision_client=FakeVisionClient(attributes=build_valid_attributes(confidence=0.42)),
        prompt_loader=FakePromptLoader(),
        retry_attempts=3,
    )

    with pytest.raises(AppError, match="No clear product was detected"):
        await service.analyze_uploaded_image(user_id="user-1", image_id="image-1")

    assert repository.saved_analysis is None
    assert repository.logs[0].status == "invalid_image"


@pytest.mark.asyncio
async def test_analysis_service_retries_openai_failures() -> None:
    vision_client = FakeVisionClient(failures_before_success=1)
    service = AiAnalysisService(
        repository=InMemoryAiAnalysisRepository(image=build_image()),
        storage_provider=InMemoryStorageProvider(),
        vision_client=vision_client,
        prompt_loader=FakePromptLoader(),
        retry_attempts=3,
    )

    response = await service.analyze_uploaded_image(user_id="user-1", image_id="image-1")

    assert response.attributes.product_type == "T-shirt"
    assert vision_client.calls == 2


@pytest.mark.asyncio
async def test_analysis_service_handles_missing_image() -> None:
    service = AiAnalysisService(
        repository=InMemoryAiAnalysisRepository(image=None),
        storage_provider=InMemoryStorageProvider(),
        vision_client=FakeVisionClient(),
        prompt_loader=FakePromptLoader(),
        retry_attempts=3,
    )

    with pytest.raises(AppError, match="Uploaded image was not found"):
        await service.analyze_uploaded_image(user_id="user-1", image_id="missing-image")


@pytest.mark.asyncio
async def test_analysis_service_logs_openai_failure() -> None:
    repository = InMemoryAiAnalysisRepository(image=build_image())
    service = AiAnalysisService(
        repository=repository,
        storage_provider=InMemoryStorageProvider(),
        vision_client=FakeVisionClient(failures_before_success=3),
        prompt_loader=FakePromptLoader(),
        retry_attempts=2,
    )

    with pytest.raises(AppError, match="Product analysis failed"):
        await service.analyze_uploaded_image(user_id="user-1", image_id="image-1")

    assert repository.logs[0].success is False
    assert repository.logs[0].error_message == "temporary OpenAI failure"


def build_image() -> ProductImage:
    return ProductImage(
        id="image-1",
        product_id="product-1",
        original_filename="front.jpg",
        storage_filename="front.jpg",
        image_url="http://testserver/uploads/front.jpg",
        content_type="image/jpeg",
        size_bytes=1024,
        created_at=datetime.now(UTC),
    )


def build_valid_attributes(confidence: float = 0.92) -> ProductAttributes:
    return ProductAttributes(
        valid_product=True,
        confidence=confidence,
        reason=None,
        category="Apparel",
        product_type="T-shirt",
        color="Black",
        material="Cotton",
        style="Minimal",
        visible_text_brand="unknown",
        target_audience="Adults",
    )


def build_invalid_attributes(reason: str) -> ProductAttributes:
    return ProductAttributes(
        valid_product=False,
        confidence=0.0,
        reason=reason,
    )
