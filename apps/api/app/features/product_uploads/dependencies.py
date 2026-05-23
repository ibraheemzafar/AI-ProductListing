from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.product_uploads.repositories import SQLAlchemyProductUploadRepository
from app.features.product_uploads.services import ProductUploadService
from app.infrastructure.database import get_database_session
from app.shared.storage.dependencies import get_storage_provider
from app.shared.storage.provider import StorageProvider


def get_product_upload_service(
    database_session: Annotated[AsyncSession, Depends(get_database_session)],
    storage_provider: Annotated[StorageProvider, Depends(get_storage_provider)],
) -> ProductUploadService:
    return ProductUploadService(
        repository=SQLAlchemyProductUploadRepository(database_session),
        storage_provider=storage_provider,
    )

