from app.features.wallet.constants import ROLLOVER_CAP_MULTIPLIER, SIGNUP_BONUS_CREDITS
from app.features.wallet.models import Wallet, WalletTransaction
from app.features.wallet.repositories import WalletRepository
from app.features.wallet.schemas import WalletEntryType


class WalletService:
    """Owns credit accounting: balances and the append-only transaction ledger."""

    def __init__(self, repository: WalletRepository) -> None:
        self._repository = repository

    async def get_wallet(self, user_id: str) -> Wallet:
        return await self._repository.get_or_create_wallet(user_id)

    async def list_transactions(
        self,
        user_id: str,
        limit: int,
        offset: int,
    ) -> tuple[list[WalletTransaction], int]:
        return await self._repository.list_transactions(
            user_id=user_id,
            limit=limit,
            offset=offset,
        )

    async def has_minimum_balance(self, user_id: str, minimum: int) -> bool:
        wallet = await self._repository.get_or_create_wallet(user_id)
        return wallet.available_credits >= minimum

    async def grant_subscription_credits(
        self,
        *,
        user_id: str,
        allowance: int,
        rollover: bool,
        reference_type: str,
        reference_id: str,
        description: str = "Subscription credits",
    ) -> WalletTransaction | None:
        """Grant a billing-cycle's credits, applying capped rollover or reset.

        Idempotent per (reference_type, reference_id): a replayed invoice webhook
        returns None instead of double-granting.
        """
        cap = ROLLOVER_CAP_MULTIPLIER * allowance
        return await self._repository.apply_subscription_grant(
            user_id=user_id,
            allowance=allowance,
            rollover=rollover,
            cap=cap,
            entry_type=WalletEntryType.SUBSCRIPTION_GRANT.value,
            reference_type=reference_type,
            reference_id=reference_id,
            description=description,
        )

    async def grant_topup(
        self,
        *,
        user_id: str,
        credits: int,
        reference_type: str,
        reference_id: str,
        description: str = "Credit top-up",
        metadata: dict[str, object] | None = None,
    ) -> WalletTransaction | None:
        """Grant one-time top-up credits. Idempotent per (reference_type, reference_id)."""
        return await self._repository.apply_credit(
            user_id=user_id,
            amount=credits,
            entry_type=WalletEntryType.TOPUP.value,
            reference_type=reference_type,
            reference_id=reference_id,
            description=description,
            metadata=metadata or {},
        )

    async def clawback(
        self,
        *,
        user_id: str,
        credits: int,
        reference_type: str,
        reference_id: str,
        description: str = "Refund clawback",
    ) -> WalletTransaction:
        """Reverse credits after a refund/dispute (clamped at zero, idempotent)."""
        return await self._repository.apply_debit(
            user_id=user_id,
            amount=credits,
            entry_type=WalletEntryType.REFUND.value,
            reference_type=reference_type,
            reference_id=reference_id,
            description=description,
        )

    async def find_transaction(
        self,
        *,
        reference_type: str,
        reference_id: str,
        entry_type: str,
    ) -> WalletTransaction | None:
        return await self._repository.get_transaction(reference_type, reference_id, entry_type)

    async def grant_signup_bonus(self, user_id: str) -> int | None:
        """Grant the one-time signup bonus. Idempotent: returns None if already granted."""
        transaction = await self._repository.apply_credit(
            user_id=user_id,
            amount=SIGNUP_BONUS_CREDITS,
            entry_type=WalletEntryType.SIGNUP_BONUS.value,
            reference_type="user",
            reference_id=user_id,
            description="Welcome bonus credits",
            metadata={},
        )
        return SIGNUP_BONUS_CREDITS if transaction is not None else None

    async def debit_for_ai_request(
        self,
        *,
        user_id: str,
        credits: int,
        workflow: str,
        request_log_id: str,
    ) -> WalletTransaction:
        """Settle a completed AI request.

        The balance was gated before the request via ``has_minimum_balance``; the
        debit is clamped so an already-completed request is never failed here.
        """
        return await self._repository.apply_debit(
            user_id=user_id,
            amount=credits,
            entry_type=WalletEntryType.AI_DEBIT.value,
            reference_type="ai_request_log",
            reference_id=request_log_id,
            description=f"AI usage: {workflow}",
        )
