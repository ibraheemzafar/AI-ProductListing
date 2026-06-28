from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database import Base


class GeneratedListing(Base):
    __tablename__ = "generated_listings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    product_id: Mapped[str] = mapped_column(String(36), ForeignKey("products.id"), index=True)
    analysis_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("product_analysis_results.id"),
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255))
    short_description: Mapped[str] = mapped_column(Text)
    long_description: Mapped[str] = mapped_column(Text)
    seo_keywords: Mapped[list[str]] = mapped_column(JSON)
    product_tags: Mapped[list[str]] = mapped_column(JSON)
    raw_output: Mapped[dict[str, object]] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(50), default="generated")
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )
