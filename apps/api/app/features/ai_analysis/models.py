from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import JSON, BigInteger, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database import Base


class ProductAnalysisResult(Base):
    __tablename__ = "product_analysis_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    product_id: Mapped[str] = mapped_column(String(36), ForeignKey("products.id"), index=True)
    image_id: Mapped[str] = mapped_column(String(36), ForeignKey("product_images.id"), index=True)
    valid_product: Mapped[bool] = mapped_column(Boolean, default=True)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(255))
    product_type: Mapped[str] = mapped_column(String(255))
    color: Mapped[str] = mapped_column(String(255))
    material: Mapped[str] = mapped_column(String(255))
    style: Mapped[str] = mapped_column(String(255))
    visible_text_brand: Mapped[str] = mapped_column(String(255))
    target_audience: Mapped[str] = mapped_column(String(255))
    raw_attributes: Mapped[dict[str, str]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )


class AiRequestLog(Base):
    __tablename__ = "ai_request_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    product_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("products.id"),
        nullable=True,
    )
    image_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("product_images.id"),
        nullable=True,
    )
    workflow_name: Mapped[str] = mapped_column(String(100))
    model_name: Mapped[str] = mapped_column(String(100))
    prompt_version: Mapped[str] = mapped_column(String(50))
    input_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    latency_ms: Mapped[int] = mapped_column(Integer)
    success: Mapped[bool] = mapped_column(Boolean)
    status: Mapped[str] = mapped_column(String(50), default="success")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Credits debited from the wallet for this request, and the ledger entry it
    # produced. The wallet_transactions ledger remains the source of truth; these
    # are a convenience back-reference (no ORM-level FK to avoid cross-feature
    # mapper coupling — the DB enforces the FK).
    credits_charged: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    wallet_transaction_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )
