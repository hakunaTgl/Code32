"""
Monkey patches to keep Pydantic v1 working on Python 3.14.

Pydantic v1.x struggles to infer field types when defaults are ``None`` or when
``default_factory`` is used on Python 3.14. FastAPI's own models hit this path
and fail at import-time. This module relaxes the inference logic to fall back to
the declared annotation or ``typing.Any`` instead of raising ``ConfigError``.
"""
from __future__ import annotations

import inspect
from typing import Any, Set

from pydantic import schema as pydantic_schema
from pydantic.fields import FieldInfo, ModelField, Undefined, UndefinedType


def apply_patch() -> None:
    """Apply the compatibility patch once."""
    if getattr(ModelField._set_default_and_type, "__patched_for_py314__", False):
        return

    def _patched_set_default_and_type(self: ModelField) -> None:
        # Handle default_factory without eager failure on Python 3.14
        if self.default_factory is not None and self.type_ is Undefined:
            if self.annotation not in (inspect._empty, Undefined, UndefinedType):
                self.type_ = self.annotation
                self.outer_type_ = self.annotation
            else:
                self.type_ = Any
                self.outer_type_ = Any
            return

        default_value = self.get_default()

        if self.type_ is Undefined:
            if self.annotation not in (inspect._empty, Undefined, UndefinedType):
                self.type_ = self.annotation
                self.outer_type_ = self.annotation
            elif default_value is not None:
                self.type_ = default_value.__class__
                self.outer_type_ = self.type_
                self.annotation = self.type_
            else:
                self.type_ = Any
                self.outer_type_ = Any
                self.annotation = Any

        if self.type_ in (Undefined, UndefinedType):
            self.type_ = Any
            self.outer_type_ = Any
            self.annotation = Any

        if self.required is False and default_value is None:
            self.allow_none = True

    _patched_set_default_and_type.__patched_for_py314__ = True  # type: ignore[attr-defined]
    ModelField._set_default_and_type = _patched_set_default_and_type  # type: ignore[assignment]

    def _patched_get_annotation_from_field_info(
        annotation: Any, field_info: FieldInfo, field_name: str, validate_assignment: bool = False
    ) -> Any:
        """Ignore unenforced constraints instead of raising ConfigError."""
        constraints = field_info.get_constraints()
        used_constraints: Set[str] = set()
        if constraints:
            try:
                annotation, used_constraints = pydantic_schema.get_annotation_with_constraints(annotation, field_info)
            except Exception:
                annotation = Any
                used_constraints = constraints
        if validate_assignment:
            used_constraints.add("allow_mutation")
        if annotation in (inspect._empty, Undefined, UndefinedType):
            return Any
        return annotation

    pydantic_schema.get_annotation_from_field_info = _patched_get_annotation_from_field_info  # type: ignore[assignment]


# Patch eagerly on import for all callers.
apply_patch()
