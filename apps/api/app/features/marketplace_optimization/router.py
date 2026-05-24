from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.rate_limit import enforce_ai_rate_limit
from app.features.auth.dependencies import get_current_user
from app.features.auth.models import User
from app.features.marketplace_optimization.dependencies import (
    get_marketplace_optimization_service,
)
from app.features.marketplace_optimization.schemas import (
    MarketplaceOptimizationRequest,
    MarketplaceOptimizationResponse,
)
from app.features.marketplace_optimization.services import MarketplaceOptimizationService

router = APIRouter(prefix="/products", tags=["marketplace-optimization"])


@router.post(
    "/listings/{listing_id}/marketplace-optimizations",
    response_model=MarketplaceOptimizationResponse,
)
async def optimize_listing_for_marketplace(
    listing_id: str,
    payload: MarketplaceOptimizationRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    optimization_service: Annotated[
        MarketplaceOptimizationService,
        Depends(get_marketplace_optimization_service),
    ],
    _: Annotated[None, Depends(enforce_ai_rate_limit)],
) -> MarketplaceOptimizationResponse:
    return await optimization_service.optimize_listing(
        user_id=current_user.id,
        listing_id=listing_id,
        marketplace=payload.marketplace,
    )
