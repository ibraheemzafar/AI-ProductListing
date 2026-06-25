from typing import Any, Protocol, cast

from passlib.context import CryptContext  # type: ignore[import-untyped]

from app.core.errors import AppError, AuthenticationError
from app.core.security import JwtSessionManager
from app.features.auth.models import User
from app.features.auth.repositories import UserRepository
from app.features.auth.schemas import AuthSession


class PasswordHasher(Protocol):
    def hash(self, password: str) -> str:
        pass

    def verify(self, password: str, password_hash: str) -> bool:
        pass


class WalletGranter(Protocol):
    """Narrow interface auth needs from the wallet domain (ISP/DIP)."""

    async def grant_signup_bonus(self, user_id: str) -> int | None:
        pass


class BcryptPasswordHasher:
    def __init__(self) -> None:
        self._context: Any = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def hash(self, password: str) -> str:
        return cast(str, self._context.hash(password))

    def verify(self, password: str, password_hash: str) -> bool:
        return cast(bool, self._context.verify(password, password_hash))


class AuthService:
    def __init__(
        self,
        user_repository: UserRepository,
        session_manager: JwtSessionManager,
        password_hasher: PasswordHasher,
        wallet_granter: WalletGranter | None = None,
        signup_bonus_enabled: bool = False,
    ) -> None:
        self._user_repository = user_repository
        self._session_manager = session_manager
        self._password_hasher = password_hasher
        self._wallet_granter = wallet_granter
        self._signup_bonus_enabled = signup_bonus_enabled

    async def register(self, email: str, password: str, name: str | None) -> AuthSession:
        normalized_email = email.lower()
        existing_user = await self._user_repository.get_by_email(normalized_email)
        if existing_user is not None:
            raise AppError("An account with this email already exists")

        user = await self._user_repository.create_user(
            email=normalized_email,
            password_hash=self._password_hasher.hash(password),
            name=name,
        )

        granted_bonus_credits: int | None = None
        if self._signup_bonus_enabled and self._wallet_granter is not None:
            granted_bonus_credits = await self._wallet_granter.grant_signup_bonus(user.id)

        return self._create_session(user, granted_bonus_credits=granted_bonus_credits)

    async def login_with_password(self, email: str, password: str) -> AuthSession:
        user = await self._user_repository.get_by_email(email.lower())
        if user is None:
            raise AuthenticationError("Invalid email or password")

        if not self._password_hasher.verify(password, user.password_hash):
            raise AuthenticationError("Invalid email or password")

        return self._create_session(user)

    def _create_session(
        self,
        user: User,
        granted_bonus_credits: int | None = None,
    ) -> AuthSession:
        access_token, expires_at = self._session_manager.create_access_token(
            subject=user.id,
            email=user.email,
        )
        return AuthSession(
            user=user,
            access_token=access_token,
            expires_at=expires_at,
            granted_bonus_credits=granted_bonus_credits,
        )

    async def get_current_user(self, access_token: str) -> User:
        user_id = self._session_manager.verify_access_token(access_token)
        user = await self._user_repository.get_by_id(user_id)
        if user is None:
            raise AuthenticationError("Session user was not found")
        return user
