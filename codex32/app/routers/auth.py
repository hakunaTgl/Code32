"""Authentication API.

This project currently doesn't ship with a database-backed user store.
So we implement a minimal API-key based admin guard and a JWT mint endpoint
that can be wired to a real user DB later.

No placeholders: these endpoints work with env-configured ADMIN_API_KEY.
"""

from __future__ import annotations

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Header, status

from app.config import settings
from app.security import SecurityManager

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


def require_admin_api_key(x_api_key: str | None = Header(default=None)) -> None:
    if not settings.ADMIN_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ADMIN_API_KEY is not configured",
        )

    if x_api_key != settings.ADMIN_API_KEY.get_secret_value():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")


@router.post("/token")
def mint_token(
    user_id: str,
    username: str,
    roles: str = "admin",
    _: None = Depends(require_admin_api_key),
) -> dict:
    roles_list = [r.strip() for r in roles.split(",") if r.strip()]
    access = SecurityManager.create_access_token(
        user_id=user_id,
        username=username,
        roles=roles_list,
        expires_delta=timedelta(minutes=settings.API_ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    refresh = SecurityManager.create_refresh_token(user_id=user_id)
    return {
        "access_token": access,
        "refresh_token": refresh,
        "token_type": "bearer",
        "expires_in": settings.API_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }
