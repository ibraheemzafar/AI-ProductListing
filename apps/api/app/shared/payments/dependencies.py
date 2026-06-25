from functools import lru_cache

from app.core.config import get_settings
from app.shared.payments.provider import PaymentProvider
from app.shared.payments.stripe_provider import StripePaymentProvider


@lru_cache
def _build_payment_provider() -> StripePaymentProvider:
    settings = get_settings()
    return StripePaymentProvider(
        api_key=settings.stripe_secret_key,
        webhook_secret=settings.stripe_webhook_secret,
    )


def get_payment_provider() -> PaymentProvider:
    return _build_payment_provider()
