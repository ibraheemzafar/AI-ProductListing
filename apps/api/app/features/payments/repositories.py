from typing import Protocol

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.payments.models import BillingCustomer, ProcessedWebhookEvent


class PaymentsRepository(Protocol):
    async def get_customer(self, user_id: str) -> BillingCustomer | None:
        pass

    async def save_customer(self, user_id: str, stripe_customer_id: str) -> BillingCustomer:
        pass

    async def get_user_id_by_customer(self, stripe_customer_id: str) -> str | None:
        pass

    async def is_event_processed(self, event_id: str) -> bool:
        pass

    async def mark_event_processed(self, event_id: str, provider: str, event_type: str) -> None:
        pass


class SQLAlchemyPaymentsRepository:
    def __init__(self, database_session: AsyncSession) -> None:
        self._database_session = database_session

    async def get_customer(self, user_id: str) -> BillingCustomer | None:
        result = await self._database_session.execute(
            select(BillingCustomer).where(BillingCustomer.user_id == user_id),
        )
        return result.scalar_one_or_none()

    async def save_customer(self, user_id: str, stripe_customer_id: str) -> BillingCustomer:
        customer = BillingCustomer(user_id=user_id, stripe_customer_id=stripe_customer_id)
        self._database_session.add(customer)
        try:
            await self._database_session.commit()
        except IntegrityError:
            # A concurrent request already linked this user's customer.
            await self._database_session.rollback()
            existing = await self.get_customer(user_id)
            if existing is None:
                raise
            return existing
        await self._database_session.refresh(customer)
        return customer

    async def get_user_id_by_customer(self, stripe_customer_id: str) -> str | None:
        result = await self._database_session.execute(
            select(BillingCustomer.user_id).where(
                BillingCustomer.stripe_customer_id == stripe_customer_id,
            ),
        )
        return result.scalar_one_or_none()

    async def is_event_processed(self, event_id: str) -> bool:
        existing = await self._database_session.get(ProcessedWebhookEvent, event_id)
        return existing is not None

    async def mark_event_processed(self, event_id: str, provider: str, event_type: str) -> None:
        self._database_session.add(
            ProcessedWebhookEvent(id=event_id, provider=provider, event_type=event_type),
        )
        try:
            await self._database_session.commit()
        except IntegrityError:
            # Already recorded by a concurrent delivery; effects are idempotent anyway.
            await self._database_session.rollback()
