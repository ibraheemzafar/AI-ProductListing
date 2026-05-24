from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database import Base


class MarketplaceOptimization(Base):
    __tablename__ = "marketplace_optimizations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    listing_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("generated_listings.id"),
        index=True,
    )
    product_id: Mapped[str] = mapped_column(String(36), ForeignKey("products.id"), index=True)
    marketplace: Mapped[str] = mapped_column(String(50), index=True)
    optimized_title: Mapped[str] = mapped_column(String(255))
    optimized_description: Mapped[str] = mapped_column(Text)
    bullet_points: Mapped[list[str]] = mapped_column(JSON)
    keywords_tags: Mapped[list[str]] = mapped_column(JSON)
    platform_notes: Mapped[str] = mapped_column(Text)
    raw_output: Mapped[dict[str, object]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )
