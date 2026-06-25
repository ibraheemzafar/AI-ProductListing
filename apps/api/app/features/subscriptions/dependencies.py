from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.subscriptions.repositories import SQLAlchemySubscriptionRepository
from app.features.subscriptions.services import SubscriptionService
from app.infrastructure.database import get_database_session


def get_subscription_service(
    database_session: Annotated[AsyncSession, Depends(get_database_session)],
) -> SubscriptionService:
    return SubscriptionService(repository=SQLAlchemySubscriptionRepository(database_session))
