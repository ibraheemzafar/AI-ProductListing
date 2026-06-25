from dataclasses import dataclass
from typing import Any, Protocol

LineItem = dict[str, Any]


@dataclass(frozen=True)
class CheckoutSession:
    id: str
    url: str


@dataclass(frozen=True)
class PortalSession:
    url: str


@dataclass(frozen=True)
class WebhookEvent:
    id: str
    type: str
    data_object: dict[str, Any]


class PaymentProvider(Protocol):
    """Abstraction over a payment gateway (Stripe is the only implementation today)."""

    async def create_customer(self, *, email: str, metadata: dict[str, str]) -> str:
        """Create a gateway customer and return its id."""
        ...

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
        """Create a hosted checkout session and return its id and redirect URL."""
        ...

    async def create_billing_portal_session(
        self,
        *,
        customer_id: str,
        return_url: str,
    ) -> PortalSession:
        """Create a hosted billing-portal session for managing the subscription."""
        ...

    def verify_and_parse_webhook(self, *, payload: bytes, signature: str) -> WebhookEvent:
        """Verify a webhook signature and return the parsed event."""
        ...

    async def retrieve_subscription(self, subscription_id: str) -> dict[str, Any]:
        """Fetch a subscription object (fallback for out-of-order webhook delivery)."""
        ...
