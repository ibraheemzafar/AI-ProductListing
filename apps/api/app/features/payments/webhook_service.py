import logging
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import Any

from app.features.payments.repositories import PaymentsRepository
from app.features.subscriptions.models import SubscriptionPlan
from app.features.subscriptions.services import SubscriptionService
from app.features.wallet.services import WalletService
from app.shared.payments.provider import PaymentProvider

logger = logging.getLogger(__name__)

StripeObject = dict[str, Any]

PROVIDER = "stripe"


class WebhookService:
    """Verifies and dispatches Stripe webhook events.

    Money effects are idempotent at the ledger/subscription layer (unique
    constraints), so events are processed at-least-once safely; the
    processed_webhook_events table is a fast-path + audit record.
    """

    def __init__(
        self,
        payment_provider: PaymentProvider,
        payments_repository: PaymentsRepository,
        subscription_service: SubscriptionService,
        wallet_service: WalletService,
    ) -> None:
        self._provider = payment_provider
        self._payments_repository = payments_repository
        self._subscription_service = subscription_service
        self._wallet_service = wallet_service

    async def handle(self, *, payload: bytes, signature: str) -> None:
        event = self._provider.verify_and_parse_webhook(payload=payload, signature=signature)

        if await self._payments_repository.is_event_processed(event.id):
            logger.info("Skipping already-processed webhook", extra={"event_id": event.id})
            return

        handlers: dict[str, Callable[[StripeObject], Awaitable[None]]] = {
            "checkout.session.completed": self._on_checkout_completed,
            "customer.subscription.created": self._on_subscription_synced,
            "customer.subscription.updated": self._on_subscription_synced,
            "customer.subscription.deleted": self._on_subscription_deleted,
            "invoice.paid": self._on_invoice_paid,
            "invoice.payment_succeeded": self._on_invoice_paid,
            "invoice.payment_failed": self._on_invoice_failed,
            "charge.refunded": self._on_charge_refunded,
        }
        handler = handlers.get(event.type)
        if handler is not None:
            await handler(event.data_object)
        else:
            logger.info("Unhandled webhook type acknowledged", extra={"type": event.type})

        await self._payments_repository.mark_event_processed(event.id, PROVIDER, event.type)

    # --- handlers ----------------------------------------------------------

    async def _on_checkout_completed(self, session: StripeObject) -> None:
        # Only one-time top-ups grant here; subscriptions grant on invoice.paid.
        if session.get("mode") != "payment":
            return
        if session.get("payment_status") != "paid":
            return

        metadata = session.get("metadata") or {}
        user_id = session.get("client_reference_id") or metadata.get("user_id")
        plan = await self._resolve_plan(metadata, price_id=None)
        if user_id is None or plan is None:
            logger.warning(
                "Top-up checkout missing user/plan",
                extra={"session": session.get("id")},
            )
            return

        reference_id = session.get("payment_intent") or session.get("id")
        await self._wallet_service.grant_topup(
            user_id=str(user_id),
            credits=plan.credit_allowance,
            reference_type="stripe_payment_intent",
            reference_id=str(reference_id),
            description=f"{plan.name} top-up",
            metadata={"plan_code": plan.code, "checkout_session": session.get("id")},
        )

    async def _on_subscription_synced(self, subscription: StripeObject) -> None:
        await self._sync_subscription(subscription)

    async def _on_subscription_deleted(self, subscription: StripeObject) -> None:
        subscription_id = subscription.get("id")
        if subscription_id:
            await self._subscription_service.update_subscription_status(
                str(subscription_id),
                "canceled",
            )

    async def _on_invoice_paid(self, invoice: StripeObject) -> None:
        subscription_id = invoice.get("subscription")
        if not subscription_id:
            return  # one-off invoice, not a subscription renewal

        local = await self._subscription_service.get_subscription_by_stripe_id(str(subscription_id))
        if local is not None:
            user_id = local.user_id
            plan = await self._subscription_service.get_plan_by_id(local.plan_id)
        else:
            # Out-of-order delivery: subscription.created not seen yet. Fetch + sync.
            subscription = await self._provider.retrieve_subscription(str(subscription_id))
            context = await self._sync_subscription(subscription)
            if context is None:
                logger.warning(
                    "Invoice paid but subscription unresolved",
                    extra={"sub": subscription_id},
                )
                return
            user_id, plan = context

        if plan is None:
            return

        await self._wallet_service.grant_subscription_credits(
            user_id=user_id,
            allowance=plan.credit_allowance,
            rollover=plan.rollover,
            reference_type="stripe_invoice",
            reference_id=str(invoice.get("id")),
            description=f"{plan.name} renewal",
        )

    async def _on_invoice_failed(self, invoice: StripeObject) -> None:
        subscription_id = invoice.get("subscription")
        if subscription_id:
            await self._subscription_service.update_subscription_status(
                str(subscription_id),
                "past_due",
            )

    async def _on_charge_refunded(self, charge: StripeObject) -> None:
        payment_intent = charge.get("payment_intent")
        if not payment_intent:
            return
        original = await self._wallet_service.find_transaction(
            reference_type="stripe_payment_intent",
            reference_id=str(payment_intent),
            entry_type="topup",
        )
        if original is None:
            logger.info("Refund for non-topup charge ignored", extra={"charge": charge.get("id")})
            return

        amount = int(charge.get("amount") or 0)
        refunded = int(charge.get("amount_refunded") or 0)
        if amount <= 0 or refunded <= 0:
            return
        # Reverse credits in proportion to the dollars refunded.
        reverse_credits = round(original.amount * refunded / amount)
        if reverse_credits <= 0:
            return

        await self._wallet_service.clawback(
            user_id=original.user_id,
            credits=reverse_credits,
            reference_type="stripe_charge",
            reference_id=str(charge.get("id")),
            description="Refund clawback",
        )

    # --- helpers -----------------------------------------------------------

    async def _sync_subscription(
        self,
        subscription: StripeObject,
    ) -> tuple[str, SubscriptionPlan | None] | None:
        metadata = subscription.get("metadata") or {}
        customer = subscription.get("customer")
        user_id = metadata.get("user_id")
        if user_id is None and customer is not None:
            user_id = await self._payments_repository.get_user_id_by_customer(
                "stripe",
                str(customer),
            )
        if user_id is None:
            logger.warning("Cannot map subscription to user", extra={"sub": subscription.get("id")})
            return None

        plan = await self._resolve_plan(metadata, price_id=self._price_id(subscription))
        if plan is None:
            logger.warning(
                "Cannot resolve plan for subscription",
                extra={"sub": subscription.get("id")},
            )
            return None

        await self._subscription_service.upsert_subscription(
            user_id=str(user_id),
            plan_id=plan.id,
            stripe_customer_id=str(customer) if customer else None,
            stripe_subscription_id=str(subscription.get("id")),
            status=str(subscription.get("status")),
            current_period_start=self._timestamp(subscription.get("current_period_start")),
            current_period_end=self._timestamp(subscription.get("current_period_end")),
            cancel_at_period_end=bool(subscription.get("cancel_at_period_end")),
        )
        return str(user_id), plan

    async def _resolve_plan(
        self,
        metadata: dict[str, Any],
        price_id: str | None,
    ) -> SubscriptionPlan | None:
        plan_id = metadata.get("plan_id")
        if plan_id:
            plan = await self._subscription_service.get_plan_by_id(str(plan_id))
            if plan is not None:
                return plan
        if price_id:
            plan = await self._subscription_service.get_plan_by_stripe_price_id(price_id)
            if plan is not None:
                return plan
        plan_code = metadata.get("plan_code")
        if plan_code:
            return await self._subscription_service.get_plan_by_code(str(plan_code))
        return None

    @staticmethod
    def _price_id(subscription: StripeObject) -> str | None:
        items = (subscription.get("items") or {}).get("data") or []
        if not items:
            return None
        price = items[0].get("price") or {}
        price_id = price.get("id")
        return str(price_id) if price_id else None

    @staticmethod
    def _timestamp(value: Any) -> datetime | None:
        if not value:
            return None
        return datetime.fromtimestamp(int(value), UTC)
