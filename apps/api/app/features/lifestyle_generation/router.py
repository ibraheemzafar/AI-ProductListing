from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import Response

from app.core.rate_limit import enforce_ai_rate_limit
from app.features.auth.dependencies import get_current_user
from app.features.auth.models import User
from app.features.lifestyle_generation.dependencies import get_lifestyle_generation_service
from app.features.lifestyle_generation.schemas import (
    GeneratedImageGalleryResponse,
    GeneratedImageResponse,
    LifestyleGenerationRequest,
)
from app.features.lifestyle_generation.services import LifestyleGenerationService

router = APIRouter(prefix="/products", tags=["lifestyle-generation"])


@router.post("/listings/{listing_id}/generated-images", response_model=GeneratedImageResponse)
async def generate_lifestyle_scene(
    listing_id: str,
    payload: LifestyleGenerationRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    generation_service: Annotated[
        LifestyleGenerationService,
        Depends(get_lifestyle_generation_service),
    ],
    _: Annotated[None, Depends(enforce_ai_rate_limit)],
) -> GeneratedImageResponse:
    return await generation_service.generate_lifestyle_scene(
        user_id=current_user.id,
        listing_id=listing_id,
        category=payload.category,
        custom_prompt=payload.custom_prompt,
    )


@router.get(
    "/listings/{listing_id}/generated-images",
    response_model=GeneratedImageGalleryResponse,
)
async def list_lifestyle_scenes(
    listing_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    generation_service: Annotated[
        LifestyleGenerationService,
        Depends(get_lifestyle_generation_service),
    ],
) -> GeneratedImageGalleryResponse:
    return await generation_service.list_generated_images(
        user_id=current_user.id,
        listing_id=listing_id,
    )


@router.get("/listings/{listing_id}/generated-images/{image_id}/download")
async def download_generated_image(
    listing_id: str,
    image_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    generation_service: Annotated[
        LifestyleGenerationService,
        Depends(get_lifestyle_generation_service),
    ],
) -> Response:
    content, media_type, filename = await generation_service.download_generated_image(
        user_id=current_user.id,
        listing_id=listing_id,
        image_id=image_id,
    )
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.delete("/listings/{listing_id}/generated-images/{image_id}", status_code=204)
async def delete_generated_image(
    listing_id: str,
    image_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    generation_service: Annotated[
        LifestyleGenerationService,
        Depends(get_lifestyle_generation_service),
    ],
) -> Response:
    await generation_service.delete_generated_image(
        user_id=current_user.id,
        listing_id=listing_id,
        image_id=image_id,
    )
    return Response(status_code=204)
