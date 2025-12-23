"""Pydantic-free bot type helpers.

The codebase is in the middle of migrating away from Pydantic models to run on
Python 3.14. This module provides a tiny compatibility layer so callers can use
attribute-style access (``bot.status``) while the registry stores and returns
plain dictionaries.

We keep this surface area intentionally small.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Mapping, MutableMapping, Optional, Iterator


@dataclass(slots=True)
class BotRecord:
    """A lightweight wrapper around a bot dict.

    - Dict-like: supports ``bot["field"]``
    - Attribute-like: supports ``bot.field`` (read/write)
    - Conversion: ``to_dict()`` returns the underlying mapping.
    """

    data: MutableMapping[str, Any]

    def __getitem__(self, key: str) -> Any:
        return self.data[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.data[key] = value

    def __iter__(self) -> Iterator[str]:
        return iter(self.data)

    def __len__(self) -> int:
        return len(self.data)

    def items(self):
        return self.data.items()

    def keys(self):
        return self.data.keys()

    def values(self):
        return self.data.values()

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.data)

    def __getattr__(self, name: str) -> Any:  # pragma: no cover
        try:
            return self.data[name]
        except KeyError as e:
            raise AttributeError(name) from e

    def __setattr__(self, name: str, value: Any) -> None:  # pragma: no cover
        if name == "data":
            object.__setattr__(self, name, value)
            return
        self.data[name] = value


def as_bot_record(obj: Any) -> BotRecord:
    """Coerce dict/Pydantic-ish objects to BotRecord."""

    if isinstance(obj, BotRecord):
        return obj
    if isinstance(obj, dict):
        return BotRecord(obj)

    # Pydantic v1
    if hasattr(obj, "dict") and callable(getattr(obj, "dict")):
        return BotRecord(obj.dict())

    # Pydantic v2
    if hasattr(obj, "model_dump") and callable(getattr(obj, "model_dump")):
        return BotRecord(obj.model_dump())

    if hasattr(obj, "__dict__"):
        return BotRecord(dict(vars(obj)))

    raise TypeError(f"Unsupported bot object type: {type(obj)}")


def ensure_iso_utc(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)
