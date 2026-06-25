from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.errors import AuthenticationError
from app.core.security import JwtSessionManager
from app.features.auth.models import User
from app.features.auth.repositories import SQLAlchemyUserRepository
from app.features.auth.services import AuthService, BcryptPasswordHasher
from app.features.wallet.dependencies import get_wallet_service
from app.features.wallet.services import WalletService
from app.infrastructure.database import get_database_session


def get_session_manager(settings: Annotated[Settings, Depends(get_settings)]) -> JwtSessionManager:
    return JwtSessionManager(
        secret_key=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
        expires_minutes=settings.access_token_expire_minutes,
    )


def get_password_hasher() -> BcryptPasswordHasher:
    return BcryptPasswordHasher()


def get_auth_service(
    database_session: Annotated[AsyncSession, Depends(get_database_session)],
    session_manager: Annotated[JwtSessionManager, Depends(get_session_manager)],
    password_hasher: Annotated[BcryptPasswordHasher, Depends(get_password_hasher)],
    settings: Annotated[Settings, Depends(get_settings)],
    wallet_service: Annotated[WalletService, Depends(get_wallet_service)],
) -> AuthService:
    return AuthService(
        user_repository=SQLAlchemyUserRepository(database_session),
        session_manager=session_manager,
        password_hasher=password_hasher,
        wallet_granter=wallet_service,
        signup_bonus_enabled=settings.signup_bonus_enabled,
    )


async def get_current_user(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> User:
    session_token = request.cookies.get(settings.session_cookie_name)
    if not session_token:
        raise AuthenticationError("Missing session")
    return await auth_service.get_current_user(session_token)
