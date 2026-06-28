from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status

from app.core.rate_limit import enforce_ai_rate_limit
from app.features.auth.dependencies import get_current_user
from app.features.auth.models import User
from app.features.listing_generation.dependencies import get_listing_generation_service
from app.features.listing_generation.schemas import (
    GeneratedListingResponse,
    ListingDetailResponse,
    ListingHistoryResponse,
)
from app.features.listing_generation.services import ListingGenerationService
from app.features.listing_improvement.schemas import ListingVersionResponse

router = APIRouter(prefix="/products", tags=["listing-generation"])


@router.post("/analysis/{analysis_id}/listing", response_model=GeneratedListingResponse)
async def generate_listing(
    analysis_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    listing_service: Annotated[
        ListingGenerationService,
        Depends(get_listing_generation_service),
    ],
    _: Annotated[None, Depends(enforce_ai_rate_limit)],
) -> GeneratedListingResponse:
    return await listing_service.generate_listing(
        user_id=current_user.id,
        analysis_id=analysis_id,
    )


@router.post("/listings/{listing_id}/regenerate", response_model=ListingVersionResponse)
async def regenerate_listing(
    listing_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    listing_service: Annotated[
        ListingGenerationService,
        Depends(get_listing_generation_service),
    ],
    _: Annotated[None, Depends(enforce_ai_rate_limit)],
) -> ListingVersionResponse:
    return await listing_service.regenerate_listing(
        user_id=current_user.id,
        listing_id=listing_id,
    )


@router.get("/analysis/{analysis_id}/listings", response_model=list[GeneratedListingResponse])
async def list_listings_for_analysis(
    analysis_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    listing_service: Annotated[
        ListingGenerationService,
        Depends(get_listing_generation_service),
    ],
) -> list[GeneratedListingResponse]:
    return await listing_service.list_existing_listings(
        user_id=current_user.id,
        analysis_id=analysis_id,
    )


@router.get("/listings", response_model=ListingHistoryResponse)
async def list_generated_listings(
    current_user: Annotated[User, Depends(get_current_user)],
    listing_service: Annotated[
        ListingGenerationService,
        Depends(get_listing_generation_service),
    ],
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ListingHistoryResponse:
    return await listing_service.list_generated_listings(
        user_id=current_user.id,
        limit=limit,
        offset=offset,
    )


@router.get("/listings/{listing_id}", response_model=ListingDetailResponse)
async def get_generated_listing_detail(
    listing_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    listing_service: Annotated[
        ListingGenerationService,
        Depends(get_listing_generation_service),
    ],
) -> ListingDetailResponse:
    return await listing_service.get_generated_listing_detail(
        user_id=current_user.id,
        listing_id=listing_id,
    )


@router.delete("/listings/{listing_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_generated_listing(
    listing_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    listing_service: Annotated[
        ListingGenerationService,
        Depends(get_listing_generation_service),
    ],
) -> Response:
    await listing_service.delete_generated_listing(
        user_id=current_user.id,
        listing_id=listing_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


listing_alias_router = APIRouter(prefix="/listings", tags=["listing-generation"])


@listing_alias_router.delete("/{listing_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_generated_listing_alias(
    listing_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    listing_service: Annotated[
        ListingGenerationService,
        Depends(get_listing_generation_service),
    ],
) -> Response:
    await listing_service.delete_generated_listing(
        user_id=current_user.id,
        listing_id=listing_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
