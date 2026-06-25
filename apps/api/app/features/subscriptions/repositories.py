from datetime import UTC, datetime
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.subscriptions.models import SubscriptionPlan, UserSubscription

UserSubscriptionRow = tuple[UserSubscription, SubscriptionPlan]


class SubscriptionRepository(Protocol):
    async def list_active_plans(self) -> list[SubscriptionPlan]:
        pass

    async def get_plan_by_code(self, code: str) -> SubscriptionPlan | None:
        pass

    async def get_plan_by_id(self, plan_id: str) -> SubscriptionPlan | None:
        pass

    async def get_plan_by_stripe_price_id(self, price_id: str) -> SubscriptionPlan | None:
        pass

    async def get_current_subscription(self, user_id: str) -> UserSubscriptionRow | None:
        pass

    async def get_subscription_by_stripe_id(
        self,
        stripe_subscription_id: str,
    ) -> UserSubscription | None:
        pass

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
        pass

    async def update_subscription_status(
        self,
        stripe_subscription_id: str,
        status: str,
    ) -> None:
        pass


class SQLAlchemySubscriptionRepository:
    def __init__(self, database_session: AsyncSession) -> None:
        self._database_session = database_session

    async def list_active_plans(self) -> list[SubscriptionPlan]:
        result = await self._database_session.execute(
            select(SubscriptionPlan)
            .where(SubscriptionPlan.is_active.is_(True))
            .order_by(SubscriptionPlan.price_cents.asc()),
        )
        return list(result.scalars().all())

    async def get_plan_by_code(self, code: str) -> SubscriptionPlan | None:
        result = await self._database_session.execute(
            select(SubscriptionPlan).where(SubscriptionPlan.code == code),
        )
        return result.scalar_one_or_none()

    async def get_plan_by_id(self, plan_id: str) -> SubscriptionPlan | None:
        return await self._database_session.get(SubscriptionPlan, plan_id)

    async def get_plan_by_stripe_price_id(self, price_id: str) -> SubscriptionPlan | None:
        result = await self._database_session.execute(
            select(SubscriptionPlan).where(SubscriptionPlan.stripe_price_id == price_id),
        )
        return result.scalar_one_or_none()

    async def get_current_subscription(self, user_id: str) -> UserSubscriptionRow | None:
        result = await self._database_session.execute(
            select(UserSubscription, SubscriptionPlan)
            .join(SubscriptionPlan, SubscriptionPlan.id == UserSubscription.plan_id)
            .where(UserSubscription.user_id == user_id)
            .order_by(UserSubscription.created_at.desc()),
        )
        row = result.first()
        if row is None:
            return None
        return row[0], row[1]

    async def get_subscription_by_stripe_id(
        self,
        stripe_subscription_id: str,
    ) -> UserSubscription | None:
        result = await self._database_session.execute(
            select(UserSubscription).where(
                UserSubscription.stripe_subscription_id == stripe_subscription_id,
            ),
        )
        return result.scalar_one_or_none()

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
        existing = await self.get_subscription_by_stripe_id(stripe_subscription_id)
        if existing is not None:
            existing.user_id = user_id
            existing.plan_id = plan_id
            existing.stripe_customer_id = stripe_customer_id
            existing.status = status
            existing.current_period_start = current_period_start
            existing.current_period_end = current_period_end
            existing.cancel_at_period_end = cancel_at_period_end
            existing.updated_at = datetime.now(UTC)
            await self._database_session.commit()
            await self._database_session.refresh(existing)
            return existing

        subscription = UserSubscription(
            user_id=user_id,
            plan_id=plan_id,
            stripe_customer_id=stripe_customer_id,
            stripe_subscription_id=stripe_subscription_id,
            status=status,
            current_period_start=current_period_start,
            current_period_end=current_period_end,
            cancel_at_period_end=cancel_at_period_end,
        )
        self._database_session.add(subscription)
        try:
            await self._database_session.commit()
        except IntegrityError:
            # Concurrent create for the same stripe_subscription_id.
            await self._database_session.rollback()
            existing = await self.get_subscription_by_stripe_id(stripe_subscription_id)
            if existing is None:
                raise
            return existing
        await self._database_session.refresh(subscription)
        return subscription

    async def update_subscription_status(
        self,
        stripe_subscription_id: str,
        status: str,
    ) -> None:
        existing = await self.get_subscription_by_stripe_id(stripe_subscription_id)
        if existing is None:
            return
        existing.status = status
        existing.updated_at = datetime.now(UTC)
        await self._database_session.commit()
