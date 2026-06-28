from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
from fastapi import HTTPException, status

from app.config import Settings


def create_session_token(settings: Settings) -> dict[str, str]:
    session_id = str(uuid4())
    expires_at = datetime.now(UTC) + timedelta(seconds=settings.jwt_ttl_seconds)
    token = jwt.encode(
        {"sub": session_id, "exp": expires_at, "iat": datetime.now(UTC)},
        settings.jwt_secret,
        algorithm="HS256",
    )
    return {
        "session_id": session_id,
        "token": token,
        "expires_at": expires_at.isoformat(),
    }


def verify_bearer_token(settings: Settings, authorization: str | None) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    token = authorization.removeprefix("Bearer ").strip()
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc
    session_id = payload.get("sub")
    if not isinstance(session_id, str) or not session_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject")
    return session_id
