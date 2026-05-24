from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database import Base


class ListingVersion(Base):
    __tablename__ = "listing_versions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    listing_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("generated_listings.id"),
        index=True,
    )
    product_id: Mapped[str] = mapped_column(String(36), ForeignKey("products.id"), index=True)
    version_number: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(255))
    short_description: Mapped[str] = mapped_column(Text)
    long_description: Mapped[str] = mapped_column(Text)
    seo_keywords: Mapped[list[str]] = mapped_column(JSON)
    product_tags: Mapped[list[str]] = mapped_column(JSON)
    source: Mapped[str] = mapped_column(String(50), default="ai_improvement")
    is_accepted: Mapped[bool] = mapped_column(Boolean, default=False)
    raw_output: Mapped[dict[str, object]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
