from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database import Base


class EnhancedImage(Base):
    __tablename__ = "enhanced_images"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    product_id: Mapped[str] = mapped_column(String(36), ForeignKey("products.id"), index=True)
    original_image_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("product_images.id"),
        index=True,
    )
    operation: Mapped[str] = mapped_column(String(50))
    provider_name: Mapped[str] = mapped_column(String(100))
    storage_filename: Mapped[str] = mapped_column(String(255), unique=True)
    enhanced_image_url: Mapped[str] = mapped_column(String(2048))
    content_type: Mapped[str] = mapped_column(String(100))
    size_bytes: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )
