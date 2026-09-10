"""Lazy bridge from versioned routes to the legacy application composition."""

from __future__ import annotations

from collections.abc import Callable
import importlib
from typing import Any


def resolve_legacy_handler(name: str) -> Callable[..., Any]:
    """Resolve one existing app-level handler without importing it at startup."""

    legacy_module = importlib.import_module("app")
    return getattr(legacy_module, name)


def call_legacy_handler(name: str, *args: Any, **kwargs: Any) -> Any:
    """Call a resolved legacy handler while keeping the adapter explicit."""

    return resolve_legacy_handler(name)(*args, **kwargs)
