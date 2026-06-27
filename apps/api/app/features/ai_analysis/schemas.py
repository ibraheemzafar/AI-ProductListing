from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.features.ai_analysis.models import ProductAnalysisResult


class ProductAttributes(BaseModel):
    valid_product: bool = True
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    reason: str | None = Field(default=None, max_length=500)
    category: str = Field(default="unknown", min_length=1, max_length=255)
    product_type: str = Field(default="unknown", min_length=1, max_length=255)
    color: str = Field(default="unknown", min_length=1, max_length=255)
    material: str = Field(default="unknown", min_length=1, max_length=255)
    style: str = Field(default="unknown", min_length=1, max_length=255)
    visible_text_brand: str = Field(default="unknown", min_length=1, max_length=255)
    target_audience: str = Field(default="unknown", min_length=1, max_length=255)

    @model_validator(mode="after")
    def validate_product_fields(self) -> "ProductAttributes":
        if self.valid_product:
            required_fields = {
                "category": self.category,
                "product_type": self.product_type,
                "color": self.color,
                "material": self.material,
                "style": self.style,
                "visible_text_brand": self.visible_text_brand,
                "target_audience": self.target_audience,
            }
            missing = [name for name, value in required_fields.items() if not value.strip()]
            if missing:
                raise ValueError(f"Valid product analysis missing fields: {', '.join(missing)}")
        return self


class ProductAnalysisResponse(BaseModel):
    id: str
    product_id: str
    image_id: str
    attributes: ProductAttributes
    valid_product: bool
    confidence: float
    reason: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_model(cls, analysis: ProductAnalysisResult) -> "ProductAnalysisResponse":
        return cls(
            id=analysis.id,
            product_id=analysis.product_id,
            image_id=analysis.image_id,
            attributes=ProductAttributes(
                valid_product=analysis.valid_product,
                confidence=analysis.confidence,
                reason=analysis.reason,
                category=analysis.category,
                product_type=analysis.product_type,
                color=analysis.color,
                material=analysis.material,
                style=analysis.style,
                visible_text_brand=analysis.visible_text_brand,
                target_audience=analysis.target_audience,
            ),
            valid_product=analysis.valid_product,
            confidence=analysis.confidence,
            reason=analysis.reason,
            created_at=analysis.created_at,
        )
