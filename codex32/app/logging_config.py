"""Logging configuration for Codex-32."""
import logging
import logging.config
import sys
from pathlib import Path

from app.config import settings


def setup_logging() -> None:
    """Configure centralized structured logging for the application."""

    log_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "detailed": {
                "format": (
                    "%(asctime)s - %(name)s - %(levelname)s - "
                    "[%(filename)s:%(lineno)d] - %(funcName)s() - %(message)s"
                ),
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "json": {
                "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
                "format": (
                    "%(asctime)s %(name)s %(levelname)s %(message)s "
                    "%(filename)s %(lineno)d %(funcName)s"
                ),
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": settings.LOG_LEVEL,
                "formatter": "detailed" if settings.DEBUG else "standard",
                "stream": "ext://sys.stdout",
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": settings.LOG_LEVEL,
                "formatter": "detailed",
                "filename": "logs/codex32.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
            },
            "file_errors": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "ERROR",
                "formatter": "detailed",
                "filename": "logs/codex32_errors.log",
                "maxBytes": 10485760,
                "backupCount": 5,
            },
        },
        "loggers": {
            "": {  # Root logger
                "level": settings.LOG_LEVEL,
                "handlers": ["console", "file", "file_errors"],
            },
            "fastapi": {
                "level": "INFO",
                "handlers": ["console", "file"],
                "propagate": False,
            },
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console", "file"],
                "propagate": False,
            },
            "uvicorn.access": {
                "level": "INFO",
                "handlers": ["console", "file"],
                "propagate": False,
            },
            "asyncio": {
                "level": "WARNING",
                "propagate": True,
            },
            "app": {
                "level": settings.LOG_LEVEL,
                "handlers": ["console", "file", "file_errors"],
                "propagate": False,
            },
        },
    }

    # Create logs directory if it doesn't exist
    Path("logs").mkdir(exist_ok=True)

    # Apply logging configuration
    logging.config.dictConfig(log_config)

    # Configure asyncio logging if in debug mode
    if settings.DEBUG:
        logging.getLogger("asyncio").setLevel(logging.DEBUG)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)
