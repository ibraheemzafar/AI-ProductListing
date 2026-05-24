from collections import defaultdict, deque
from time import monotonic
from typing import Annotated

from fastapi import Depends

from app.core.config import Settings, get_settings
from app.core.errors import RateLimitError
from app.features.auth.dependencies import get_current_user
from app.features.auth.models import User

WINDOW_SECONDS = 60.0


class InMemoryRateLimiter:
    def __init__(self) -> None:
        self._requests_by_key: dict[str, deque[float]] = defaultdict(deque)

    def check(self, key: str, limit: int) -> None:
        now = monotonic()
        requests = self._requests_by_key[key]
        while requests and now - requests[0] >= WINDOW_SECONDS:
            requests.popleft()
        if len(requests) >= limit:
            raise RateLimitError()
        requests.append(now)

    def reset(self) -> None:
        self._requests_by_key.clear()


ai_rate_limiter = InMemoryRateLimiter()


async def enforce_ai_rate_limit(
    current_user: Annotated[User, Depends(get_current_user)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> None:
    ai_rate_limiter.check(
        key=current_user.id,
        limit=settings.ai_rate_limit_requests_per_minute,
    )
