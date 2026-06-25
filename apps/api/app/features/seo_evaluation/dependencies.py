from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.features.billing_meter.dependencies import get_token_billing_meter
from app.features.billing_meter.service import BillingMeter
from app.features.seo_evaluation.openai_client import OpenAISeoEvaluationClient
from app.features.seo_evaluation.prompts import SeoEvaluationPromptBuilder
from app.features.seo_evaluation.repositories import SQLAlchemySeoEvaluationRepository
from app.features.seo_evaluation.services import SeoEvaluationService
from app.infrastructure.database import get_database_session


def get_seo_evaluation_service(
    database_session: Annotated[AsyncSession, Depends(get_database_session)],
    settings: Annotated[Settings, Depends(get_settings)],
    billing_meter: Annotated[BillingMeter, Depends(get_token_billing_meter)],
) -> SeoEvaluationService:
    return SeoEvaluationService(
        repository=SQLAlchemySeoEvaluationRepository(database_session),
        seo_client=OpenAISeoEvaluationClient(
            api_key=settings.openai_api_key,
            model_name=settings.openai_text_model,
            timeout_seconds=settings.openai_timeout_seconds,
        ),
        prompt_builder=SeoEvaluationPromptBuilder(),
        retry_attempts=settings.ai_retry_attempts,
        billing_meter=billing_meter,
    )
