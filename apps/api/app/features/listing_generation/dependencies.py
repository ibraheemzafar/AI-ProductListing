from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.features.listing_generation.openai_client import OpenAIListingGenerationClient
from app.features.listing_generation.prompts import ListingPromptBuilder
from app.features.listing_generation.repositories import SQLAlchemyListingGenerationRepository
from app.features.listing_generation.services import ListingGenerationService
from app.infrastructure.database import get_database_session


def get_listing_generation_service(
    database_session: Annotated[AsyncSession, Depends(get_database_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> ListingGenerationService:
    return ListingGenerationService(
        repository=SQLAlchemyListingGenerationRepository(database_session),
        listing_client=OpenAIListingGenerationClient(
            api_key=settings.openai_api_key,
            model_name=settings.openai_text_model,
            timeout_seconds=settings.openai_timeout_seconds,
        ),
        prompt_builder=ListingPromptBuilder(),
        retry_attempts=settings.ai_retry_attempts,
    )
