from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict

from app.features.wallet.models import Wallet, WalletTransaction


class WalletEntryType(str, Enum):
    SIGNUP_BONUS = "signup_bonus"
    SUBSCRIPTION_GRANT = "subscription_grant"
    TOPUP = "topup"
    AI_DEBIT = "ai_debit"
    REFUND = "refund"
    ADJUSTMENT = "adjustment"


class WalletResponse(BaseModel):
    id: str
    user_id: str
    total_credits: int
    available_credits: int

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_model(cls, wallet: Wallet) -> "WalletResponse":
        return cls(
            id=wallet.id,
            user_id=wallet.user_id,
            total_credits=wallet.total_credits,
            available_credits=wallet.available_credits,
        )


class WalletTransactionResponse(BaseModel):
    id: str
    entry_type: str
    amount: int
    balance_after: int
    reference_type: str | None
    reference_id: str | None
    description: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_model(cls, transaction: WalletTransaction) -> "WalletTransactionResponse":
        return cls(
            id=transaction.id,
            entry_type=transaction.entry_type,
            amount=transaction.amount,
            balance_after=transaction.balance_after,
            reference_type=transaction.reference_type,
            reference_id=transaction.reference_id,
            description=transaction.description,
            created_at=transaction.created_at,
        )


class WalletTransactionListResponse(BaseModel):
    transactions: list[WalletTransactionResponse]
    total: int
    limit: int
    offset: int
