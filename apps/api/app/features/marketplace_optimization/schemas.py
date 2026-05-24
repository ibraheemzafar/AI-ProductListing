from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.features.marketplace_optimization.models import MarketplaceOptimization

Marketplace = Literal["shopify", "amazon", "etsy", "daraz"]


class MarketplaceOptimizationRequest(BaseModel):
    marketplace: Marketplace


class MarketplaceOptimizationContent(BaseModel):
    optimized_title: str = Field(min_length=1, max_length=255)
    optimized_description: str = Field(min_length=1)
    bullet_points: list[str] = Field(min_length=1, max_length=8)
    keywords_tags: list[str] = Field(min_length=1, max_length=20)
    platform_notes: str = Field(min_length=1)


class MarketplaceOptimizationResponse(BaseModel):
    id: str
    listing_id: str
    product_id: str
    marketplace: Marketplace
    optimization: MarketplaceOptimizationContent
    created_at: datetime

    @classmethod
    def from_model(cls, optimization: MarketplaceOptimization) -> "MarketplaceOptimizationResponse":
        return cls(
            id=optimization.id,
            listing_id=optimization.listing_id,
            product_id=optimization.product_id,
            marketplace=optimization.marketplace,  # type: ignore[arg-type]
            optimization=MarketplaceOptimizationContent(
                optimized_title=optimization.optimized_title,
                optimized_description=optimization.optimized_description,
                bullet_points=optimization.bullet_points,
                keywords_tags=optimization.keywords_tags,
                platform_notes=optimization.platform_notes,
            ),
            created_at=optimization.created_at,
        )
