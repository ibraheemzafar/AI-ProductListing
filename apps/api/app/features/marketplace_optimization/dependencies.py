from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.features.billing_meter.dependencies import get_token_billing_meter
from app.features.billing_meter.service import BillingMeter
from app.features.marketplace_optimization.openai_client import (
    OpenAIMarketplaceOptimizationClient,
)
from app.features.marketplace_optimization.prompts import MarketplaceOptimizationPromptBuilder
from app.features.marketplace_optimization.repositories import (
    SQLAlchemyMarketplaceOptimizationRepository,
)
from app.features.marketplace_optimization.services import MarketplaceOptimizationService
from app.infrastructure.database import get_database_session


def get_marketplace_optimization_service(
    database_session: Annotated[AsyncSession, Depends(get_database_session)],
    settings: Annotated[Settings, Depends(get_settings)],
    billing_meter: Annotated[BillingMeter, Depends(get_token_billing_meter)],
) -> MarketplaceOptimizationService:
    return MarketplaceOptimizationService(
        repository=SQLAlchemyMarketplaceOptimizationRepository(database_session),
        optimization_client=OpenAIMarketplaceOptimizationClient(
            api_key=settings.openai_api_key,
            model_name=settings.openai_text_model,
            timeout_seconds=settings.openai_timeout_seconds,
        ),
        prompt_builder=MarketplaceOptimizationPromptBuilder(),
        retry_attempts=settings.ai_retry_attempts,
        billing_meter=billing_meter,
    )
