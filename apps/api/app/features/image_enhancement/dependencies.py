from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.features.image_enhancement.openai_provider import OpenAIImageEnhancementProvider
from app.features.image_enhancement.repositories import SQLAlchemyImageEnhancementRepository
from app.features.image_enhancement.services import ImageEnhancementService
from app.infrastructure.database import get_database_session
from app.shared.storage.dependencies import get_storage_provider
from app.shared.storage.provider import StorageProvider


def get_image_enhancement_service(
    database_session: Annotated[AsyncSession, Depends(get_database_session)],
    storage_provider: Annotated[StorageProvider, Depends(get_storage_provider)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> ImageEnhancementService:
    return ImageEnhancementService(
        repository=SQLAlchemyImageEnhancementRepository(database_session),
        image_provider=OpenAIImageEnhancementProvider(
            api_key=settings.openai_api_key,
            model_name=settings.openai_image_model,
            timeout_seconds=settings.openai_image_timeout_seconds,
        ),
        storage_provider=storage_provider,
        retry_attempts=settings.ai_retry_attempts,
    )
