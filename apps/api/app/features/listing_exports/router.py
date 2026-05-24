from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import Response

from app.features.auth.dependencies import get_current_user
from app.features.auth.models import User
from app.features.listing_exports.dependencies import get_listing_export_service
from app.features.listing_exports.schemas import ListingJsonExportResponse
from app.features.listing_exports.services import ListingExportService

router = APIRouter(prefix="/products", tags=["listing-exports"])


@router.get("/listings/{listing_id}/export/json", response_model=ListingJsonExportResponse)
async def export_listing_as_json(
    listing_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    export_service: Annotated[ListingExportService, Depends(get_listing_export_service)],
) -> ListingJsonExportResponse:
    return await export_service.export_listing_as_json(
        user_id=current_user.id,
        listing_id=listing_id,
    )


@router.get("/listings/{listing_id}/export/shopify.csv")
async def export_listing_as_shopify_csv(
    listing_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    export_service: Annotated[ListingExportService, Depends(get_listing_export_service)],
) -> Response:
    export = await export_service.export_listing_as_shopify_csv(
        user_id=current_user.id,
        listing_id=listing_id,
    )
    return Response(
        content=export.content,
        media_type=export.media_type,
        headers={"Content-Disposition": f'attachment; filename="{export.filename}"'},
    )
