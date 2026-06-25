from datetime import UTC, datetime
from typing import Protocol

from sqlalchemy import desc, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.wallet.models import Wallet, WalletTransaction


class WalletRepository(Protocol):
    async def get_or_create_wallet(self, user_id: str) -> Wallet:
        pass

    async def apply_credit(
        self,
        *,
        user_id: str,
        amount: int,
        entry_type: str,
        reference_type: str | None,
        reference_id: str | None,
        description: str | None,
        metadata: dict[str, object] | None,
    ) -> WalletTransaction | None:
        pass

    async def apply_debit(
        self,
        *,
        user_id: str,
        amount: int,
        entry_type: str,
        reference_type: str | None,
        reference_id: str | None,
        description: str | None,
    ) -> WalletTransaction:
        pass

    async def apply_subscription_grant(
        self,
        *,
        user_id: str,
        allowance: int,
        rollover: bool,
        cap: int,
        entry_type: str,
        reference_type: str | None,
        reference_id: str | None,
        description: str | None,
    ) -> WalletTransaction | None:
        pass

    async def list_transactions(
        self,
        user_id: str,
        limit: int,
        offset: int,
    ) -> tuple[list[WalletTransaction], int]:
        pass

    async def get_transaction(
        self,
        reference_type: str | None,
        reference_id: str | None,
        entry_type: str,
    ) -> WalletTransaction | None:
        pass


class SQLAlchemyWalletRepository:
    def __init__(self, database_session: AsyncSession) -> None:
        self._database_session = database_session

    async def get_or_create_wallet(self, user_id: str) -> Wallet:
        existing = await self._get_wallet(user_id)
        if existing is not None:
            return existing

        wallet = Wallet(user_id=user_id, total_credits=0, available_credits=0, version=0)
        self._database_session.add(wallet)
        try:
            await self._database_session.commit()
        except IntegrityError:
            # Another concurrent request created the wallet first.
            await self._database_session.rollback()
            existing = await self._get_wallet(user_id)
            if existing is None:
                raise
            return existing
        await self._database_session.refresh(wallet)
        return wallet

    async def apply_credit(
        self,
        *,
        user_id: str,
        amount: int,
        entry_type: str,
        reference_type: str | None,
        reference_id: str | None,
        description: str | None,
        metadata: dict[str, object] | None,
    ) -> WalletTransaction | None:
        wallet = await self.get_or_create_wallet(user_id)
        statement = (
            update(Wallet)
            .where(Wallet.id == wallet.id)
            .values(
                available_credits=Wallet.available_credits + amount,
                total_credits=Wallet.total_credits + amount,
                version=Wallet.version + 1,
                updated_at=datetime.now(UTC),
            )
            .returning(Wallet.available_credits)
        )
        result = await self._database_session.execute(statement)
        balance_after = result.scalar_one()

        transaction = WalletTransaction(
            wallet_id=wallet.id,
            user_id=user_id,
            entry_type=entry_type,
            amount=amount,
            balance_after=balance_after,
            reference_type=reference_type,
            reference_id=reference_id,
            description=description,
            entry_metadata=metadata or {},
        )
        self._database_session.add(transaction)
        try:
            await self._database_session.commit()
        except IntegrityError:
            # Duplicate (reference_type, reference_id, entry_type): already credited.
            # Rollback undoes the wallet increment too, keeping the grant idempotent.
            await self._database_session.rollback()
            return None
        await self._database_session.refresh(transaction)
        return transaction

    async def apply_debit(
        self,
        *,
        user_id: str,
        amount: int,
        entry_type: str,
        reference_type: str | None,
        reference_id: str | None,
        description: str | None,
    ) -> WalletTransaction:
        """Debit up to ``amount`` credits, clamped so the balance never goes negative.

        The wallet row is locked FOR UPDATE so concurrent debits serialize. The
        caller is expected to have already gated on a minimum balance; clamping
        here guarantees a completed AI request is never failed for a settlement
        race after the provider cost was already incurred. Idempotent on the
        (reference_type, reference_id, entry_type) unique constraint.
        """
        wallet = await self.get_or_create_wallet(user_id)
        locked_result = await self._database_session.execute(
            select(Wallet).where(Wallet.id == wallet.id).with_for_update(),
        )
        locked = locked_result.scalar_one()

        debited = min(amount, locked.available_credits)
        locked.available_credits = locked.available_credits - debited
        locked.version = locked.version + 1
        locked.updated_at = datetime.now(UTC)

        transaction = WalletTransaction(
            wallet_id=locked.id,
            user_id=user_id,
            entry_type=entry_type,
            amount=-debited,
            balance_after=locked.available_credits,
            reference_type=reference_type,
            reference_id=reference_id,
            description=description,
            entry_metadata={"requested": amount, "debited": debited},
        )
        self._database_session.add(transaction)
        try:
            await self._database_session.commit()
        except IntegrityError:
            # This reference was already debited; return the existing entry.
            await self._database_session.rollback()
            existing = await self._get_transaction(reference_type, reference_id, entry_type)
            if existing is None:
                raise
            return existing
        await self._database_session.refresh(transaction)
        return transaction

    async def apply_subscription_grant(
        self,
        *,
        user_id: str,
        allowance: int,
        rollover: bool,
        cap: int,
        entry_type: str,
        reference_type: str | None,
        reference_id: str | None,
        description: str | None,
    ) -> WalletTransaction | None:
        """Apply a billing-cycle credit grant.

        With rollover, unused credits carry over but the balance is capped at
        ``cap``. Without rollover, the balance is reset to the plan ``allowance``.
        The ledger entry records the signed delta and is idempotent on the
        (reference_type, reference_id, entry_type) unique constraint.
        """
        wallet = await self.get_or_create_wallet(user_id)
        locked_result = await self._database_session.execute(
            select(Wallet).where(Wallet.id == wallet.id).with_for_update(),
        )
        locked = locked_result.scalar_one()

        old_available = locked.available_credits
        if rollover:
            new_available = min(old_available + allowance, cap)
        else:
            new_available = allowance
        delta = new_available - old_available

        locked.available_credits = new_available
        # Lifetime total only ever counts credits actually added.
        locked.total_credits = locked.total_credits + max(delta, 0)
        locked.version = locked.version + 1
        locked.updated_at = datetime.now(UTC)

        transaction = WalletTransaction(
            wallet_id=locked.id,
            user_id=user_id,
            entry_type=entry_type,
            amount=delta,
            balance_after=new_available,
            reference_type=reference_type,
            reference_id=reference_id,
            description=description,
            entry_metadata={
                "allowance": allowance,
                "rollover": rollover,
                "cap": cap if rollover else None,
            },
        )
        self._database_session.add(transaction)
        try:
            await self._database_session.commit()
        except IntegrityError:
            # Already granted for this reference (e.g. duplicate invoice webhook).
            await self._database_session.rollback()
            return None
        await self._database_session.refresh(transaction)
        return transaction

    async def list_transactions(
        self,
        user_id: str,
        limit: int,
        offset: int,
    ) -> tuple[list[WalletTransaction], int]:
        total_result = await self._database_session.execute(
            select(func.count(WalletTransaction.id)).where(WalletTransaction.user_id == user_id),
        )
        total = total_result.scalar_one()

        result = await self._database_session.execute(
            select(WalletTransaction)
            .where(WalletTransaction.user_id == user_id)
            .order_by(desc(WalletTransaction.created_at))
            .limit(limit)
            .offset(offset),
        )
        return list(result.scalars().all()), total

    async def get_transaction(
        self,
        reference_type: str | None,
        reference_id: str | None,
        entry_type: str,
    ) -> WalletTransaction | None:
        return await self._get_transaction(reference_type, reference_id, entry_type)

    async def _get_wallet(self, user_id: str) -> Wallet | None:
        result = await self._database_session.execute(
            select(Wallet).where(Wallet.user_id == user_id),
        )
        return result.scalar_one_or_none()

    async def _get_transaction(
        self,
        reference_type: str | None,
        reference_id: str | None,
        entry_type: str,
    ) -> WalletTransaction | None:
        result = await self._database_session.execute(
            select(WalletTransaction).where(
                WalletTransaction.reference_type == reference_type,
                WalletTransaction.reference_id == reference_id,
                WalletTransaction.entry_type == entry_type,
            ),
        )
        return result.scalar_one_or_none()
