from datetime import UTC, datetime, timedelta

import jwt
from jwt import InvalidTokenError

from app.core.errors import AuthenticationError


class JwtSessionManager:
    def __init__(self, secret_key: str, algorithm: str, expires_minutes: int) -> None:
        self._secret_key = secret_key
        self._algorithm = algorithm
        self._expires_minutes = expires_minutes

    def create_access_token(self, subject: str, email: str) -> tuple[str, datetime]:
        expires_at = datetime.now(UTC) + timedelta(minutes=self._expires_minutes)
        payload = {
            "sub": subject,
            "email": email,
            "exp": expires_at,
            "iat": datetime.now(UTC),
        }
        token = jwt.encode(payload, self._secret_key, algorithm=self._algorithm)
        return token, expires_at

    def verify_access_token(self, token: str) -> str:
        try:
            payload = jwt.decode(token, self._secret_key, algorithms=[self._algorithm])
        except InvalidTokenError as error:
            raise AuthenticationError("Invalid or expired session") from error

        subject = payload.get("sub")
        if not isinstance(subject, str) or not subject:
            raise AuthenticationError("Invalid session subject")
        return subject

