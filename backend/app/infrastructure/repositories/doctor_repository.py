"""Doctor dataset repository; normalization remains a later slice."""

from __future__ import annotations

from typing import Any

from ..data.loaders import DataLoadError, JsonDataLoader
from ..regions.registry import RegionContext


class DoctorRepository:
    def __init__(self, region: RegionContext, loader: JsonDataLoader):
        self.region = region
        self.loader = loader

    def _sources(self) -> list[dict[str, Any]]:
        sources = self.region.datasets.get("doctors", [])
        return [item for item in sources if isinstance(item, dict) and item.get("path")]

    def load_datasets(self) -> list[dict[str, Any]]:
        datasets = []
        for source in self._sources():
            rows, loaded = self.loader.collection(
                self.region.resolve_dataset_path(source["path"]),
                source.get("record_key", "doctors"),
            )
            datasets.append({
                "dataset_id": source.get("dataset_id"),
                "hospital_id": source.get("hospital_id"),
                "path": str(loaded.path),
                "sha256": loaded.sha256,
                "rows": rows,
            })
        return datasets

    def count(self) -> int:
        return sum(len(dataset["rows"]) for dataset in self.load_datasets())
