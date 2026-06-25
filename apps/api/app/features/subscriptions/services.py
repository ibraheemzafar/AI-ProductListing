from datetime import datetime

from app.features.subscriptions.models import SubscriptionPlan, UserSubscription
from app.features.subscriptions.repositories import SubscriptionRepository, UserSubscriptionRow


class SubscriptionService:
    """Reads the plan catalog and manages a user's subscription state.

    Lifecycle mutations are driven by Stripe webhooks; reads back the current state.
    """

    def __init__(self, repository: SubscriptionRepository) -> None:
        self._repository = repository

    async def list_active_plans(self) -> list[SubscriptionPlan]:
        return await self._repository.list_active_plans()

    async def get_plan_by_code(self, code: str) -> SubscriptionPlan | None:
        return await self._repository.get_plan_by_code(code)

    async def get_plan_by_id(self, plan_id: str) -> SubscriptionPlan | None:
        return await self._repository.get_plan_by_id(plan_id)

    async def get_plan_by_stripe_price_id(self, price_id: str) -> SubscriptionPlan | None:
        return await self._repository.get_plan_by_stripe_price_id(price_id)

    async def get_current_subscription(self, user_id: str) -> UserSubscriptionRow | None:
        return await self._repository.get_current_subscription(user_id)

    async def get_subscription_by_stripe_id(
        self,
        stripe_subscription_id: str,
    ) -> UserSubscription | None:
        return await self._repository.get_subscription_by_stripe_id(stripe_subscription_id)

    async def upsert_subscription(
        self,
        *,
        user_id: str,
        plan_id: str,
        stripe_customer_id: str | None,
        stripe_subscription_id: str,
        status: str,
        current_period_start: datetime | None,
        current_period_end: datetime | None,
        cancel_at_period_end: bool,
    ) -> UserSubscription:
        return await self._repository.upsert_subscription(
            user_id=user_id,
            plan_id=plan_id,
            stripe_customer_id=stripe_customer_id,
            stripe_subscription_id=stripe_subscription_id,
            status=status,
            current_period_start=current_period_start,
            current_period_end=current_period_end,
            cancel_at_period_end=cancel_at_period_end,
        )

    async def update_subscription_status(self, stripe_subscription_id: str, status: str) -> None:
        await self._repository.update_subscription_status(stripe_subscription_id, status)
