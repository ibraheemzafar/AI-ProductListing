from dataclasses import dataclass
from typing import Protocol

from app.core.errors import InsufficientCreditsError
from app.features.billing_meter.pricing import CreditPricingPolicy, UsageInput
from app.features.wallet.services import WalletService


@dataclass(frozen=True)
class ChargeResult:
    credits_charged: int
    transaction_id: str


class RequestMeter(Protocol):
    """Abstraction the AI services depend on (DIP); BillingMeter implements it."""

    async def authorize(self, user_id: str) -> None:
        pass

    async def charge(
        self,
        *,
        user_id: str,
        workflow: str,
        usage: UsageInput,
        request_log_id: str,
    ) -> ChargeResult:
        pass


class BillingMeter:
    """Gates AI requests on wallet balance and settles the credit cost afterwards."""

    def __init__(
        self,
        wallet_service: WalletService,
        pricing_policy: CreditPricingPolicy,
        minimum_balance: int,
    ) -> None:
        self._wallet_service = wallet_service
        self._pricing_policy = pricing_policy
        self._minimum_balance = minimum_balance

    async def authorize(self, user_id: str) -> None:
        """Block before the provider call if the user cannot afford a request."""
        if not await self._wallet_service.has_minimum_balance(user_id, self._minimum_balance):
            raise InsufficientCreditsError()

    async def charge(
        self,
        *,
        user_id: str,
        workflow: str,
        usage: UsageInput,
        request_log_id: str,
    ) -> ChargeResult:
        """Debit the credit cost of a completed request. Never raises for balance."""
        credits = self._pricing_policy.credits_for(usage)
        transaction = await self._wallet_service.debit_for_ai_request(
            user_id=user_id,
            credits=credits,
            workflow=workflow,
            request_log_id=request_log_id,
        )
        return ChargeResult(credits_charged=-transaction.amount, transaction_id=transaction.id)
