"""Configuration module for Codex-32.

Why this file is intentionally *not* Pydantic-based
-----------------------------------------------

This repository originally used Pydantic (v1/v2) + pydantic-settings. However, in
the current workspace environment (CPython 3.14), both:

* Pydantic v2's Rust core (pydantic-core) fails to build because PyO3 doesn't yet
  officially support Python 3.14.
* Pydantic v1 exhibits runtime/type-inference issues on 3.14.

To keep the repo runnable and testable on 3.14, we use a small settings loader that
is dependency-light and stable.

Public contract (kept stable for the rest of the app/tests):
* `Settings` class with attributes for configuration
* `get_settings()` factory
* module-level `settings` instance
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Optional


logger = logging.getLogger(__name__)


# Avoid log spam when dev servers reload or multiple modules import settings.
_PLACEHOLDER_SECRET_WARNED: set[str] = set()


class SecretValue:
    """Lightweight secret wrapper compatible with .get_secret_value()."""

    def __init__(self, value: Optional[str]):
        self._value = value or ""

    def get_secret_value(self) -> str:
        return self._value

    def __str__(self) -> str:
        return "********" if self._value else ""

    def __repr__(self) -> str:  # pragma: no cover - representation only
        return "SecretValue(********)"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, SecretValue):
            return self._value == other._value
        if isinstance(other, str):
            return self._value == other
        return False


def _env_str(name: str, default: str) -> str:
    val = os.environ.get(name)
    return default if val is None else val


def _env_int(name: str, default: int) -> int:
    val = os.environ.get(name)
    if val is None:
        return default
    return int(val)


def _env_float(name: str, default: float) -> float:
    val = os.environ.get(name)
    if val is None:
        return default
    return float(val)


def _env_bool(name: str, default: bool) -> bool:
    val = os.environ.get(name)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "on"}


def _as_secret(raw: Optional[str]) -> SecretValue:
    return raw if isinstance(raw, SecretValue) else SecretValue(raw)


@dataclass
class Settings:
    # Core Application Settings
    APP_NAME: str = "Codex-32 AI Orchestration System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # API Settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_SECRET_KEY: SecretValue = field(
        default_factory=lambda: SecretValue("CHANGE_THIS_IN_PRODUCTION")
    )
    API_ALGORITHM: str = "HS256"
    API_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    API_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Database Configuration
    DATABASE_URL: str = "postgresql+asyncpg://codex_user:codex_password@localhost:5432/codex32"
    DATABASE_ECHO: bool = False
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10

    # Redis Configuration (Self-Knowledge Base)
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_PASSWORD: Optional[str] = None
    REDIS_CACHE_TTL_SECONDS: int = 3600

    # Bot Registry & Management
    REGISTRY_FILE: str = "codex32_registry.json"
    BOTS_DIRECTORY: str = "bots"
    DEFAULT_BOT_CPU_REQUEST: str = "100m"
    DEFAULT_BOT_MEM_REQUEST: str = "128Mi"
    DEFAULT_BOT_CPU_LIMIT: str = "500m"
    DEFAULT_BOT_MEM_LIMIT: str = "512Mi"

    # Monitoring & Resource Management
    MEMORY_THRESHOLD_MB: int = 500
    CPU_THRESHOLD_PERCENT: float = 90.0
    MONITORING_INTERVAL_SEC: int = 30
    HEALTH_CHECK_INTERVAL_SEC: int = 10

    # Custom Container Engine Configuration
    CONTAINER_STORAGE_DIR: str = "/tmp/codex32-containers"
    CONTAINER_ISOLATION_LEVEL: str = "standard"  # Options: "minimal", "standard", "strict"

    # Kubernetes Configuration
    KUBECONFIG_PATH: str = field(default_factory=lambda: os.path.expanduser("~/.kube/config"))
    KUBERNETES_NAMESPACE: str = "codex-32"
    DEFAULT_REPLICAS: int = 1

    # Conversational AI Configuration
    RASA_URL: Optional[str] = None
    STT_PROVIDER: str = "vosk"  # Options: "vosk", "google", "azure"
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = None
    AZURE_SPEECH_KEY: Optional[str] = None
    AZURE_SPEECH_REGION: Optional[str] = None
    VOSK_MODEL_PATH: str = "./vosk_model_small"

    # Security Settings
    ADMIN_API_KEY: SecretValue = field(
        default_factory=lambda: SecretValue("CHANGE_THIS_IN_PRODUCTION")
    )
    CORS_ORIGINS: list[str] = field(default_factory=lambda: ["*"])
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_PERIOD_SECONDS: int = 60

    # Feature Flags
    ENABLE_CONVERSATIONAL_AI: bool = True
    ENABLE_VOICE_INPUT: bool = True
    ENABLE_SELF_KNOWLEDGE: bool = True
    ENABLE_ANOMALY_DETECTION: bool = False

    def validated(self) -> "Settings":
        lvl = self.LOG_LEVEL.upper()
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if lvl not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of {sorted(valid_levels)}")

        provider = self.STT_PROVIDER.lower()
        if provider not in {"vosk", "google", "azure"}:
            raise ValueError("STT_PROVIDER must be one of ['vosk', 'google', 'azure']")

        env_name = os.environ.get("CODEX32_ENV", "").strip().lower()
        is_debug = _env_bool("DEBUG", True)
        allow_defaults = _env_bool("CODEX32_ALLOW_DEFAULT_SECRETS", False)
        strict_env = env_name in {"production", "prod"}

        for field_name in ("API_SECRET_KEY", "ADMIN_API_KEY"):
            raw_val = getattr(self, field_name)
            raw = (
                raw_val.get_secret_value()
                if isinstance(raw_val, SecretValue)
                else str(raw_val or "")
            ).strip()
            if not raw.startswith("CHANGE_THIS_IN_PRODUCTION"):
                continue
            if strict_env or (not is_debug and not allow_defaults):
                raise ValueError(
                    f"{field_name} is set to a default placeholder; set a real secret in .env"
                )
            if not strict_env:
                # In local/dev we allow placeholders, but keep the signal without spamming logs.
                if field_name not in _PLACEHOLDER_SECRET_WARNED:
                    _PLACEHOLDER_SECRET_WARNED.add(field_name)
                    logger.warning(
                        "%s is using a placeholder secret (dev allowed). Set a real value in .env before production.",
                        field_name,
                    )

        # normalize
        return Settings(
            **{
                **self.__dict__,
                "LOG_LEVEL": lvl,
                "STT_PROVIDER": provider,
                "API_SECRET_KEY": _as_secret(self.API_SECRET_KEY),
                "ADMIN_API_KEY": _as_secret(self.ADMIN_API_KEY),
            }
        )


def get_settings() -> Settings:
    """Factory function to get application settings."""

    default = Settings()
    cors_raw = _env_str("CORS_ORIGINS", ",".join(default.CORS_ORIGINS))
    cors = [x.strip() for x in cors_raw.split(",") if x.strip()]

    s = Settings(
        APP_NAME=_env_str("APP_NAME", default.APP_NAME),
        APP_VERSION=_env_str("APP_VERSION", default.APP_VERSION),
        DEBUG=_env_bool("DEBUG", default.DEBUG),
        LOG_LEVEL=_env_str("LOG_LEVEL", default.LOG_LEVEL),

        API_HOST=_env_str("API_HOST", default.API_HOST),
        API_PORT=_env_int("API_PORT", default.API_PORT),
        API_SECRET_KEY=_as_secret(_env_str("API_SECRET_KEY", default.API_SECRET_KEY.get_secret_value())),
        API_ALGORITHM=_env_str("API_ALGORITHM", default.API_ALGORITHM),
        API_ACCESS_TOKEN_EXPIRE_MINUTES=_env_int(
            "API_ACCESS_TOKEN_EXPIRE_MINUTES", default.API_ACCESS_TOKEN_EXPIRE_MINUTES
        ),
        API_REFRESH_TOKEN_EXPIRE_DAYS=_env_int(
            "API_REFRESH_TOKEN_EXPIRE_DAYS", default.API_REFRESH_TOKEN_EXPIRE_DAYS
        ),

        DATABASE_URL=_env_str("DATABASE_URL", default.DATABASE_URL),
        DATABASE_ECHO=_env_bool("DATABASE_ECHO", default.DATABASE_ECHO),
        DATABASE_POOL_SIZE=_env_int("DATABASE_POOL_SIZE", default.DATABASE_POOL_SIZE),
        DATABASE_MAX_OVERFLOW=_env_int("DATABASE_MAX_OVERFLOW", default.DATABASE_MAX_OVERFLOW),

        REDIS_URL=_env_str("REDIS_URL", default.REDIS_URL),
        REDIS_PASSWORD=os.environ.get("REDIS_PASSWORD"),
        REDIS_CACHE_TTL_SECONDS=_env_int(
            "REDIS_CACHE_TTL_SECONDS", default.REDIS_CACHE_TTL_SECONDS
        ),

        REGISTRY_FILE=_env_str("REGISTRY_FILE", default.REGISTRY_FILE),
        BOTS_DIRECTORY=_env_str("BOTS_DIRECTORY", default.BOTS_DIRECTORY),
        DEFAULT_BOT_CPU_REQUEST=_env_str("DEFAULT_BOT_CPU_REQUEST", default.DEFAULT_BOT_CPU_REQUEST),
        DEFAULT_BOT_MEM_REQUEST=_env_str("DEFAULT_BOT_MEM_REQUEST", default.DEFAULT_BOT_MEM_REQUEST),
        DEFAULT_BOT_CPU_LIMIT=_env_str("DEFAULT_BOT_CPU_LIMIT", default.DEFAULT_BOT_CPU_LIMIT),
        DEFAULT_BOT_MEM_LIMIT=_env_str("DEFAULT_BOT_MEM_LIMIT", default.DEFAULT_BOT_MEM_LIMIT),

        MEMORY_THRESHOLD_MB=_env_int("MEMORY_THRESHOLD_MB", default.MEMORY_THRESHOLD_MB),
        CPU_THRESHOLD_PERCENT=_env_float("CPU_THRESHOLD_PERCENT", default.CPU_THRESHOLD_PERCENT),
        MONITORING_INTERVAL_SEC=_env_int("MONITORING_INTERVAL_SEC", default.MONITORING_INTERVAL_SEC),
        HEALTH_CHECK_INTERVAL_SEC=_env_int("HEALTH_CHECK_INTERVAL_SEC", default.HEALTH_CHECK_INTERVAL_SEC),

        CONTAINER_STORAGE_DIR=_env_str("CONTAINER_STORAGE_DIR", default.CONTAINER_STORAGE_DIR),
        CONTAINER_ISOLATION_LEVEL=_env_str(
            "CONTAINER_ISOLATION_LEVEL", default.CONTAINER_ISOLATION_LEVEL
        ),

        KUBECONFIG_PATH=_env_str("KUBECONFIG_PATH", default.KUBECONFIG_PATH),
        KUBERNETES_NAMESPACE=_env_str("KUBERNETES_NAMESPACE", default.KUBERNETES_NAMESPACE),
        DEFAULT_REPLICAS=_env_int("DEFAULT_REPLICAS", default.DEFAULT_REPLICAS),

        RASA_URL=os.environ.get("RASA_URL"),
        STT_PROVIDER=_env_str("STT_PROVIDER", default.STT_PROVIDER),
        GOOGLE_APPLICATION_CREDENTIALS=os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"),
        AZURE_SPEECH_KEY=os.environ.get("AZURE_SPEECH_KEY"),
        AZURE_SPEECH_REGION=os.environ.get("AZURE_SPEECH_REGION"),
        VOSK_MODEL_PATH=_env_str("VOSK_MODEL_PATH", default.VOSK_MODEL_PATH),

        ADMIN_API_KEY=_as_secret(_env_str("ADMIN_API_KEY", default.ADMIN_API_KEY.get_secret_value())),
        CORS_ORIGINS=cors or default.CORS_ORIGINS,
        RATE_LIMIT_REQUESTS=_env_int("RATE_LIMIT_REQUESTS", default.RATE_LIMIT_REQUESTS),
        RATE_LIMIT_PERIOD_SECONDS=_env_int(
            "RATE_LIMIT_PERIOD_SECONDS", default.RATE_LIMIT_PERIOD_SECONDS
        ),

        ENABLE_CONVERSATIONAL_AI=_env_bool(
            "ENABLE_CONVERSATIONAL_AI", default.ENABLE_CONVERSATIONAL_AI
        ),
        ENABLE_VOICE_INPUT=_env_bool("ENABLE_VOICE_INPUT", default.ENABLE_VOICE_INPUT),
        ENABLE_SELF_KNOWLEDGE=_env_bool(
            "ENABLE_SELF_KNOWLEDGE", default.ENABLE_SELF_KNOWLEDGE
        ),
        ENABLE_ANOMALY_DETECTION=_env_bool(
            "ENABLE_ANOMALY_DETECTION", default.ENABLE_ANOMALY_DETECTION
        ),
    ).validated()
    return s


# Global settings instance (loaded at application startup)
settings = get_settings()
