"""Hospital repository backed by the active region hospital catalog."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

from ..regions.registry import RegionContext


class HospitalRepository:
    """Serve public hospital records from a region-owned catalog.

    The repository keeps the catalog envelope out of application services and
    preserves the injected-record seam used by unit tests.
    """

    def __init__(self, region: RegionContext, records: Iterable[dict[str, Any]] = ()):
        self.region = region
        self._records = tuple(dict(record) for record in records)

    @classmethod
    def from_json(cls, region: RegionContext, path: Path) -> "HospitalRepository":
        """Load and minimally validate a region hospital catalog."""

        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict) or not isinstance(payload.get("records"), list):
            raise ValueError(f"invalid hospital catalog: {path}")
        if str(payload.get("region_code")) != region.code:
            raise ValueError(f"hospital catalog region mismatch: {path}")
        records = [record for record in payload["records"] if isinstance(record, dict)]
        return cls(region, records)

    def list(self) -> list[dict[str, Any]]:
        return [dict(record) for record in self._records]

    def get(self, hospital_id: int | str) -> dict[str, Any] | None:
        for record in self._records:
            if str(record.get("id")) == str(hospital_id):
                return dict(record)
        return None
