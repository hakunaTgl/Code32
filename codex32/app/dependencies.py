"""Dependency injection helpers for FastAPI.

This module intentionally keeps dependencies lightweight and file-based.
It provides singleton-ish instances for the registry/executor while still
being test-friendly (overrideable via FastAPI dependency overrides).
"""

from __future__ import annotations

from functools import lru_cache

from app.bot_registry import SecureRegistry
from app.adaptive_executor import AdaptiveExecutor
from app.container_engine import get_engine


@lru_cache(maxsize=1)
def get_registry() -> SecureRegistry:
    """Return a process-wide SecureRegistry instance."""
    return SecureRegistry()


@lru_cache(maxsize=1)
def get_executor() -> AdaptiveExecutor:
    """Return a process-wide AdaptiveExecutor instance."""
    registry = get_registry()
    engine = get_engine()
    return AdaptiveExecutor(registry=registry, container_engine=engine)
