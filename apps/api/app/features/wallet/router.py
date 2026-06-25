from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.features.auth.dependencies import get_current_user
from app.features.auth.models import User
from app.features.wallet.dependencies import get_wallet_service
from app.features.wallet.schemas import (
    WalletResponse,
    WalletTransactionListResponse,
    WalletTransactionResponse,
)
from app.features.wallet.services import WalletService

router = APIRouter(prefix="/billing", tags=["billing"])


@router.get("/wallet", response_model=WalletResponse)
async def get_wallet(
    current_user: Annotated[User, Depends(get_current_user)],
    wallet_service: Annotated[WalletService, Depends(get_wallet_service)],
) -> WalletResponse:
    wallet = await wallet_service.get_wallet(current_user.id)
    return WalletResponse.from_model(wallet)


@router.get("/transactions", response_model=WalletTransactionListResponse)
async def list_wallet_transactions(
    current_user: Annotated[User, Depends(get_current_user)],
    wallet_service: Annotated[WalletService, Depends(get_wallet_service)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> WalletTransactionListResponse:
    transactions, total = await wallet_service.list_transactions(
        user_id=current_user.id,
        limit=limit,
        offset=offset,
    )
    return WalletTransactionListResponse(
        transactions=[WalletTransactionResponse.from_model(item) for item in transactions],
        total=total,
        limit=limit,
        offset=offset,
    )
