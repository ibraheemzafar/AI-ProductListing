from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.features.ai_analysis.openai_client import OpenAIVisionAnalysisClient
from app.features.ai_analysis.prompts import PromptLoader
from app.features.ai_analysis.repositories import SQLAlchemyAiAnalysisRepository
from app.features.ai_analysis.services import AiAnalysisService
from app.features.billing_meter.dependencies import get_token_billing_meter
from app.features.billing_meter.service import BillingMeter
from app.infrastructure.database import get_database_session
from app.shared.storage.dependencies import get_storage_provider
from app.shared.storage.provider import StorageProvider


def get_ai_analysis_service(
    database_session: Annotated[AsyncSession, Depends(get_database_session)],
    storage_provider: Annotated[StorageProvider, Depends(get_storage_provider)],
    settings: Annotated[Settings, Depends(get_settings)],
    billing_meter: Annotated[BillingMeter, Depends(get_token_billing_meter)],
) -> AiAnalysisService:
    return AiAnalysisService(
        repository=SQLAlchemyAiAnalysisRepository(database_session),
        storage_provider=storage_provider,
        vision_client=OpenAIVisionAnalysisClient(
            api_key=settings.openai_api_key,
            model_name=settings.openai_vision_model,
            timeout_seconds=settings.openai_timeout_seconds,
        ),
        prompt_loader=PromptLoader(),
        retry_attempts=settings.ai_retry_attempts,
        billing_meter=billing_meter,
    )
