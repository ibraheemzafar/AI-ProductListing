from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database import Base


class BillingCustomer(Base):
    __tablename__ = "billing_customers"

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), primary_key=True)
    stripe_customer_id: Mapped[str] = mapped_column(String(255), unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )


class ProcessedWebhookEvent(Base):
    __tablename__ = "processed_webhook_events"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)  # provider event id
    provider: Mapped[str] = mapped_column(String(50))
    event_type: Mapped[str] = mapped_column(String(100))
    processed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )
