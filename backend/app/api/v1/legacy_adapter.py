"""Lazy bridge from versioned routes to the legacy application composition."""

from __future__ import annotations

from collections.abc import Callable
import importlib
from typing import Any


HANDLER_EXTENSION = "changyi.v1_legacy_handlers"


def register_legacy_handlers(application: Any, handlers: dict[str, Callable[..., Any]]) -> None:
    """Register compatibility handlers on the active Flask app composition root."""

    application.extensions[HANDLER_EXTENSION] = dict(handlers)


def resolve_legacy_handler(name: str) -> Callable[..., Any]:
    """Resolve a registered handler, with the import bridge kept for old callers."""

    try:
        from flask import current_app, has_app_context

        if has_app_context():
            handlers = current_app.extensions.get(HANDLER_EXTENSION, {})
            handler = handlers.get(name)
            if handler is not None:
                return handler
    except ImportError:
        pass

    legacy_module = importlib.import_module("app")
    return getattr(legacy_module, name)


def call_legacy_handler(name: str, *args: Any, **kwargs: Any) -> Any:
    """Call a resolved legacy handler while keeping the adapter explicit."""

    return resolve_legacy_handler(name)(*args, **kwargs)
