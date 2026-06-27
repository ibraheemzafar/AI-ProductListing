from app.core.errors import AppError, NotFoundError
from app.features.auth.models import User
from app.features.payments.models import BillingCustomer
from app.features.payments.repositories import PaymentsRepository
from app.features.subscriptions.models import SubscriptionPlan
from app.features.subscriptions.services import SubscriptionService
from app.shared.payments.provider import LineItem, PaymentProvider


class PaymentService:
    """Creates Stripe Checkout and Billing Portal sessions for the current user.

    Credits are never granted here — that happens on webhook confirmation (Phase 6).
    """

    def __init__(
        self,
        repository: PaymentsRepository,
        payment_provider: PaymentProvider,
        subscription_service: SubscriptionService,
        success_url: str,
        cancel_url: str,
        portal_return_url: str,
    ) -> None:
        self._repository = repository
        self._payment_provider = payment_provider
        self._subscription_service = subscription_service
        self._success_url = success_url
        self._cancel_url = cancel_url
        self._portal_return_url = portal_return_url

    async def create_checkout_session(self, user: User, plan_code: str) -> str:
        plan = await self._subscription_service.get_plan_by_code(plan_code)
        if plan is None or not plan.is_active:
            raise NotFoundError("Subscription plan was not found")

        customer_id = (
            ""
            if self._payment_provider.provider_code == "paddle"
            else await self._ensure_customer(user)
        )
        mode = "subscription" if plan.plan_type == "subscription" else "payment"
        metadata = {
            "user_id": user.id,
            "plan_id": plan.id,
            "plan_code": plan.code,
            "plan_type": plan.plan_type,
        }
        session = await self._payment_provider.create_checkout_session(
            mode=mode,
            line_items=[self._line_item(plan)],
            success_url=self._success_url,
            cancel_url=self._cancel_url,
            customer_id=customer_id,
            client_reference_id=user.id,
            metadata=metadata,
            subscription_metadata=metadata if mode == "subscription" else None,
        )
        return session.url

    async def create_portal_session(self, user: User) -> str:
        subscription = await self._subscription_service.get_current_subscription(user.id)
        if subscription is None:
            raise AppError("No active subscription is available to manage yet")

        customer_id = await self._ensure_customer(user)
        session = await self._payment_provider.create_billing_portal_session(
            customer_id=customer_id,
            return_url=self._portal_return_url,
        )
        return session.url

    async def _ensure_customer(self, user: User) -> str:
        existing = await self._repository.get_customer(user.id)
        if existing is not None:
            existing_customer_id = self._customer_id(existing)
            if existing_customer_id is not None:
                return existing_customer_id

        customer_id = await self._payment_provider.create_customer(
            email=user.email,
            metadata={"user_id": user.id},
        )
        saved = await self._repository.save_customer(
            user.id,
            self._payment_provider.provider_code,
            customer_id,
        )
        saved_customer_id = self._customer_id(saved)
        if saved_customer_id is None:
            raise AppError("Payment customer could not be saved")
        return saved_customer_id

    def _customer_id(self, customer: BillingCustomer) -> str | None:
        if self._payment_provider.provider_code == "stripe":
            return customer.stripe_customer_id
        if self._payment_provider.provider_code == "paddle":
            return customer.paddle_customer_id
        raise AppError("Unsupported payment provider")

    def _line_item(self, plan: SubscriptionPlan) -> LineItem:
        if self._payment_provider.provider_code == "paddle":
            return self._paddle_line_item(plan)

        # Prefer a pre-created Stripe Price; otherwise build an inline price so the
        # checkout works before Stripe products are configured in the dashboard.
        if plan.stripe_price_id:
            return {"price": plan.stripe_price_id, "quantity": 1}

        price_data: dict[str, object] = {
            "currency": plan.currency,
            "product_data": {"name": plan.name},
            "unit_amount": plan.price_cents,
        }
        if plan.plan_type == "subscription":
            if plan.interval not in {"month", "year"}:
                raise AppError("Subscription plans require a monthly or yearly interval")
            price_data["recurring"] = {"interval": plan.interval}
        return {"price_data": price_data, "quantity": 1}

    def _paddle_line_item(self, plan: SubscriptionPlan) -> LineItem:
        if plan.paddle_price_id:
            return {"price_id": plan.paddle_price_id, "quantity": 1}

        price: dict[str, object] = {
            "description": f"{plan.name} plan",
            "name": plan.name,
            "tax_mode": "account_setting",
            "unit_price": {
                "amount": str(plan.price_cents),
                "currency_code": plan.currency.upper(),
            },
            "product": {
                "name": plan.name,
                "description": plan.description,
                "tax_category": "saas",
            },
        }
        if plan.plan_type == "subscription":
            if plan.interval not in {"month", "year"}:
                raise AppError("Paddle subscription plans require a monthly or yearly interval")
            price["billing_cycle"] = {"interval": plan.interval, "frequency": 1}
        else:
            price["billing_cycle"] = None
        return {"price": price, "quantity": 1}
