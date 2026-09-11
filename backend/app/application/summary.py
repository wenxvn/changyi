"""Build the read-only runtime summary used by the v1 home page."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any


class SummaryApplicationService:
    """Compose summary metrics from already-loaded region and catalog suppliers."""

    def __init__(
        self,
        *,
        region: Callable[[str], Any],
        hospitals: Callable[[], list[Mapping[str, Any]]],
        real_doctors: Callable[[], list[Mapping[str, Any]]],
        fallback_doctors: Callable[[], list[Mapping[str, Any]]],
        transit: Callable[[], Mapping[str, Any]],
    ) -> None:
        self._region = region
        self._hospitals = hospitals
        self._real_doctors = real_doctors
        self._fallback_doctors = fallback_doctors
        self._transit = transit

    def build(self, region_code: str) -> dict[str, Any]:
        region = self._region(region_code)
        districts = list(region.manifest.get("districts") or []) if region else []
        hospital_dataset = (region.datasets.get("hospitals") or {}) if region else {}
        transit_dataset = (region.datasets.get("transit") or {}) if region else {}
        real_doctors = self._real_doctors()
        hospitals = self._hospitals()
        fallback_doctors = self._fallback_doctors()
        transit = self._transit()
        bus_routes = transit.get("routes", [])

        metrics = {
            "hospitals": {
                "value": len(hospitals),
                "label": "医疗机构",
                "source_class": hospital_dataset.get("source_class", hospital_dataset.get("source", "legacy_catalog_import")),
                "status": hospital_dataset.get("status", "provisional"),
            },
            "doctors": {
                "value": len(real_doctors) if real_doctors else len(fallback_doctors),
                "label": "医生公开资料",
                "source_class": "public_source_mixed" if real_doctors else "legacy_mock_catalog",
                "status": "available" if real_doctors else "fallback",
            },
            "bus_routes": {
                "value": len(bus_routes),
                "label": "公交线路",
                "source_class": (transit_dataset.get("bus_routes") or {}).get("source_class", "unknown"),
                "status": "available",
            },
            "districts": {
                "value": len(districts),
                "label": "城市区域",
                "source_class": "region_manifest",
                "status": "available" if region else "not_ready",
            },
        }
        return {
            "region": {
                "code": region.code if region else region_code,
                "name": region.name if region else "常州市",
                "status": region.status if region else "not_ready",
                "region_pack_version": region.version if region else "unknown",
            },
            "metrics": metrics,
            "generated_from": {
                "region_pack_version": region.version if region else "unknown",
                "dataset_status": "runtime_summary",
            },
        }
