import hashlib
import hmac
import json
from datetime import UTC, datetime
from typing import Any, cast

import httpx

from app.core.errors import ConfigurationError, PaymentProviderError, WebhookVerificationError
from app.shared.payments.provider import CheckoutSession, LineItem, PortalSession, WebhookEvent


class PaddlePaymentProvider:
    provider_code = "paddle"

    def __init__(
        self,
        *,
        api_key: str,
        webhook_secret: str,
        environment: str,
        checkout_url: str | None = None,
        timeout_seconds: float = 30.0,
    ) -> None:
        self._api_key = api_key
        self._webhook_secret = webhook_secret
        self._base_url = (
            "https://api.paddle.com"
            if environment == "live"
            else "https://sandbox-api.paddle.com"
        )
        self._checkout_url = checkout_url
        self._timeout_seconds = timeout_seconds

    async def create_customer(self, *, email: str, metadata: dict[str, str]) -> str:
        payload = {"email": email, "custom_data": metadata}
        data = await self._request("POST", "/customers", json_payload=payload)
        customer_id = data.get("id")
        if not isinstance(customer_id, str):
            raise PaymentProviderError("Paddle customer response did not include an id")
        return customer_id

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
        if not self._checkout_url:
            raise ConfigurationError(
                "PADDLE_CHECKOUT_URL is required for Paddle checkout. Set it to your "
                "approved Paddle checkout/payment link URL, or define a Default Payment "
                "Link in Paddle Checkout settings.",
            )

        custom_data = dict(metadata)
        custom_data["client_reference_id"] = client_reference_id
        if subscription_metadata:
            custom_data.update(subscription_metadata)

        payload = {
            "items": line_items,
            "custom_data": custom_data,
            "collection_mode": "automatic",
        }
        if customer_id:
            payload["customer_id"] = customer_id
        payload["checkout"] = {"url": self._checkout_url}
        data = await self._request("POST", "/transactions", json_payload=payload)
        checkout = data.get("checkout") if isinstance(data.get("checkout"), dict) else {}
        checkout_url = checkout.get("url")
        transaction_id = data.get("id")
        if not isinstance(checkout_url, str) or not isinstance(transaction_id, str):
            raise PaymentProviderError("Paddle transaction response did not include a checkout URL")
        return CheckoutSession(id=transaction_id, url=checkout_url)

    async def create_billing_portal_session(
        self,
        *,
        customer_id: str,
        return_url: str,
    ) -> PortalSession:
        payload = {"customer_ids": [customer_id]}
        data = await self._request("POST", "/customer-portal-sessions", json_payload=payload)
        urls = data.get("urls") if isinstance(data.get("urls"), dict) else {}
        general = urls.get("general") if isinstance(urls.get("general"), dict) else {}
        overview_url = general.get("overview")
        if not isinstance(overview_url, str):
            raise PaymentProviderError("Paddle portal response did not include a portal URL")
        return PortalSession(url=overview_url)

    def verify_and_parse_webhook(self, *, payload: bytes, signature: str) -> WebhookEvent:
        if not self._webhook_secret:
            raise ConfigurationError("PADDLE_WEBHOOK_SECRET is required for webhooks")
        if not self._is_valid_signature(payload=payload, signature=signature):
            raise WebhookVerificationError()
        try:
            event = json.loads(payload.decode("utf-8"))
        except ValueError as error:
            raise WebhookVerificationError() from error

        data = event.get("data")
        if not isinstance(data, dict):
            raise WebhookVerificationError()
        return WebhookEvent(
            id=str(event.get("event_id") or event.get("id")),
            type=str(event.get("event_type") or event.get("type")),
            data_object=cast(dict[str, Any], data),
        )

    async def retrieve_subscription(self, subscription_id: str) -> dict[str, Any]:
        return await self._request("GET", f"/subscriptions/{subscription_id}")

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json_payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not self._api_key:
            raise ConfigurationError("PADDLE_API_KEY is required for Paddle payments")

        async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
            try:
                response = await client.request(
                    method,
                    f"{self._base_url}{path}",
                    headers={
                        "Authorization": f"Bearer {self._api_key}",
                        "Content-Type": "application/json",
                    },
                    json=json_payload,
                )
                response.raise_for_status()
            except httpx.HTTPStatusError as error:
                raise PaymentProviderError(self._extract_error_message(error.response)) from error
            except httpx.HTTPError as error:
                raise PaymentProviderError(str(error)) from error

        try:
            payload = response.json()
        except ValueError as error:
            raise PaymentProviderError("Paddle returned a non-JSON response") from error
        data = payload.get("data") if isinstance(payload, dict) else None
        if not isinstance(data, dict):
            raise PaymentProviderError("Paddle response did not include a data object")
        return cast(dict[str, Any], data)

    def _is_valid_signature(self, *, payload: bytes, signature: str) -> bool:
        parts = dict(part.split("=", 1) for part in signature.split(";") if "=" in part)
        timestamp = parts.get("ts")
        provided = parts.get("h1")
        if timestamp is None or provided is None:
            return False

        signed_payload = timestamp.encode("utf-8") + b":" + payload
        expected = hmac.new(
            self._webhook_secret.encode("utf-8"),
            signed_payload,
            hashlib.sha256,
        ).hexdigest()

        try:
            signed_at = datetime.fromtimestamp(int(timestamp), UTC)
        except ValueError:
            return False
        if abs((datetime.now(UTC) - signed_at).total_seconds()) > 300:
            return False
        return hmac.compare_digest(expected, provided)

    def _extract_error_message(self, response: httpx.Response) -> str:
        if response.status_code in {401, 403}:
            return (
                "Paddle rejected the request because the API key is not permitted. "
                "Use a Paddle API key for the configured environment with transaction.write "
                "permission."
            )
        try:
            payload = response.json()
        except ValueError:
            return response.text[:300] or "Paddle returned an error"
        if isinstance(payload, dict):
            error = payload.get("error")
            if isinstance(error, dict) and isinstance(error.get("detail"), str):
                return cast(str, error["detail"])[:300]
            if isinstance(error, dict) and isinstance(error.get("message"), str):
                return cast(str, error["message"])[:300]
        return "Paddle returned an error"
