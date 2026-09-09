"""Region-scoped transit data repository."""

from __future__ import annotations

from typing import Any

from ..data.loaders import JsonDataLoader
from ..regions.registry import RegionContext


class TransitRepository:
    def __init__(self, region: RegionContext, loader: JsonDataLoader):
        self.region = region
        self.loader = loader

    def list(self, dataset_id: str) -> list[dict[str, Any]]:
        source = self.region.datasets.get("transit", {}).get(dataset_id)
        if not isinstance(source, dict) or not source.get("path"):
            return []
        rows, _ = self.loader.collection(
            self.region.resolve_dataset_path(source["path"]),
            source.get("record_key", dataset_id),
        )
        return rows
