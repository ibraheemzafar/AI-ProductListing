from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.features.billing_meter.dependencies import get_flat_billing_meter
from app.features.billing_meter.service import BillingMeter
from app.features.lifestyle_generation.openai_provider import OpenAIImageGenerationProvider
from app.features.lifestyle_generation.prompts import LifestyleScenePromptBuilder
from app.features.lifestyle_generation.repositories import SQLAlchemyLifestyleGenerationRepository
from app.features.lifestyle_generation.services import LifestyleGenerationService
from app.infrastructure.database import get_database_session
from app.shared.storage.dependencies import get_storage_provider
from app.shared.storage.provider import StorageProvider


def get_lifestyle_generation_service(
    database_session: Annotated[AsyncSession, Depends(get_database_session)],
    storage_provider: Annotated[StorageProvider, Depends(get_storage_provider)],
    settings: Annotated[Settings, Depends(get_settings)],
    billing_meter: Annotated[BillingMeter, Depends(get_flat_billing_meter)],
) -> LifestyleGenerationService:
    return LifestyleGenerationService(
        repository=SQLAlchemyLifestyleGenerationRepository(database_session),
        generation_provider=OpenAIImageGenerationProvider(
            api_key=settings.openai_api_key,
            model_name=settings.openai_image_model,
            timeout_seconds=settings.openai_image_timeout_seconds,
        ),
        storage_provider=storage_provider,
        prompt_builder=LifestyleScenePromptBuilder(),
        retry_attempts=settings.ai_retry_attempts,
        billing_meter=billing_meter,
    )
