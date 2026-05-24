from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.rate_limit import enforce_ai_rate_limit
from app.features.auth.dependencies import get_current_user
from app.features.auth.models import User
from app.features.listing_improvement.dependencies import get_listing_improvement_service
from app.features.listing_improvement.schemas import (
    AcceptListingVersionResponse,
    ListingImprovementResponse,
    ListingVersionHistoryResponse,
)
from app.features.listing_improvement.services import ListingImprovementService

router = APIRouter(prefix="/products", tags=["listing-improvement"])


@router.post("/listings/{listing_id}/improvements", response_model=ListingImprovementResponse)
async def improve_listing(
    listing_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    improvement_service: Annotated[
        ListingImprovementService,
        Depends(get_listing_improvement_service),
    ],
    _: Annotated[None, Depends(enforce_ai_rate_limit)],
) -> ListingImprovementResponse:
    return await improvement_service.improve_listing(
        user_id=current_user.id,
        listing_id=listing_id,
    )


@router.get("/listings/{listing_id}/versions", response_model=ListingVersionHistoryResponse)
async def list_listing_versions(
    listing_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    improvement_service: Annotated[
        ListingImprovementService,
        Depends(get_listing_improvement_service),
    ],
) -> ListingVersionHistoryResponse:
    return await improvement_service.list_versions(
        user_id=current_user.id,
        listing_id=listing_id,
    )


@router.post(
    "/listings/{listing_id}/versions/{version_id}/accept",
    response_model=AcceptListingVersionResponse,
)
async def accept_listing_version(
    listing_id: str,
    version_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    improvement_service: Annotated[
        ListingImprovementService,
        Depends(get_listing_improvement_service),
    ],
) -> AcceptListingVersionResponse:
    return await improvement_service.accept_version(
        user_id=current_user.id,
        listing_id=listing_id,
        version_id=version_id,
    )
