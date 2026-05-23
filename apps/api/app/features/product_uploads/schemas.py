from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.features.product_uploads.models import Product, ProductImage


class UploadedImageResponse(BaseModel):
    id: str
    product_id: str
    original_filename: str
    image_url: str
    content_type: str
    size_bytes: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_model(cls, image: ProductImage) -> "UploadedImageResponse":
        return cls(
            id=image.id,
            product_id=image.product_id,
            original_filename=image.original_filename,
            image_url=image.image_url,
            content_type=image.content_type,
            size_bytes=image.size_bytes,
            created_at=image.created_at,
        )


class ProductUploadResponse(BaseModel):
    product_id: str
    images: list[UploadedImageResponse]

    @classmethod
    def from_models(
        cls,
        product: Product,
        images: list[ProductImage],
    ) -> "ProductUploadResponse":
        return cls(
            product_id=product.id,
            images=[UploadedImageResponse.from_model(image) for image in images],
        )


class ProductImageListResponse(BaseModel):
    images: list[UploadedImageResponse]

    @classmethod
    def from_models(cls, images: list[ProductImage]) -> "ProductImageListResponse":
        return cls(images=[UploadedImageResponse.from_model(image) for image in images])

