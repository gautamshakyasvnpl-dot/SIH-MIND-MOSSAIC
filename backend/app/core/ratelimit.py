"""In-memory sliding-window rate limiting (stdlib, per-process).

Good enough for a single-instance demo; swap for Redis limits before
horizontal scaling. Keys are (scope, identity) with a minute window.
"""

import time
from collections import deque

from fastapi import HTTPException, Request, status

from app.core.security import get_current_user  # noqa: F401
from app.models import User

_buckets: dict[tuple[str, str], deque[float]] = {}


def check(key: tuple[str, str], limit_per_minute: int) -> None:
    now = time.monotonic()
    bucket = _buckets.setdefault(key, deque())
    window_start = now - 60.0
    while bucket and bucket[0] < window_start:
        bucket.popleft()
    if len(bucket) >= limit_per_minute:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests — slow down for a moment.",
        )
    bucket.append(now)


def _client_ip(request: Request) -> str:
    fwd = request.headers.get("x-forwarded-for")
    return (fwd.split(",")[0].strip() if fwd else None) or (
        request.client.host if request.client else "unknown"
    )


def ip_limited(limit_per_minute: int):
    from fastapi import Depends

    def dependency(request: Request) -> None:
        check(("ip", _client_ip(request)), limit_per_minute)

    return Depends(dependency)


def user_limited(limit_per_minute: int):
    from fastapi import Depends

    def dependency(request: Request, user: User = Depends(get_current_user)) -> None:
        check(("user", user.id), limit_per_minute)

    return Depends(dependency)
