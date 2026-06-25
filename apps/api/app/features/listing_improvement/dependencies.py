from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.features.billing_meter.dependencies import get_token_billing_meter
from app.features.billing_meter.service import BillingMeter
from app.features.listing_improvement.openai_client import OpenAIListingImprovementClient
from app.features.listing_improvement.prompts import ListingImprovementPromptBuilder
from app.features.listing_improvement.repositories import SQLAlchemyListingImprovementRepository
from app.features.listing_improvement.services import ListingImprovementService
from app.infrastructure.database import get_database_session


def get_listing_improvement_service(
    database_session: Annotated[AsyncSession, Depends(get_database_session)],
    settings: Annotated[Settings, Depends(get_settings)],
    billing_meter: Annotated[BillingMeter, Depends(get_token_billing_meter)],
) -> ListingImprovementService:
    return ListingImprovementService(
        repository=SQLAlchemyListingImprovementRepository(database_session),
        improvement_client=OpenAIListingImprovementClient(
            api_key=settings.openai_api_key,
            model_name=settings.openai_text_model,
            timeout_seconds=settings.openai_timeout_seconds,
        ),
        prompt_builder=ListingImprovementPromptBuilder(),
        retry_attempts=settings.ai_retry_attempts,
        billing_meter=billing_meter,
    )
