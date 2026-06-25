from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from app.features.auth.models import User

PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 128


class RegisterRequest(BaseModel):
    email: EmailStr
    name: str | None = None
    password: str = Field(min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH)
    confirm_password: str = Field(min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH)

    @model_validator(mode="after")
    def validate_passwords(self) -> "RegisterRequest":
        if not any(char.isalpha() for char in self.password) or not any(
            char.isdigit() for char in self.password
        ):
            raise ValueError("Password must contain at least one letter and one number")
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self


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
    granted_bonus_credits: int | None = None


class AuthSession(BaseModel):
    user: User
    access_token: str
    expires_at: datetime
    granted_bonus_credits: int | None = None

    model_config = ConfigDict(arbitrary_types_allowed=True)
