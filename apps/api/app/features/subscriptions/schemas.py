from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict

from app.features.subscriptions.models import SubscriptionPlan, UserSubscription


class PlanType(str, Enum):
    SUBSCRIPTION = "subscription"
    TOPUP = "topup"


class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    INCOMPLETE = "incomplete"
    INCOMPLETE_EXPIRED = "incomplete_expired"
    TRIALING = "trialing"
    UNPAID = "unpaid"


class SubscriptionPlanResponse(BaseModel):
    id: str
    code: str
    name: str
    description: str | None
    plan_type: str
    credit_allowance: int
    price_cents: int
    currency: str
    interval: str
    rollover: bool

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_model(cls, plan: SubscriptionPlan) -> "SubscriptionPlanResponse":
        return cls(
            id=plan.id,
            code=plan.code,
            name=plan.name,
            description=plan.description,
            plan_type=plan.plan_type,
            credit_allowance=plan.credit_allowance,
            price_cents=plan.price_cents,
            currency=plan.currency,
            interval=plan.interval,
            rollover=plan.rollover,
        )


class PlanListResponse(BaseModel):
    plans: list[SubscriptionPlanResponse]


class UserSubscriptionResponse(BaseModel):
    id: str
    status: str
    plan: SubscriptionPlanResponse
    current_period_end: datetime | None
    cancel_at_period_end: bool

    @classmethod
    def from_models(
        cls,
        subscription: UserSubscription,
        plan: SubscriptionPlan,
    ) -> "UserSubscriptionResponse":
        return cls(
            id=subscription.id,
            status=subscription.status,
            plan=SubscriptionPlanResponse.from_model(plan),
            current_period_end=subscription.current_period_end,
            cancel_at_period_end=subscription.cancel_at_period_end,
        )
