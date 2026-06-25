from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from app.core.config import Settings, get_settings
from app.features.auth.dependencies import get_auth_service, get_current_user
from app.features.auth.models import User
from app.features.auth.schemas import (
    AuthenticatedUserResponse,
    LoginRequest,
    RegisterRequest,
    SessionResponse,
)
from app.features.auth.services import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


def set_session_cookie(
    response: Response,
    settings: Settings,
    access_token: str,
) -> None:
    response.set_cookie(
        key=settings.session_cookie_name,
        value=access_token,
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite=settings.session_cookie_samesite,
        max_age=settings.access_token_expire_minutes * 60,
        path="/",
    )


@router.post("/register", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    response: Response,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> SessionResponse:
    session = await auth_service.register(
        email=str(request.email),
        password=request.password,
        name=request.name,
    )
    set_session_cookie(response, settings, session.access_token)
    return SessionResponse(
        user=AuthenticatedUserResponse.from_user(session.user),
        granted_bonus_credits=session.granted_bonus_credits,
    )


@router.post("/login", response_model=SessionResponse, status_code=status.HTTP_200_OK)
async def login(
    request: LoginRequest,
    response: Response,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> SessionResponse:
    session = await auth_service.login_with_password(str(request.email), request.password)
    set_session_cookie(response, settings, session.access_token)
    return SessionResponse(user=AuthenticatedUserResponse.from_user(session.user))


@router.get("/me", response_model=SessionResponse)
async def get_authenticated_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> SessionResponse:
    return SessionResponse(user=AuthenticatedUserResponse.from_user(current_user))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    settings: Annotated[Settings, Depends(get_settings)],
) -> Response:
    response.status_code = status.HTTP_204_NO_CONTENT
    response.delete_cookie(
        key=settings.session_cookie_name,
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite=settings.session_cookie_samesite,
        path="/",
    )
    return response
