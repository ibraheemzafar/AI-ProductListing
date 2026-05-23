from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile, status

from app.features.auth.dependencies import get_current_user
from app.features.auth.models import User
from app.features.product_uploads.dependencies import get_product_upload_service
from app.features.product_uploads.schemas import ProductImageListResponse, ProductUploadResponse
from app.features.product_uploads.services import ProductUploadService

router = APIRouter(prefix="/products", tags=["product-uploads"])


@router.post(
    "/images",
    response_model=ProductUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_product_images(
    current_user: Annotated[User, Depends(get_current_user)],
    upload_service: Annotated[ProductUploadService, Depends(get_product_upload_service)],
    files: Annotated[list[UploadFile], File()],
) -> ProductUploadResponse:
    return await upload_service.upload_images(user_id=current_user.id, files=files)


@router.get("/images", response_model=ProductImageListResponse)
async def list_product_images(
    current_user: Annotated[User, Depends(get_current_user)],
    upload_service: Annotated[ProductUploadService, Depends(get_product_upload_service)],
) -> ProductImageListResponse:
    return await upload_service.list_uploaded_images(user_id=current_user.id)

