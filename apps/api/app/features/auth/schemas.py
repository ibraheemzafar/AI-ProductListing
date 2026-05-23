from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.features.auth.models import User


class RegisterRequest(BaseModel):
    email: EmailStr
    name: str | None = None
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class AuthenticatedUserResponse(BaseModel):
    id: str
    email: EmailStr
    name: str | None
    avatar_url: str | None

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_user(cls, user: User) -> "AuthenticatedUserResponse":
        return cls(
            id=user.id,
            email=user.email,
            name=user.name,
            avatar_url=user.avatar_url,
        )


class SessionResponse(BaseModel):
    user: AuthenticatedUserResponse


class AuthSession(BaseModel):
    user: User
    access_token: str
    expires_at: datetime

    model_config = ConfigDict(arbitrary_types_allowed=True)
