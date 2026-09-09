"""Registry for verifiable city resource packs."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class RegionContext:
    code: str
    name: str
    status: str
    pack_root: Path
    manifest: dict[str, Any]

    @classmethod
    def from_manifest(cls, path: Path) -> "RegionContext":
        manifest_path = path.resolve()
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError(f"invalid region manifest: {manifest_path}") from exc
        if not isinstance(manifest, dict):
            raise ValueError(f"region manifest must be an object: {manifest_path}")
        code = str(manifest.get("region_code") or "").strip()
        name = str(manifest.get("name") or "").strip()
        status = str(manifest.get("status") or "draft").strip()
        if not code or not name:
            raise ValueError(f"region manifest needs region_code and name: {manifest_path}")
        return cls(code=code, name=name, status=status, pack_root=manifest_path.parent, manifest=manifest)

    @property
    def is_active(self) -> bool:
        return self.status == "active"

    @property
    def version(self) -> str:
        return str(self.manifest.get("region_pack_version") or self.manifest.get("schema_version") or "unknown")

    @property
    def datasets(self) -> dict[str, Any]:
        return dict(self.manifest.get("datasets") or {})

    def get_district(self, district: str | None) -> dict[str, Any] | None:
        value = (district or "").strip()
        for item in self.manifest.get("districts") or []:
            if isinstance(item, dict) and item.get("name") == value:
                return dict(item)
        return None

    def resolve_location(self, district: str | None) -> dict[str, Any] | None:
        item = self.get_district(district)
        if not item:
            return None
        return {
            "region_code": self.code,
            "district": item["name"],
            "lat": item.get("lat"),
            "lng": item.get("lng"),
            "source": item.get("source", "region_manifest"),
        }

    def resolve_dataset_path(self, path: str | Path) -> Path:
        """Resolve a manifest-relative dataset path without leaving the pack."""
        candidate = (self.pack_root / Path(path)).resolve()
        try:
            candidate.relative_to(self.pack_root.parent.parent)
        except ValueError as exc:
            raise ValueError(f"dataset path escapes data root: {path}") from exc
        return candidate

    def public_summary(self) -> dict[str, Any]:
        return {
            "region_code": self.code,
            "name": self.name,
            "status": self.status,
            "region_pack_version": self.version,
            "districts": [item for item in self.manifest.get("districts", []) if isinstance(item, dict)],
            "future_regions": self.manifest.get("future_regions", []),
        }


class RegionRegistry:
    def __init__(self, contexts: list[RegionContext]):
        self._contexts = {context.code: context for context in contexts}

    @classmethod
    def from_root(cls, root: Path) -> "RegionRegistry":
        contexts = []
        root = root.resolve()
        if not root.exists():
            return cls([])
        for manifest_path in sorted(root.glob("*/manifest.json")):
            contexts.append(RegionContext.from_manifest(manifest_path))
        return cls(contexts)

    def get(self, code: str) -> RegionContext | None:
        return self._contexts.get(str(code))

    def active(self) -> list[RegionContext]:
        return [context for context in self._contexts.values() if context.is_active]

    def public_summaries(self, active_only: bool = True) -> list[dict[str, Any]]:
        contexts = self.active() if active_only else list(self._contexts.values())
        return [context.public_summary() for context in contexts]
