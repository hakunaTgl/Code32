"""Codex-32: Advanced AI Orchestration System."""

__version__ = "1.0.0"
__author__ = "Codex Team"
__description__ = "An async, secure, and scalable AI bot orchestration platform"

from app.config import settings

# NOTE: Keep `app` package imports lightweight.
# Importing heavy modules (and Pydantic-based types) at package import time makes
# startup and test collection fragile on newer Python versions. Call sites should
# import the concrete objects from their modules directly.

from app.logging_config import setup_logging, get_logger

__all__ = [
    "settings",
    "setup_logging",
    "get_logger",
]
