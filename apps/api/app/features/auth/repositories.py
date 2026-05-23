from typing import Protocol

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.auth.models import User


class UserRepository(Protocol):
    async def get_by_id(self, user_id: str) -> User | None:
        pass

    async def get_by_email(self, email: str) -> User | None:
        pass

    async def create_user(self, email: str, password_hash: str, name: str | None) -> User:
        pass


class SQLAlchemyUserRepository:
    def __init__(self, database_session: AsyncSession) -> None:
        self._database_session = database_session

    async def get_by_id(self, user_id: str) -> User | None:
        result = await self._database_session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        result = await self._database_session.execute(
            select(User).where(User.email == email.lower()),
        )
        return result.scalar_one_or_none()

    async def create_user(self, email: str, password_hash: str, name: str | None) -> User:
        user = User(email=email.lower(), password_hash=password_hash, name=name, avatar_url=None)
        self._database_session.add(user)
        await self._database_session.commit()
        await self._database_session.refresh(user)
        return user
