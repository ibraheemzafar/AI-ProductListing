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

PaddleObject = dict[str, Any]
PROVIDER = "paddle"


class PaddleWebhookService:
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
            logger.info("Skipping already-processed Paddle webhook", extra={"event_id": event.id})
            return

        handlers: dict[str, Callable[[PaddleObject], Awaitable[None]]] = {
            "transaction.completed": self._on_transaction_completed,
            "subscription.created": self._on_subscription_synced,
            "subscription.updated": self._on_subscription_synced,
            "subscription.canceled": self._on_subscription_canceled,
            "subscription.past_due": self._on_subscription_past_due,
        }
        handler = handlers.get(event.type)
        if handler is not None:
            await handler(event.data_object)
        else:
            logger.info("Unhandled Paddle webhook type acknowledged", extra={"type": event.type})

        await self._payments_repository.mark_event_processed(event.id, PROVIDER, event.type)

    async def _on_transaction_completed(self, transaction: PaddleObject) -> None:
        if transaction.get("status") not in {None, "completed", "paid"}:
            return

        custom_data = transaction.get("custom_data") or {}
        plan = await self._resolve_plan(custom_data, price_id=self._price_id(transaction))
        user_id = custom_data.get("user_id")
        customer_id = transaction.get("customer_id")
        if user_id is None and customer_id is not None:
            user_id = await self._payments_repository.get_user_id_by_customer(
                PROVIDER,
                str(customer_id),
            )
        if user_id is None or plan is None:
            logger.warning(
                "Paddle transaction missing user/plan",
                extra={"transaction": transaction.get("id")},
            )
            return

        subscription_id = transaction.get("subscription_id")
        if plan.plan_type == "subscription":
            if subscription_id:
                local = await self._subscription_service.get_subscription_by_paddle_id(
                    str(subscription_id),
                )
                if local is None:
                    subscription = await self._provider.retrieve_subscription(str(subscription_id))
                    await self._sync_subscription(subscription)
            await self._wallet_service.grant_subscription_credits(
                user_id=str(user_id),
                allowance=plan.credit_allowance,
                rollover=plan.rollover,
                reference_type="paddle_transaction",
                reference_id=str(transaction.get("id")),
                description=f"{plan.name} renewal",
            )
            return

        await self._wallet_service.grant_topup(
            user_id=str(user_id),
            credits=plan.credit_allowance,
            reference_type="paddle_transaction",
            reference_id=str(transaction.get("id")),
            description=f"{plan.name} top-up",
            metadata={"plan_code": plan.code},
        )

    async def _on_subscription_synced(self, subscription: PaddleObject) -> None:
        await self._sync_subscription(subscription)

    async def _on_subscription_canceled(self, subscription: PaddleObject) -> None:
        subscription_id = subscription.get("id")
        if subscription_id:
            await self._subscription_service.update_paddle_subscription_status(
                str(subscription_id),
                "canceled",
            )

    async def _on_subscription_past_due(self, subscription: PaddleObject) -> None:
        subscription_id = subscription.get("id")
        if subscription_id:
            await self._subscription_service.update_paddle_subscription_status(
                str(subscription_id),
                "past_due",
            )

    async def _sync_subscription(
        self,
        subscription: PaddleObject,
    ) -> tuple[str, SubscriptionPlan | None] | None:
        custom_data = subscription.get("custom_data") or {}
        customer_id = subscription.get("customer_id")
        user_id = custom_data.get("user_id")
        if user_id is None and customer_id is not None:
            user_id = await self._payments_repository.get_user_id_by_customer(
                PROVIDER,
                str(customer_id),
            )
        if user_id is None:
            logger.warning(
                "Cannot map Paddle subscription to user",
                extra={"sub": subscription.get("id")},
            )
            return None

        plan = await self._resolve_plan(custom_data, price_id=self._price_id(subscription))
        if plan is None:
            logger.warning(
                "Cannot resolve plan for Paddle subscription",
                extra={"sub": subscription.get("id")},
            )
            return None

        period = subscription.get("current_billing_period") or {}
        scheduled_change = subscription.get("scheduled_change") or {}
        await self._subscription_service.upsert_subscription(
            user_id=str(user_id),
            plan_id=plan.id,
            stripe_customer_id=None,
            stripe_subscription_id=None,
            paddle_customer_id=str(customer_id) if customer_id else None,
            paddle_subscription_id=str(subscription.get("id")),
            status=str(subscription.get("status") or "active"),
            current_period_start=self._timestamp(period.get("starts_at")),
            current_period_end=self._timestamp(period.get("ends_at")),
            cancel_at_period_end=scheduled_change.get("action") == "cancel",
        )
        return str(user_id), plan

    async def _resolve_plan(
        self,
        custom_data: dict[str, Any],
        price_id: str | None,
    ) -> SubscriptionPlan | None:
        plan_id = custom_data.get("plan_id")
        if plan_id:
            plan = await self._subscription_service.get_plan_by_id(str(plan_id))
            if plan is not None:
                return plan
        if price_id:
            plan = await self._subscription_service.get_plan_by_paddle_price_id(price_id)
            if plan is not None:
                return plan
        plan_code = custom_data.get("plan_code")
        if plan_code:
            return await self._subscription_service.get_plan_by_code(str(plan_code))
        return None

    @staticmethod
    def _price_id(source: PaddleObject) -> str | None:
        items = source.get("items")
        if not isinstance(items, list) or not items:
            return None
        price = items[0].get("price") if isinstance(items[0], dict) else None
        if isinstance(price, dict) and isinstance(price.get("id"), str):
            return str(price["id"])
        price_id = items[0].get("price_id") if isinstance(items[0], dict) else None
        return str(price_id) if price_id else None

    @staticmethod
    def _timestamp(value: Any) -> datetime | None:
        if not value:
            return None
        if isinstance(value, str):
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        return datetime.fromtimestamp(int(value), UTC)
