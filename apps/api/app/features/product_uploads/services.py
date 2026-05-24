from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.core.errors import AppError
from app.features.product_uploads.models import ProductImage
from app.features.product_uploads.repositories import ProductUploadRepository
from app.features.product_uploads.schemas import ProductImageListResponse, ProductUploadResponse
from app.shared.storage.provider import StorageProvider

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024
MAX_UPLOAD_FILES = 10
ALLOWED_CONTENT_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


class ProductUploadService:
    def __init__(
        self,
        repository: ProductUploadRepository,
        storage_provider: StorageProvider,
    ) -> None:
        self._repository = repository
        self._storage_provider = storage_provider

    async def upload_images(
        self,
        user_id: str,
        files: list[UploadFile],
    ) -> ProductUploadResponse:
        if not files:
            raise AppError("At least one image is required")
        if len(files) > MAX_UPLOAD_FILES:
            raise AppError(f"Upload up to {MAX_UPLOAD_FILES} images at a time")

        uploaded_storage_names: list[str] = []
        product_images: list[ProductImage] = []

        try:
            for file in files:
                content = await self._read_and_validate_file(file)
                storage_filename = self._generate_storage_filename(file)
                image_url = await self._storage_provider.upload(
                    file_name=storage_filename,
                    content=content,
                    content_type=file.content_type or "",
                )
                uploaded_storage_names.append(storage_filename)
                product_images.append(
                    ProductImage(
                        product_id="",
                        original_filename=file.filename or storage_filename,
                        storage_filename=storage_filename,
                        image_url=image_url,
                        content_type=file.content_type or "",
                        size_bytes=len(content),
                    ),
                )

            product, saved_images = await self._repository.create_product_with_images(
                user_id=user_id,
                images=product_images,
            )
            return ProductUploadResponse.from_models(product, saved_images)
        except Exception:
            for storage_name in uploaded_storage_names:
                await self._storage_provider.delete(storage_name)
            raise

    async def list_uploaded_images(self, user_id: str) -> ProductImageListResponse:
        images = await self._repository.list_images_for_user(user_id)
        return ProductImageListResponse.from_models(images)

    async def _read_and_validate_file(self, file: UploadFile) -> bytes:
        self._validate_file_name(file.filename)
        self._validate_content_type(file.content_type)

        content = await file.read()
        if len(content) > MAX_FILE_SIZE_BYTES:
            raise AppError("Image must be 10MB or smaller")
        if not content:
            raise AppError("Image file cannot be empty")
        self._validate_image_signature(content, file.content_type)
        return content

    def _validate_file_name(self, filename: str | None) -> None:
        if not filename:
            raise AppError("Image filename is required")
        if "/" in filename or "\\" in filename:
            raise AppError("Image filename cannot include path separators")
        extension = Path(filename).suffix.lower()
        if extension not in ALLOWED_EXTENSIONS:
            raise AppError("Only JPG, PNG, and WEBP images are supported")

    def _validate_content_type(self, content_type: str | None) -> None:
        if content_type not in ALLOWED_CONTENT_TYPES:
            raise AppError("Only JPG, PNG, and WEBP images are supported")

    def _generate_storage_filename(self, file: UploadFile) -> str:
        return f"{uuid4()}{ALLOWED_CONTENT_TYPES[file.content_type or '']}"

    def _validate_image_signature(self, content: bytes, content_type: str | None) -> None:
        if content_type == "image/jpeg" and content.startswith(b"\xff\xd8\xff"):
            return
        if content_type == "image/png" and content.startswith(b"\x89PNG\r\n\x1a\n"):
            return
        if (
            content_type == "image/webp"
            and len(content) >= 12
            and content[:4] == b"RIFF"
            and content[8:12] == b"WEBP"
        ):
            return
        raise AppError("Uploaded file content does not match a supported image format")
