from typing import Annotated

from fastapi import APIRouter, Depends

from app.features.auth.dependencies import get_current_user
from app.features.auth.models import User
from app.features.subscriptions.dependencies import get_subscription_service
from app.features.subscriptions.schemas import (
    PlanListResponse,
    SubscriptionPlanResponse,
    UserSubscriptionResponse,
)
from app.features.subscriptions.services import SubscriptionService

router = APIRouter(prefix="/billing", tags=["billing"])


@router.get("/plans", response_model=PlanListResponse)
async def list_plans(
    subscription_service: Annotated[SubscriptionService, Depends(get_subscription_service)],
) -> PlanListResponse:
    plans = await subscription_service.list_active_plans()
    return PlanListResponse(plans=[SubscriptionPlanResponse.from_model(plan) for plan in plans])


@router.get("/subscription", response_model=UserSubscriptionResponse | None)
async def get_current_subscription(
    current_user: Annotated[User, Depends(get_current_user)],
    subscription_service: Annotated[SubscriptionService, Depends(get_subscription_service)],
) -> UserSubscriptionResponse | None:
    row = await subscription_service.get_current_subscription(current_user.id)
    if row is None:
        return None
    subscription, plan = row
    return UserSubscriptionResponse.from_models(subscription, plan)
