from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.features.payments.repositories import SQLAlchemyPaymentsRepository
from app.features.payments.services import PaymentService
from app.features.payments.webhook_service import WebhookService
from app.features.subscriptions.dependencies import get_subscription_service
from app.features.subscriptions.services import SubscriptionService
from app.features.wallet.dependencies import get_wallet_service
from app.features.wallet.services import WalletService
from app.infrastructure.database import get_database_session
from app.shared.payments.dependencies import get_payment_provider
from app.shared.payments.provider import PaymentProvider


def get_payment_service(
    database_session: Annotated[AsyncSession, Depends(get_database_session)],
    settings: Annotated[Settings, Depends(get_settings)],
    payment_provider: Annotated[PaymentProvider, Depends(get_payment_provider)],
    subscription_service: Annotated[SubscriptionService, Depends(get_subscription_service)],
) -> PaymentService:
    return PaymentService(
        repository=SQLAlchemyPaymentsRepository(database_session),
        payment_provider=payment_provider,
        subscription_service=subscription_service,
        success_url=settings.billing_success_url,
        cancel_url=settings.billing_cancel_url,
        portal_return_url=settings.billing_portal_return_url,
    )


def get_webhook_service(
    database_session: Annotated[AsyncSession, Depends(get_database_session)],
    payment_provider: Annotated[PaymentProvider, Depends(get_payment_provider)],
    subscription_service: Annotated[SubscriptionService, Depends(get_subscription_service)],
    wallet_service: Annotated[WalletService, Depends(get_wallet_service)],
) -> WebhookService:
    return WebhookService(
        payment_provider=payment_provider,
        payments_repository=SQLAlchemyPaymentsRepository(database_session),
        subscription_service=subscription_service,
        wallet_service=wallet_service,
    )
