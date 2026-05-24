from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.features.ai_analysis.models import ProductAnalysisResult


class ProductAttributes(BaseModel):
    category: str = Field(min_length=1, max_length=255)
    product_type: str = Field(min_length=1, max_length=255)
    color: str = Field(min_length=1, max_length=255)
    material: str = Field(min_length=1, max_length=255)
    style: str = Field(min_length=1, max_length=255)
    visible_text_brand: str = Field(min_length=1, max_length=255)
    target_audience: str = Field(min_length=1, max_length=255)


class ProductAnalysisResponse(BaseModel):
    id: str
    product_id: str
    image_id: str
    attributes: ProductAttributes
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_model(cls, analysis: ProductAnalysisResult) -> "ProductAnalysisResponse":
        return cls(
            id=analysis.id,
            product_id=analysis.product_id,
            image_id=analysis.image_id,
            attributes=ProductAttributes(
                category=analysis.category,
                product_type=analysis.product_type,
                color=analysis.color,
                material=analysis.material,
                style=analysis.style,
                visible_text_brand=analysis.visible_text_brand,
                target_audience=analysis.target_audience,
            ),
            created_at=analysis.created_at,
        )
