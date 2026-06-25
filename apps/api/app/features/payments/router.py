from typing import Annotated

from fastapi import APIRouter, Depends, Request

from app.features.auth.dependencies import get_current_user
from app.features.auth.models import User
from app.features.payments.dependencies import get_payment_service, get_webhook_service
from app.features.payments.schemas import (
    CheckoutSessionRequest,
    CheckoutSessionResponse,
    PortalSessionResponse,
)
from app.features.payments.services import PaymentService
from app.features.payments.webhook_service import WebhookService

router = APIRouter(prefix="/billing", tags=["billing"])


@router.post("/checkout-sessions", response_model=CheckoutSessionResponse)
async def create_checkout_session(
    request: CheckoutSessionRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    payment_service: Annotated[PaymentService, Depends(get_payment_service)],
) -> CheckoutSessionResponse:
    url = await payment_service.create_checkout_session(current_user, request.plan_code)
    return CheckoutSessionResponse(url=url)


@router.post("/portal-sessions", response_model=PortalSessionResponse)
async def create_portal_session(
    current_user: Annotated[User, Depends(get_current_user)],
    payment_service: Annotated[PaymentService, Depends(get_payment_service)],
) -> PortalSessionResponse:
    url = await payment_service.create_portal_session(current_user)
    return PortalSessionResponse(url=url)


@router.post("/webhooks/stripe")
async def stripe_webhook(
    request: Request,
    webhook_service: Annotated[WebhookService, Depends(get_webhook_service)],
) -> dict[str, bool]:
    # Public endpoint: authenticated by Stripe signature, not the session cookie.
    payload = await request.body()
    signature = request.headers.get("stripe-signature", "")
    await webhook_service.handle(payload=payload, signature=signature)
    return {"received": True}
