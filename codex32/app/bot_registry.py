"""Bot registry with atomic operations and caching."""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from pathlib import Path

from enum import Enum

from app.utils import atomic_save_json, load_json
from app.config import settings
from app.bot_types import BotRecord

logger = logging.getLogger(__name__)


def _normalize_for_json(bot: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure bot dict is JSON-serializable (notably datetimes)."""

    normalized = dict(bot)
    for k, v in list(normalized.items()):
        if isinstance(v, datetime):
            normalized[k] = v.isoformat()
    return normalized


def _as_dict(bot: Any) -> Dict[str, Any]:
    """Normalize a Bot-like object to a plain dict.

    Supports:
    - plain dict
    - Pydantic v1 (`dict()`)
    - Pydantic v2 (`model_dump()`)
    - generic objects with `__dict__`
    """
    if isinstance(bot, dict):
        return dict(bot)
    if hasattr(bot, "to_dict") and callable(getattr(bot, "to_dict")):
        return dict(bot.to_dict())  # type: ignore[no-any-return]
    if hasattr(bot, "model_dump"):
        return dict(bot.model_dump())  # type: ignore[attr-defined]
    if hasattr(bot, "dict"):
        return dict(bot.dict())  # type: ignore[attr-defined]
    if hasattr(bot, "__dict__"):
        return dict(vars(bot))
    raise TypeError("Bot must be a dict or a model-like object")


class BotStatus(str, Enum):
    """Minimal bot status enum.

    This replaces the Pydantic-backed model while running on Python versions where
    Pydantic is not currently compatible (e.g., CPython 3.14).
    """

    CREATED = "created"
    DEPLOYING = "deploying"
    RUNNING = "running"
    STOPPED = "stopped"
    FAILED = "failed"
    ERROR = "error"


class SecureRegistry:
    """Manages bot registry with atomic writes and caching.

    This registry stores bot configurations and status in a JSON file with atomic
    write guarantees to prevent corruption during concurrent access.

    Note: This implementation is intentionally dict-backed for maximum compatibility
    under CPython 3.14 (where Pydantic may not be available).
    """

    def __init__(self, registry_file: str = None):
        self.file = registry_file or settings.REGISTRY_FILE
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._load_initial_data()

    def _load_initial_data(self) -> None:
        """Load bot registry from disk into memory cache."""
        try:
            raw_data = load_json(self.file).get("bots", [])
            # Store as plain dicts for maximum compatibility.
            self._cache = {}
            for d in raw_data:
                if not isinstance(d, dict):
                    continue
                bot_id = str(d.get("id", "")).strip()
                if not bot_id:
                    continue
                self._cache[bot_id] = dict(d)
            logger.info("Loaded %d bots from registry: %s", len(self._cache), self.file)
        except Exception as e:
            logger.error(f"Failed to load registry from {self.file}: {e}")
            self._cache = {}

    def _save(self) -> None:
        """Save current cache to disk atomically."""
        try:
            data = {
                "bots": [dict(bot) for bot in self._cache.values()],
                "metadata": {
                    "total_bots": len(self._cache),
                    "last_updated": Path(self.file).stat().st_mtime if Path(self.file).exists() else None,
                },
            }
            atomic_save_json(self.file, data)
        except Exception as e:
            logger.error(f"Failed to save registry: {e}")
            raise

    def get_all_bots(self) -> List[BotRecord]:
        """Get all registered bots."""
        return [BotRecord(dict(b)) for b in self._cache.values()]

    def get_bot_by_id(self, bot_id: str) -> Optional[BotRecord]:
        """Retrieve a bot by its ID."""
        bot = self._cache.get(bot_id)
        return BotRecord(dict(bot)) if bot else None

    def get_bot_by_name(self, name: str) -> Optional[BotRecord]:
        """Retrieve a bot by its name."""
        for bot in self._cache.values():
            if str(bot.get("name", "")).lower() == name.lower():
                return BotRecord(dict(bot))
        return None

    def get_bots_by_status(self, status: BotStatus) -> List[BotRecord]:
        """Get all bots with a specific status."""
        target = status.value if isinstance(status, Enum) else str(status)
        return [BotRecord(dict(bot)) for bot in self._cache.values() if str(bot.get("status", "")) == target]

    def get_bots_by_role(self, role: str) -> List[BotRecord]:
        """Get all bots with a specific role."""
        return [BotRecord(dict(bot)) for bot in self._cache.values() if str(bot.get("role", "")) == role]

    def register_bot(self, bot: Any) -> Dict[str, Any]:
        """Register a new bot in the registry."""
        bot_d = _as_dict(bot)
        bot_id = str(bot_d.get("id", "")).strip()
        if not bot_id:
            raise ValueError("Bot must include non-empty 'id'")
        if bot_id in self._cache:
            raise ValueError(f"Bot with ID '{bot_id}' already exists")

        self._cache[bot_id] = _normalize_for_json(dict(bot_d))
        self._save()
        logger.info("Registered bot: %s (ID: %s)", self._cache[bot_id].get("name"), bot_id)
        return dict(self._cache[bot_id])

    def update_bot(self, bot: Any) -> Dict[str, Any]:
        """Update an existing bot in the registry."""
        bot_d = _as_dict(bot)
        bot_id = str(bot_d.get("id", "")).strip()
        if not bot_id:
            raise ValueError("Bot must include non-empty 'id'")
        if bot_id not in self._cache:
            raise ValueError(f"Bot with ID '{bot_id}' not found in registry")

        self._cache[bot_id] = _normalize_for_json(dict(bot_d))
        self._save()
        logger.info(
            "Updated bot: %s (ID: %s), status: %s",
            self._cache[bot_id].get("name"),
            bot_id,
            self._cache[bot_id].get("status"),
        )
        return dict(self._cache[bot_id])

    def update_bot_status(self, bot_id: str, status: BotStatus, **kwargs) -> Optional[Dict[str, Any]]:
        """Update only the status of a bot."""
        bot = self._cache.get(bot_id)
        if not bot:
            logger.warning("Attempted to update non-existent bot: %s", bot_id)
            return None

        bot["status"] = status.value if isinstance(status, Enum) else str(status)
        for key, value in kwargs.items():
            bot[key] = value

        self._save()
        logger.info("Updated bot %s status to %s", bot_id, bot.get("status"))
        return dict(bot)

    def unregister_bot(self, bot_id: str) -> bool:
        """Remove a bot from the registry."""
        if bot_id not in self._cache:
            logger.warning("Attempted to unregister non-existent bot: %s", bot_id)
            return False

        bot_name = self._cache[bot_id].get("name")
        del self._cache[bot_id]
        self._save()
        logger.info("Unregistered bot: %s (ID: %s)", bot_name, bot_id)
        return True

    def get_registry_stats(self) -> Dict[str, Any]:
        """Get statistics about the current registry."""
        bots_by_status: Dict[str, int] = {}
        active_bots = 0
        failed_bots = 0

        for b in self._cache.values():
            status_val = str(b.get("status", "")).lower()
            if status_val:
                bots_by_status[status_val] = bots_by_status.get(status_val, 0) + 1
            if status_val == BotStatus.RUNNING.value:
                active_bots += 1
            if (
                status_val in {BotStatus.ERROR.value, "error", BotStatus.FAILED.value}
                or b.get("error")
                or b.get("error_message")
            ):
                failed_bots += 1

        return {
            "total_bots": len(self._cache),
            "bots_by_status": bots_by_status,
            "active_bots": active_bots,
            "failed_bots": failed_bots,
        }

    def clear_registry(self) -> None:
        """Clear all bots from the registry (WARNING: destructive operation)."""
        logger.warning("Clearing entire bot registry!")
        self._cache.clear()
        self._save()

    def export_registry(self, filepath: str) -> bool:
        """Export registry to a backup file."""
        try:
            data = {
                "bots": [dict(bot) for bot in self._cache.values()],
                "metadata": {"total_bots": len(self._cache)},
            }
            atomic_save_json(filepath, data)
            logger.info("Registry exported to: %s", filepath)
            return True
        except Exception as e:
            logger.error(f"Failed to export registry: {e}")
            return False

    def import_registry(self, filepath: str, merge: bool = False) -> bool:
        """Import registry from a backup file."""
        try:
            data = load_json(filepath)
            imported_bots: Dict[str, Dict[str, Any]] = {}
            for d in data.get("bots", []):
                if not isinstance(d, dict):
                    continue
                bot_id = str(d.get("id", "")).strip()
                if not bot_id:
                    continue
                imported_bots[bot_id] = dict(d)

            if merge:
                self._cache.update(imported_bots)
                logger.info("Merged %d bots from: %s", len(imported_bots), filepath)
            else:
                self._cache = dict(imported_bots)
                logger.info("Replaced registry with %d bots from: %s", len(imported_bots), filepath)

            self._save()
            return True
        except Exception as e:
            logger.error(f"Failed to import registry: {e}")
            return False
