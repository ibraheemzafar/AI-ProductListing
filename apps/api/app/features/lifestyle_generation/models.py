from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database import Base


class GeneratedImage(Base):
    __tablename__ = "generated_images"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    product_id: Mapped[str] = mapped_column(String(36), ForeignKey("products.id"), index=True)
    listing_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("generated_listings.id"),
        index=True,
    )
    source_image_id: Mapped[str] = mapped_column(String(36), ForeignKey("product_images.id"))
    source_enhanced_image_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("enhanced_images.id"),
        nullable=True,
    )
    scene_preset: Mapped[str] = mapped_column(String(100))
    custom_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    prompt: Mapped[str] = mapped_column(Text)
    provider_name: Mapped[str] = mapped_column(String(100))
    storage_filename: Mapped[str] = mapped_column(String(255), unique=True)
    generated_image_url: Mapped[str] = mapped_column(String(2048))
    content_type: Mapped[str] = mapped_column(String(100))
    size_bytes: Mapped[int] = mapped_column(Integer)
    generation_time_ms: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(50), default="success")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )
