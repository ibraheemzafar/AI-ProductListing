from typing import Annotated

from fastapi import Depends

from app.features.billing_meter.pricing import FlatPricingPolicy, TokenWeightedPricingPolicy
from app.features.billing_meter.service import BillingMeter
from app.features.wallet.constants import (
    FLAT_CREDITS_PER_IMAGE,
    INPUT_WEIGHT,
    MARGIN_MULTIPLIER,
    MIN_CREDITS_PER_REQUEST,
    OUTPUT_WEIGHT,
    TOKENS_PER_CREDIT,
)
from app.features.wallet.dependencies import get_wallet_service
from app.features.wallet.services import WalletService


def get_token_billing_meter(
    wallet_service: Annotated[WalletService, Depends(get_wallet_service)],
) -> BillingMeter:
    return BillingMeter(
        wallet_service=wallet_service,
        pricing_policy=TokenWeightedPricingPolicy(
            input_weight=INPUT_WEIGHT,
            output_weight=OUTPUT_WEIGHT,
            tokens_per_credit=TOKENS_PER_CREDIT,
            margin_multiplier=MARGIN_MULTIPLIER,
            min_credits=MIN_CREDITS_PER_REQUEST,
        ),
        minimum_balance=MIN_CREDITS_PER_REQUEST,
    )


def get_flat_billing_meter(
    wallet_service: Annotated[WalletService, Depends(get_wallet_service)],
) -> BillingMeter:
    return BillingMeter(
        wallet_service=wallet_service,
        pricing_policy=FlatPricingPolicy(flat_credits=FLAT_CREDITS_PER_IMAGE),
        minimum_balance=FLAT_CREDITS_PER_IMAGE,
    )
