from datetime import UTC, datetime

import pytest

from app.core.errors import AppError
from app.features.ai_analysis.models import AiRequestLog
from app.features.image_enhancement.models import EnhancedImage
from app.features.image_enhancement.providers import (
    ImageEnhancementInput,
    ImageEnhancementOutput,
    ImageProvider,
)
from app.features.image_enhancement.repositories import ImageEnhancementRepository
from app.features.image_enhancement.schemas import ImageEnhancementOperation
from app.features.image_enhancement.services import ImageEnhancementService
from app.features.listing_generation.models import GeneratedListing
from app.features.product_uploads.models import ProductImage
from app.shared.storage.provider import StorageProvider


class InMemoryImageEnhancementRepository(ImageEnhancementRepository):
    def __init__(
        self,
        listing: GeneratedListing | None,
        image: ProductImage | None,
    ) -> None:
        self.listing = listing
        self.image = image
        self.enhanced_images: list[EnhancedImage] = []
        self.logs: list[AiRequestLog] = []

    async def get_listing_image_for_user(
        self,
        listing_id: str,
        user_id: str,
    ) -> tuple[GeneratedListing, ProductImage] | None:
        del user_id
        if self.listing and self.image and self.listing.id == listing_id:
            return self.listing, self.image
        return None

    async def save_enhanced_image(self, image: EnhancedImage) -> EnhancedImage:
        image.id = f"enhanced-{len(self.enhanced_images) + 1}"
        image.created_at = datetime.now(UTC)
        self.enhanced_images.append(image)
        return image

    async def create_request_log(self, log: AiRequestLog) -> None:
        self.logs.append(log)


class FakeImageProvider(ImageProvider):
    provider_name = "fake-provider"

    def __init__(self, failures_before_success: int = 0) -> None:
        self.failures_before_success = failures_before_success
        self.calls = 0
        self.inputs: list[ImageEnhancementInput] = []

    async def enhance_image(self, image: ImageEnhancementInput) -> ImageEnhancementOutput:
        self.calls += 1
        self.inputs.append(image)
        if self.calls <= self.failures_before_success:
            raise RuntimeError("temporary provider failure")
        return ImageEnhancementOutput(
            content=b"enhanced-png",
            content_type="image/png",
            file_extension=".png",
        )


class InMemoryStorageProvider(StorageProvider):
    def __init__(self) -> None:
        self.files: dict[str, bytes] = {"original.png": b"original-png"}

    async def upload(self, file_name: str, content: bytes, content_type: str) -> str:
        del content_type
        self.files[file_name] = content
        return f"http://testserver/uploads/{file_name}"

    async def read(self, file_name: str) -> bytes:
        return self.files[file_name]

    async def delete(self, file_name: str) -> None:
        self.files.pop(file_name, None)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "operation",
    ["background_removal", "image_cleanup", "image_optimization"],
)
async def test_image_enhancement_service_saves_enhanced_image(
    operation: ImageEnhancementOperation,
) -> None:
    repository = InMemoryImageEnhancementRepository(
        listing=build_listing(),
        image=build_product_image(),
    )
    provider = FakeImageProvider()
    service = build_service(repository, provider)

    response = await service.enhance_listing_image(
        user_id="user-1",
        listing_id="listing-1",
        operation=operation,
    )

    assert response.operation == operation
    assert response.enhanced_image_url.startswith("http://testserver/uploads/")
    assert repository.enhanced_images[0].provider_name == "fake-provider"
    assert repository.logs[0].workflow_name == "image_enhancement"
    assert repository.logs[0].image_id == "image-1"
    assert provider.inputs[0].image_url == "http://testserver/uploads/original.png"
    assert provider.inputs[0].image_content == b"original-png"
    assert provider.inputs[0].image_content_type == "image/png"
    assert provider.inputs[0].image_filename == "original.png"


@pytest.mark.asyncio
async def test_image_enhancement_service_requires_owned_listing_image() -> None:
    service = build_service(InMemoryImageEnhancementRepository(listing=None, image=None))

    with pytest.raises(AppError, match="Generated listing image was not found"):
        await service.enhance_listing_image(
            user_id="user-1",
            listing_id="listing-1",
            operation="background_removal",
        )


@pytest.mark.asyncio
async def test_image_enhancement_service_retries_and_logs_failure() -> None:
    repository = InMemoryImageEnhancementRepository(
        listing=build_listing(),
        image=build_product_image(),
    )
    provider = FakeImageProvider(failures_before_success=3)
    service = build_service(repository, provider, attempts=2)

    with pytest.raises(AppError, match="Image enhancement failed"):
        await service.enhance_listing_image(
            user_id="user-1",
            listing_id="listing-1",
            operation="background_removal",
        )

    assert provider.calls == 2
    assert repository.logs[0].success is False
    assert repository.logs[0].error_message == "temporary provider failure"


def build_service(
    repository: InMemoryImageEnhancementRepository,
    provider: FakeImageProvider | None = None,
    attempts: int = 3,
) -> ImageEnhancementService:
    return ImageEnhancementService(
        repository=repository,
        image_provider=provider or FakeImageProvider(),
        storage_provider=InMemoryStorageProvider(),
        retry_attempts=attempts,
    )


def build_listing() -> GeneratedListing:
    return GeneratedListing(
        id="listing-1",
        product_id="product-1",
        analysis_id="analysis-1",
        title="Minimal Black Cotton T-Shirt",
        short_description="A soft black cotton T-shirt.",
        long_description="A simple black cotton T-shirt.",
        seo_keywords=["black cotton t-shirt"],
        product_tags=["t-shirt"],
        raw_output={},
        created_at=datetime.now(UTC),
    )


def build_product_image() -> ProductImage:
    return ProductImage(
        id="image-1",
        product_id="product-1",
        original_filename="original.png",
        storage_filename="original.png",
        image_url="http://testserver/uploads/original.png",
        content_type="image/png",
        size_bytes=12,
        created_at=datetime.now(UTC),
    )
