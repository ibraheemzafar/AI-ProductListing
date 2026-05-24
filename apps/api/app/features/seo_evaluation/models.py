from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database import Base


class SeoAnalysis(Base):
    __tablename__ = "seo_analysis"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    listing_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("generated_listings.id"),
        index=True,
    )
    product_id: Mapped[str] = mapped_column(String(36), ForeignKey("products.id"), index=True)
    seo_score: Mapped[int] = mapped_column(Integer)
    readability_score: Mapped[int] = mapped_column(Integer)
    keyword_optimization_feedback: Mapped[str] = mapped_column(Text)
    title_quality_feedback: Mapped[str] = mapped_column(Text)
    description_quality_feedback: Mapped[str] = mapped_column(Text)
    strengths: Mapped[list[str]] = mapped_column(JSON)
    weaknesses: Mapped[list[str]] = mapped_column(JSON)
    improvement_suggestions: Mapped[list[str]] = mapped_column(JSON)
    raw_output: Mapped[dict[str, object]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )
