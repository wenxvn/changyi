"""Small response envelope helper shared by v1 routes."""

from __future__ import annotations

from typing import Any
import uuid


def request_id() -> str:
    return uuid.uuid4().hex


def success(data: Any, *, region_code: str, model_version: str, request_id_value: str | None = None, **extra) -> dict:
    meta = {
        "request_id": request_id_value or request_id(),
        "model_version": model_version,
        "region_code": region_code,
    }
    meta.update(extra)
    return {"data": data, "meta": meta, "error": None}


def failure(code: str, message: str, *, region_code: str, model_version: str, request_id_value: str | None = None, details: Any = None) -> dict:
    error = {"code": code, "message": message}
    if details is not None:
        error["details"] = details
    return {
        "data": None,
        "meta": {
            "request_id": request_id_value or request_id(),
            "model_version": model_version,
            "region_code": region_code,
        },
        "error": error,
    }
