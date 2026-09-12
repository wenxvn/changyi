"""Provenance-aware import pipeline foundation.

Raw snapshots stay read-only and are never loaded by the application layer.
Canonical records must carry source, capture time, verification status, and
displayable/rankable gates before promotion.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RAW_ROOT = Path("data/raw")
CANONICAL_ROOT = Path("data/regions/320400")


@dataclass(frozen=True)
class ImportProvenance:
    source_url: str | None
    provider: str | None
    captured_at: str | None
    license_status: str
    verification_status: str  # VERIFIED | PROVISIONAL | INVALID
    displayable: bool
    rankable: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "source_url": self.source_url,
            "provider": self.provider,
            "captured_at": self.captured_at,
            "license_status": self.license_status,
            "verification_status": self.verification_status,
            "displayable": self.displayable,
            "rankable": self.rankable,
        }


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def write_raw_snapshot(
    *,
    dataset: str,
    source_url: str | None,
    provider: str | None,
    payload: dict[str, Any] | list[Any],
    license_status: str = "not_recorded",
    root: Path = RAW_ROOT,
) -> Path:
    """Persist a read-only raw snapshot under data/raw/<dataset>/."""

    if not dataset or "/" in dataset or "\\" in dataset:
        raise ValueError("dataset must be a simple directory name")
    captured_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    directory = root / dataset
    directory.mkdir(parents=True, exist_ok=True)
    body = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    raw_path = directory / "snapshot.json"
    raw_path.write_text(body, encoding="utf-8")
    meta = {
        "schema_version": "raw-snapshot/v1",
        "dataset": dataset,
        "source_url": source_url,
        "provider": provider,
        "captured_at": captured_at,
        "license_status": license_status,
        "sha256": sha256_bytes(body.encode("utf-8")),
        "readonly": True,
        "application_layer_must_not_read": True,
    }
    (directory / "metadata.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return raw_path


def read_raw_metadata(dataset: str, root: Path = RAW_ROOT) -> dict[str, Any] | None:
    path = root / dataset / "metadata.json"
    if not path.is_file():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def quality_gate(
    *,
    schema_valid: bool,
    source_url: str | None,
    license_status: str,
    captured_at: str | None,
    coordinates_valid: bool = True,
) -> ImportProvenance:
    """Decide displayable/rankable from explicit provenance facts only."""

    verified = bool(
        schema_valid
        and source_url
        and license_status not in {None, "", "not_recorded", "unknown"}
        and captured_at
        and coordinates_valid
    )
    provisional = schema_valid and not verified
    return ImportProvenance(
        source_url=source_url,
        provider=None,
        captured_at=captured_at,
        license_status=license_status or "not_recorded",
        verification_status="VERIFIED" if verified else ("PROVISIONAL" if provisional else "INVALID"),
        displayable=schema_valid and (verified or provisional),
        rankable=verified,
    )


def assert_raw_not_used_by_application(project_root: Path) -> None:
    """Guardrail helper for tests: application packages must not import data/raw."""

    forbidden = []
    for path in (project_root / "backend").rglob("*.py"):
        if path.name == "import_pipeline.py":
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if "data/raw" in text or "data\\raw" in text:
            forbidden.append(str(path))
    if forbidden:
        raise AssertionError(f"application layer must not read raw snapshots: {forbidden}")
