"""FastAPI routers for Codex-32."""

from .bots import router as bots_router
from .auth import router as auth_router
from .system import router as system_router
from .ws import router as ws_router
from .self import router as self_router
from .guide import router as guide_router
from .dashboard import router as dashboard_router

__all__ = [
    "bots_router",
    "auth_router",
    "system_router",
    "ws_router",
    "self_router",
    "guide_router",
    "dashboard_router",
]
