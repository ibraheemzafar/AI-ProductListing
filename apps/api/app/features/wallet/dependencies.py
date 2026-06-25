from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.wallet.repositories import SQLAlchemyWalletRepository
from app.features.wallet.services import WalletService
from app.infrastructure.database import get_database_session


def get_wallet_service(
    database_session: Annotated[AsyncSession, Depends(get_database_session)],
) -> WalletService:
    return WalletService(repository=SQLAlchemyWalletRepository(database_session))
