from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.rate_limit import enforce_ai_rate_limit
from app.features.auth.dependencies import get_current_user
from app.features.auth.models import User
from app.features.image_enhancement.dependencies import get_image_enhancement_service
from app.features.image_enhancement.schemas import (
    EnhancedImageResponse,
    ImageEnhancementRequest,
)
from app.features.image_enhancement.services import ImageEnhancementService

router = APIRouter(prefix="/products", tags=["image-enhancement"])


@router.post("/listings/{listing_id}/image-enhancements", response_model=EnhancedImageResponse)
async def enhance_listing_image(
    listing_id: str,
    payload: ImageEnhancementRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    enhancement_service: Annotated[
        ImageEnhancementService,
        Depends(get_image_enhancement_service),
    ],
    _: Annotated[None, Depends(enforce_ai_rate_limit)],
) -> EnhancedImageResponse:
    return await enhancement_service.enhance_listing_image(
        user_id=current_user.id,
        listing_id=listing_id,
        operation=payload.operation,
    )
