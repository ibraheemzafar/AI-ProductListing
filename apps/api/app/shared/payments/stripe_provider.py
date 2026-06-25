import asyncio
from typing import Any

from app.core.errors import (
    ConfigurationError,
    PaymentProviderError,
    WebhookVerificationError,
)
from app.shared.payments.provider import (
    CheckoutSession,
    LineItem,
    PortalSession,
    WebhookEvent,
)


class StripePaymentProvider:
    """Stripe implementation of PaymentProvider.

    ``stripe`` is imported lazily so the application boots even when the package
    is not installed; billing endpoints then fail with a clear ConfigurationError
    instead of crashing the whole API at import time.
    """

    def __init__(self, *, api_key: str, webhook_secret: str) -> None:
        self._api_key = api_key
        self._webhook_secret = webhook_secret

    def _stripe(self) -> Any:
        if not self._api_key:
            raise ConfigurationError("STRIPE_SECRET_KEY is required for payments")
        try:
            import stripe
        except ModuleNotFoundError as error:  # pragma: no cover - install-time guard
            raise ConfigurationError(
                "The 'stripe' package is not installed. Run: uv pip install stripe",
            ) from error
        return stripe

    async def create_customer(self, *, email: str, metadata: dict[str, str]) -> str:
        stripe = self._stripe()
        try:
            customer = await asyncio.to_thread(
                stripe.Customer.create,
                email=email,
                metadata=metadata,
                api_key=self._api_key,
            )
        except Exception as error:
            raise PaymentProviderError(str(error)) from error
        return str(customer.id)

    async def create_checkout_session(
        self,
        *,
        mode: str,
        line_items: list[LineItem],
        success_url: str,
        cancel_url: str,
        customer_id: str,
        client_reference_id: str,
        metadata: dict[str, str],
        subscription_metadata: dict[str, str] | None = None,
    ) -> CheckoutSession:
        stripe = self._stripe()
        params: dict[str, Any] = {
            "mode": mode,
            "line_items": line_items,
            "success_url": success_url,
            "cancel_url": cancel_url,
            "customer": customer_id,
            "client_reference_id": client_reference_id,
            "metadata": metadata,
            "api_key": self._api_key,
        }
        # Checkout metadata does not propagate to the created subscription, so stamp
        # it onto the subscription too for webhook plan resolution in Phase 6.
        if mode == "subscription" and subscription_metadata is not None:
            params["subscription_data"] = {"metadata": subscription_metadata}
        try:
            session = await asyncio.to_thread(stripe.checkout.Session.create, **params)
        except Exception as error:
            raise PaymentProviderError(str(error)) from error
        return CheckoutSession(id=str(session.id), url=str(session.url))

    async def create_billing_portal_session(
        self,
        *,
        customer_id: str,
        return_url: str,
    ) -> PortalSession:
        stripe = self._stripe()
        try:
            session = await asyncio.to_thread(
                stripe.billing_portal.Session.create,
                customer=customer_id,
                return_url=return_url,
                api_key=self._api_key,
            )
        except Exception as error:
            raise PaymentProviderError(str(error)) from error
        return PortalSession(url=str(session.url))

    def verify_and_parse_webhook(self, *, payload: bytes, signature: str) -> WebhookEvent:
        stripe = self._stripe()
        if not self._webhook_secret:
            raise ConfigurationError("STRIPE_WEBHOOK_SECRET is required for webhooks")
        try:
            event = stripe.Webhook.construct_event(payload, signature, self._webhook_secret)
        except Exception as error:
            raise WebhookVerificationError() from error
        return WebhookEvent(
            id=str(event["id"]),
            type=str(event["type"]),
            data_object=dict(event["data"]["object"]),
        )

    async def retrieve_subscription(self, subscription_id: str) -> dict[str, Any]:
        stripe = self._stripe()
        try:
            subscription = await asyncio.to_thread(
                stripe.Subscription.retrieve,
                subscription_id,
                api_key=self._api_key,
            )
        except Exception as error:
            raise PaymentProviderError(str(error)) from error
        return dict(subscription)
