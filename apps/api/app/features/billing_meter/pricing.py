from dataclasses import dataclass
from math import ceil
from typing import Protocol


@dataclass(frozen=True)
class UsageInput:
    """Provider usage used to price a request. Both None for non-token workflows."""

    input_tokens: int | None = None
    output_tokens: int | None = None


class CreditPricingPolicy(Protocol):
    def credits_for(self, usage: UsageInput) -> int:
        pass


class TokenWeightedPricingPolicy:
    """Prices a request from weighted token usage with a margin and a floor."""

    def __init__(
        self,
        *,
        input_weight: int,
        output_weight: int,
        tokens_per_credit: int,
        margin_multiplier: float,
        min_credits: int,
    ) -> None:
        self._input_weight = input_weight
        self._output_weight = output_weight
        self._tokens_per_credit = tokens_per_credit
        self._margin_multiplier = margin_multiplier
        self._min_credits = min_credits

    def credits_for(self, usage: UsageInput) -> int:
        weighted = (usage.input_tokens or 0) * self._input_weight + (
            usage.output_tokens or 0
        ) * self._output_weight
        scaled = ceil(weighted / self._tokens_per_credit * self._margin_multiplier)
        return max(self._min_credits, scaled)


class FlatPricingPolicy:
    """Prices every request at a flat credit cost (image workflows have no tokens)."""

    def __init__(self, *, flat_credits: int) -> None:
        self._flat_credits = flat_credits

    def credits_for(self, usage: UsageInput) -> int:
        return self._flat_credits
