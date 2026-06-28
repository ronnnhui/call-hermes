import time
from collections import defaultdict, deque
from typing import Deque

from fastapi import HTTPException, Request, status

from app.config import Settings


_buckets: dict[str, Deque[float]] = defaultdict(deque)


def enforce_auth_rate_limit(request: Request, settings: Settings) -> None:
    client = request.client.host if request.client else "unknown"
    now = time.monotonic()
    window = settings.auth_rate_limit_window_seconds
    bucket = _buckets[client]
    while bucket and now - bucket[0] > window:
        bucket.popleft()
    if len(bucket) >= settings.auth_rate_limit_requests:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many auth attempts. Please wait and try again.",
        )
    bucket.append(now)
