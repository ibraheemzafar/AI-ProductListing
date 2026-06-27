from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.core.security import JwtSessionManager
from app.features.auth.dependencies import get_auth_service
from app.features.auth.models import User
from app.features.auth.services import AuthService
from app.main import create_app


class PlainTextPasswordHasher:
    def hash(self, password: str) -> str:
        return f"hashed:{password}"

    def verify(self, password: str, password_hash: str) -> bool:
        return password_hash == f"hashed:{password}"


class InMemoryUserRepository:
    def __init__(self) -> None:
        self.users_by_id: dict[str, User] = {}

    async def get_by_id(self, user_id: str) -> User | None:
        return self.users_by_id.get(user_id)

    async def get_by_email(self, email: str) -> User | None:
        return next((user for user in self.users_by_id.values() if user.email == email), None)

    async def create_user(self, email: str, password_hash: str, name: str | None) -> User:
        user = User(
            id="user-1",
            email=email,
            name=name,
            avatar_url=None,
            password_hash=password_hash,
        )
        self.users_by_id[user.id] = user
        return user


@pytest.fixture
def client() -> Iterator[TestClient]:
    settings = get_settings()
    user_repository = InMemoryUserRepository()
    session_manager = JwtSessionManager(
        secret_key=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
        expires_minutes=settings.access_token_expire_minutes,
    )
    auth_service = AuthService(
        user_repository=user_repository,
        session_manager=session_manager,
        password_hasher=PlainTextPasswordHasher(),
    )
    app = create_app()
    app.dependency_overrides[get_auth_service] = lambda: auth_service

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def test_register_sets_session_cookie(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "seller@example.com",
            "password": "password123",
            "confirm_password": "password123",
            "name": "Test Seller",
        },
    )

    assert response.status_code == 201
    assert response.json()["user"]["email"] == "seller@example.com"
    assert "apl_session" in response.cookies


def test_login_sets_session_cookie(client: TestClient) -> None:
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "seller@example.com",
            "password": "password123",
            "confirm_password": "password123",
            "name": "Test Seller",
        },
    )

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "seller@example.com", "password": "password123"},
    )

    assert response.status_code == 200
    assert "apl_session" in response.cookies


def test_me_returns_authenticated_user(client: TestClient) -> None:
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "seller@example.com",
            "password": "password123",
            "confirm_password": "password123",
            "name": "Test Seller",
        },
    )
    client.cookies.set("apl_session", register_response.cookies["apl_session"])

    response = client.get("/api/v1/auth/me")

    assert response.status_code == 200
    assert response.json()["user"]["id"] == "user-1"


def test_logout_clears_session_cookie(client: TestClient) -> None:
    response = client.post("/api/v1/auth/logout")

    assert response.status_code == 204
    assert response.headers["set-cookie"].startswith("apl_session=")


def test_me_rejects_missing_session(client: TestClient) -> None:
    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "authentication_failed"


def test_login_rejects_invalid_password(client: TestClient) -> None:
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "seller@example.com",
            "password": "password123",
            "confirm_password": "password123",
            "name": "Test Seller",
        },
    )

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "seller@example.com", "password": "wrong-password"},
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "authentication_failed"
