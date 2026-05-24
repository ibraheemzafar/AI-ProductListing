from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.listing_exports.repositories import SQLAlchemyListingExportRepository
from app.features.listing_exports.services import ListingExportService
from app.infrastructure.database import get_database_session


def get_listing_export_service(
    database_session: Annotated[AsyncSession, Depends(get_database_session)],
) -> ListingExportService:
    return ListingExportService(
        repository=SQLAlchemyListingExportRepository(database_session),
    )
