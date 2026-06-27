from typing import Protocol

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.payments.models import BillingCustomer, ProcessedWebhookEvent


class PaymentsRepository(Protocol):
    async def get_customer(self, user_id: str) -> BillingCustomer | None:
        pass

    async def save_customer(
        self,
        user_id: str,
        provider_code: str,
        customer_id: str,
    ) -> BillingCustomer:
        pass

    async def get_user_id_by_customer(self, provider_code: str, customer_id: str) -> str | None:
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

    async def save_customer(
        self,
        user_id: str,
        provider_code: str,
        customer_id: str,
    ) -> BillingCustomer:
        customer = await self.get_customer(user_id)
        if customer is None:
            customer = BillingCustomer(user_id=user_id)
            self._database_session.add(customer)

        self._set_customer_id(customer, provider_code, customer_id)
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

    async def get_user_id_by_customer(self, provider_code: str, customer_id: str) -> str | None:
        column = self._customer_id_column(provider_code)
        result = await self._database_session.execute(
            select(BillingCustomer.user_id).where(column == customer_id),
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

    def _set_customer_id(
        self,
        customer: BillingCustomer,
        provider_code: str,
        customer_id: str,
    ) -> None:
        if provider_code == "stripe":
            customer.stripe_customer_id = customer_id
            return
        if provider_code == "paddle":
            customer.paddle_customer_id = customer_id
            return
        raise ValueError(f"Unsupported payment provider: {provider_code}")

    def _customer_id_column(self, provider_code: str):  # type: ignore[no-untyped-def]
        if provider_code == "stripe":
            return BillingCustomer.stripe_customer_id
        if provider_code == "paddle":
            return BillingCustomer.paddle_customer_id
        raise ValueError(f"Unsupported payment provider: {provider_code}")
