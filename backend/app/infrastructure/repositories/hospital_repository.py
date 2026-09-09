"""Hospital repository seam with an explicit legacy compatibility adapter."""

from __future__ import annotations

from typing import Any, Iterable

from ..regions.registry import RegionContext


class HospitalRepository:
    """Serve injected hospital records while the legacy constant is migrated.

    The injected-record seam lets callers test the repository without touching
    the current `app.py` catalog. Moving the catalog itself is P1-S3's next
    small step because its provenance must be audited field by field first.
    """

    def __init__(self, region: RegionContext, records: Iterable[dict[str, Any]] = ()):
        self.region = region
        self._records = tuple(dict(record) for record in records)

    def list(self) -> list[dict[str, Any]]:
        return [dict(record) for record in self._records]

    def get(self, hospital_id: int | str) -> dict[str, Any] | None:
        for record in self._records:
            if str(record.get("id")) == str(hospital_id):
                return dict(record)
        return None
