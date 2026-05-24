from datetime import UTC, datetime

import pytest

from app.core.errors import AppError
from app.features.ai_analysis.models import AiRequestLog
from app.features.image_enhancement.models import EnhancedImage
from app.features.lifestyle_generation.models import GeneratedImage
from app.features.lifestyle_generation.prompts import LifestyleScenePromptBuilder, PromptTemplate
from app.features.lifestyle_generation.providers import (
    ImageGenerationInput,
    ImageGenerationOutput,
    ImageGenerationProvider,
)
from app.features.lifestyle_generation.repositories import (
    LifestyleGenerationRepository,
    LifestyleGenerationSource,
)
from app.features.lifestyle_generation.schemas import ScenePreset
from app.features.lifestyle_generation.services import LifestyleGenerationService
from app.features.listing_generation.models import GeneratedListing
from app.features.product_uploads.models import ProductImage
from app.shared.storage.provider import StorageProvider


class InMemoryLifestyleGenerationRepository(LifestyleGenerationRepository):
    def __init__(self, source: LifestyleGenerationSource | None) -> None:
        self.source = source
        self.generated_images: list[GeneratedImage] = []
        self.logs: list[AiRequestLog] = []

    async def get_generation_source_for_user(
        self,
        listing_id: str,
        user_id: str,
    ) -> LifestyleGenerationSource | None:
        del user_id
        if self.source and self.source.listing.id == listing_id:
            return self.source
        return None

    async def save_generated_image(self, image: GeneratedImage) -> GeneratedImage:
        image.id = f"generated-{len(self.generated_images) + 1}"
        image.created_at = datetime.now(UTC)
        self.generated_images.append(image)
        return image

    async def list_generated_images_for_user(
        self,
        listing_id: str,
        user_id: str,
    ) -> list[GeneratedImage] | None:
        if self.source is None or self.source.listing.id != listing_id:
            return None
        return [image for image in self.generated_images if image.user_id == user_id]

    async def get_generated_image_for_user(
        self,
        listing_id: str,
        image_id: str,
        user_id: str,
    ) -> GeneratedImage | None:
        for image in self.generated_images:
            if image.id == image_id and image.listing_id == listing_id and image.user_id == user_id:
                return image
        return None

    async def delete_generated_image(self, image: GeneratedImage) -> None:
        self.generated_images = [saved for saved in self.generated_images if saved.id != image.id]

    async def create_request_log(self, log: AiRequestLog) -> None:
        self.logs.append(log)


class FakeImageGenerationProvider(ImageGenerationProvider):
    provider_name = "fake-images"
    model_name = "fake-image-model"

    def __init__(self, failures_before_success: int = 0) -> None:
        self.failures_before_success = failures_before_success
        self.calls = 0
        self.inputs: list[ImageGenerationInput] = []

    async def generate_scene(self, image: ImageGenerationInput) -> ImageGenerationOutput:
        self.calls += 1
        self.inputs.append(image)
        if self.calls <= self.failures_before_success:
            raise RuntimeError("temporary image generation failure")
        return ImageGenerationOutput(
            content=b"generated-png",
            content_type="image/png",
            file_extension=".png",
        )


class FakeAppErrorImageGenerationProvider(FakeImageGenerationProvider):
    async def generate_scene(self, image: ImageGenerationInput) -> ImageGenerationOutput:
        del image
        raise AppError("OpenAI image generation failed: unsupported image format")


class FakePromptBuilder(LifestyleScenePromptBuilder):
    def __init__(self) -> None:
        pass

    def build_prompt(
        self,
        category: ScenePreset,
        custom_prompt: str | None,
    ) -> PromptTemplate:
        return PromptTemplate(
            content=f"Generate {category} with {custom_prompt or 'default direction'}",
            version="test-lifestyle-v1",
        )


class InMemoryStorageProvider(StorageProvider):
    def __init__(self) -> None:
        self.files: dict[str, bytes] = {
            "original.png": b"original-png",
            "enhanced.png": b"enhanced-png",
        }

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
    "scene_preset",
    [
        "luxury_product_shot",
        "wooden_table_setup",
        "studio_white_background",
        "minimal_ecommerce_background",
        "lifestyle_home_setup",
        "social_media_banner",
        "marketplace_hero_image",
        "custom_prompt",
    ],
)
async def test_lifestyle_generation_service_saves_generated_scene(
    scene_preset: ScenePreset,
) -> None:
    repository = InMemoryLifestyleGenerationRepository(source=build_source())
    provider = FakeImageGenerationProvider()
    service = build_service(repository, provider)

    response = await service.generate_lifestyle_scene(
        user_id="user-1",
        listing_id="listing-1",
        category=scene_preset,
        custom_prompt="Warm afternoon light",
    )

    assert response.category == scene_preset
    assert response.generated_image_url.startswith("http://testserver/uploads/")
    assert repository.generated_images[0].source_enhanced_image_id == "enhanced-1"
    assert repository.generated_images[0].prompt.startswith("Generate")
    assert repository.logs[0].workflow_name == "lifestyle_scene_generation"
    assert repository.logs[0].model_name == "fake-images:fake-image-model"
    assert provider.inputs[0].source_image == b"enhanced-png"


@pytest.mark.asyncio
async def test_lifestyle_generation_service_lists_generated_scenes() -> None:
    repository = InMemoryLifestyleGenerationRepository(source=build_source(include_enhanced=False))
    service = build_service(repository)
    await service.generate_lifestyle_scene(
        user_id="user-1",
        listing_id="listing-1",
        category="studio_white_background",
        custom_prompt=None,
    )

    response = await service.list_generated_images(user_id="user-1", listing_id="listing-1")

    assert len(response.images) == 1
    assert response.images[0].source_enhanced_image_id is None


@pytest.mark.asyncio
async def test_lifestyle_generation_service_requires_owned_listing_image() -> None:
    service = build_service(InMemoryLifestyleGenerationRepository(source=None))

    with pytest.raises(AppError, match="Generated listing image was not found"):
        await service.generate_lifestyle_scene(
            user_id="user-1",
            listing_id="listing-1",
            category="luxury_product_shot",
            custom_prompt=None,
        )


@pytest.mark.asyncio
async def test_lifestyle_generation_service_retries_and_logs_failure() -> None:
    repository = InMemoryLifestyleGenerationRepository(source=build_source())
    provider = FakeImageGenerationProvider(failures_before_success=3)
    service = build_service(repository, provider, attempts=2)

    with pytest.raises(AppError, match="Lifestyle scene generation failed"):
        await service.generate_lifestyle_scene(
            user_id="user-1",
            listing_id="listing-1",
            category="lifestyle_home_setup",
            custom_prompt=None,
        )

    assert provider.calls == 2
    assert repository.logs[0].success is False
    assert repository.logs[0].error_message == "temporary image generation failure"


@pytest.mark.asyncio
async def test_lifestyle_generation_service_preserves_provider_app_error() -> None:
    repository = InMemoryLifestyleGenerationRepository(source=build_source())
    service = build_service(
        repository,
        provider=FakeAppErrorImageGenerationProvider(),
        attempts=1,
    )

    with pytest.raises(AppError, match="unsupported image format"):
        await service.generate_lifestyle_scene(
            user_id="user-1",
            listing_id="listing-1",
            category="studio_white_background",
            custom_prompt=None,
        )

    assert repository.logs[0].error_message == (
        "OpenAI image generation failed: unsupported image format"
    )


@pytest.mark.asyncio
async def test_lifestyle_generation_service_downloads_owned_generated_image() -> None:
    repository = InMemoryLifestyleGenerationRepository(source=build_source())
    storage_provider = InMemoryStorageProvider()
    service = build_service(repository, storage_provider=storage_provider)
    await service.generate_lifestyle_scene(
        user_id="user-1",
        listing_id="listing-1",
        category="marketplace_hero_image",
        custom_prompt=None,
    )

    content, content_type, filename = await service.download_generated_image(
        user_id="user-1",
        listing_id="listing-1",
        image_id="generated-1",
    )

    assert content == b"generated-png"
    assert content_type == "image/png"
    assert filename == "listing-1-marketplace_hero_image.png"


@pytest.mark.asyncio
async def test_lifestyle_generation_service_deletes_owned_generated_image() -> None:
    repository = InMemoryLifestyleGenerationRepository(source=build_source())
    storage_provider = InMemoryStorageProvider()
    service = build_service(repository, storage_provider=storage_provider)
    await service.generate_lifestyle_scene(
        user_id="user-1",
        listing_id="listing-1",
        category="marketplace_hero_image",
        custom_prompt=None,
    )
    storage_filename = repository.generated_images[0].storage_filename

    await service.delete_generated_image(
        user_id="user-1",
        listing_id="listing-1",
        image_id="generated-1",
    )

    assert repository.generated_images == []
    assert storage_filename not in storage_provider.files


@pytest.mark.asyncio
async def test_lifestyle_generation_service_blocks_unauthorized_generated_image_access() -> None:
    repository = InMemoryLifestyleGenerationRepository(source=build_source())
    service = build_service(repository)
    await service.generate_lifestyle_scene(
        user_id="user-1",
        listing_id="listing-1",
        category="marketplace_hero_image",
        custom_prompt=None,
    )

    with pytest.raises(AppError, match="Generated image was not found"):
        await service.download_generated_image(
            user_id="user-2",
            listing_id="listing-1",
            image_id="generated-1",
        )


def build_service(
    repository: InMemoryLifestyleGenerationRepository,
    provider: FakeImageGenerationProvider | None = None,
    storage_provider: InMemoryStorageProvider | None = None,
    attempts: int = 3,
) -> LifestyleGenerationService:
    return LifestyleGenerationService(
        repository=repository,
        generation_provider=provider or FakeImageGenerationProvider(),
        storage_provider=storage_provider or InMemoryStorageProvider(),
        prompt_builder=FakePromptBuilder(),
        retry_attempts=attempts,
    )


def build_source(include_enhanced: bool = True) -> LifestyleGenerationSource:
    return LifestyleGenerationSource(
        listing=build_listing(),
        product_image=build_product_image(),
        enhanced_image=build_enhanced_image() if include_enhanced else None,
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


def build_enhanced_image() -> EnhancedImage:
    return EnhancedImage(
        id="enhanced-1",
        product_id="product-1",
        original_image_id="image-1",
        operation="background_removal",
        provider_name="fake-provider",
        storage_filename="enhanced.png",
        enhanced_image_url="http://testserver/uploads/enhanced.png",
        content_type="image/png",
        size_bytes=12,
        created_at=datetime.now(UTC),
    )
