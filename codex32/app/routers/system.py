"""System monitoring API."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.bot_registry import SecureRegistry
from app.dependencies import get_registry

router = APIRouter(prefix="/api/v1/system", tags=["system"])


@router.get("/stats")
def system_stats(registry: SecureRegistry = Depends(get_registry)) -> dict:
    return {
        "registry": registry.get_registry_stats(),
    }
