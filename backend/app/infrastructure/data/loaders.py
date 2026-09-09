"""Deterministic, read-only loaders used at the data boundary."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any


class DataLoadError(RuntimeError):
    """Raised when a declared dataset cannot be safely loaded."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


@dataclass(frozen=True)
class LoadedJson:
    path: Path
    value: Any
    sha256: str


class JsonDataLoader:
    """Load JSON without hiding missing files or malformed content."""

    def __init__(self, project_root: Path):
        self.project_root = project_root.resolve()

    def resolve(self, path: str | Path) -> Path:
        candidate = Path(path)
        resolved = candidate.resolve() if candidate.is_absolute() else (self.project_root / candidate).resolve()
        try:
            resolved.relative_to(self.project_root)
        except ValueError as exc:
            raise DataLoadError(f"dataset path escapes project root: {path}") from exc
        return resolved

    def load(self, path: str | Path) -> LoadedJson:
        resolved = self.resolve(path)
        if not resolved.exists():
            raise DataLoadError(f"dataset not found: {resolved}")
        if not resolved.is_file():
            raise DataLoadError(f"dataset is not a file: {resolved}")
        try:
            value = json.loads(resolved.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise DataLoadError(f"invalid JSON dataset: {resolved}") from exc
        return LoadedJson(path=resolved, value=value, sha256=sha256_file(resolved))

    def collection(self, path: str | Path, key: str) -> tuple[list[dict], LoadedJson]:
        loaded = self.load(path)
        if not isinstance(loaded.value, dict):
            raise DataLoadError(f"dataset root must be an object: {loaded.path}")
        rows = loaded.value.get(key)
        if not isinstance(rows, list):
            raise DataLoadError(f"dataset collection missing or invalid: {loaded.path}#{key}")
        if not all(isinstance(row, dict) for row in rows):
            raise DataLoadError(f"dataset collection rows must be objects: {loaded.path}#{key}")
        return rows, loaded
