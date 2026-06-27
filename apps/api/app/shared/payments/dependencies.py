from functools import lru_cache

from app.core.config import get_settings
from app.shared.payments.paddle_provider import PaddlePaymentProvider
from app.shared.payments.provider import PaymentProvider
from app.shared.payments.stripe_provider import StripePaymentProvider


@lru_cache
def _build_stripe_payment_provider() -> StripePaymentProvider:
    settings = get_settings()
    return StripePaymentProvider(
        api_key=settings.stripe_secret_key,
        webhook_secret=settings.stripe_webhook_secret,
    )


@lru_cache
def _build_paddle_payment_provider() -> PaddlePaymentProvider:
    settings = get_settings()
    return PaddlePaymentProvider(
        api_key=settings.paddle_api_key,
        webhook_secret=settings.paddle_webhook_secret,
        environment=settings.paddle_environment,
        checkout_url=settings.paddle_checkout_url or None,
        timeout_seconds=settings.openai_timeout_seconds,
    )


def get_payment_provider() -> PaymentProvider:
    settings = get_settings()
    if settings.payment_provider_code == "paddle":
        return _build_paddle_payment_provider()
    return _build_stripe_payment_provider()


def get_stripe_payment_provider() -> StripePaymentProvider:
    return _build_stripe_payment_provider()


def get_paddle_payment_provider() -> PaddlePaymentProvider:
    return _build_paddle_payment_provider()
