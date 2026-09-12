"""Transit dataset quality gate.

Transit rows stay provisional until source, license, timestamp, coordinates
and schema checks pass. Only rankable features may influence recommendation
ranking; everything else is display reference or distance-only fallback.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from typing import Any


QUALITY_VERIFIED = "VERIFIED"
QUALITY_PROVISIONAL = "PROVISIONAL"
QUALITY_INVALID = "INVALID"


@dataclass(frozen=True)
class TransitQuality:
    dataset_id: str
    quality: str
    rankable: bool
    record_count: int
    source: str | None
    license_status: str
    last_updated: str | None
    reasons: tuple[str, ...]
    notice: str
    metadata: Mapping[str, Any] | None = None

    def to_payload(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["reasons"] = list(self.reasons)
        payload["metadata"] = dict(self.metadata) if self.metadata else None
        return payload


def _has_source(value: Any) -> bool:
    return isinstance(value, str) and value.strip() and value.strip().lower() not in {"unknown", "none", "null"}


def _valid_coord(lat: Any, lng: Any) -> bool:
    try:
        lat_f = float(lat)
        lng_f = float(lng)
    except (TypeError, ValueError):
        return False
    return 18 <= lat_f <= 55 and 73 <= lng_f <= 136


def _dataset_metadata(metadata: Mapping[str, Any] | None, dataset_id: str) -> Mapping[str, Any] | None:
    if not metadata:
        return None
    datasets = metadata.get("datasets") if isinstance(metadata, Mapping) else None
    if isinstance(datasets, Mapping):
        item = datasets.get(dataset_id)
        if isinstance(item, Mapping):
            return item
    return None


def _license_from_metadata(metadata: Mapping[str, Any] | None) -> str:
    if not metadata:
        return "not_recorded"
    value = metadata.get("license_status")
    if isinstance(value, str) and value.strip():
        return value.strip()
    return "not_recorded"


def classify_bus_stations(
    rows: Sequence[Mapping[str, Any]],
    summary: Mapping[str, Any] | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> TransitQuality:
    summary = summary or {}
    source = summary.get("source") or (metadata or {}).get("source_url")
    license_status = _license_from_metadata(metadata)
    cleaned = [row for row in rows if isinstance(row, Mapping)]
    valid_coords = sum(1 for row in cleaned if _valid_coord(row.get("latitude"), row.get("longitude")))
    active = sum(1 for row in cleaned if row.get("active_status") == "有效")
    reasons: list[str] = []
    if not _has_source(source):
        reasons.append("source_missing")
    if license_status == "not_recorded":
        reasons.append("license_not_recorded")
    if valid_coords < len(cleaned):
        reasons.append("invalid_coordinates_present")
    if len(cleaned) < 200:
        reasons.append("sparse_citywide_sample")
    if active < len(cleaned):
        reasons.append("inactive_or_unknown_status_present")
    quality = QUALITY_VERIFIED if not reasons else QUALITY_PROVISIONAL
    # Provisional/sparse samples must not reorder hospitals; ranking stays distance-only.
    rankable = quality == QUALITY_VERIFIED
    notice = (
        "公交站点数据未通过正式质量门，仅作可达性参考，不参与推荐排序。"
        if not rankable
        else "公交站点数据已通过质量门，可在普通场景辅助可达性测算。"
    )
    return TransitQuality(
        dataset_id="bus_stations",
        quality=quality,
        rankable=rankable,
        record_count=len(cleaned),
        source=str(source) if source else None,
        license_status=license_status,
        last_updated=str(summary.get("cleaned_at") or None),
        reasons=tuple(reasons),
        notice=notice,
        metadata=metadata,
    )


def classify_taxi_operations(
    rows: Sequence[Mapping[str, Any]],
    summary: Mapping[str, Any] | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> TransitQuality:
    summary = summary or {}
    source = summary.get("source") or (metadata or {}).get("source_url")
    cleaned = [row for row in rows if isinstance(row, Mapping)]
    reasons: list[str] = []
    if not _has_source(source):
        reasons.append("source_missing")
    reasons.append("license_not_recorded")
    reasons.append("masked_or_sample_operations")
    quality = QUALITY_PROVISIONAL if cleaned else QUALITY_INVALID
    return TransitQuality(
        dataset_id="taxi_operations",
        quality=quality,
        rankable=False,
        record_count=len(cleaned),
        source=str(source) if source else None,
        license_status=_license_from_metadata(metadata),
        last_updated=str(summary.get("cleaned_at") or None),
        reasons=tuple(reasons),
        notice="出租车样本为展示参考，不作为正式排序依据。",
        metadata=metadata,
    )


def classify_bike_dataset(
    rows: Sequence[Mapping[str, Any]],
    summary: Mapping[str, Any] | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> TransitQuality:
    summary = summary or {}
    cleaned = [row for row in rows if isinstance(row, Mapping)]
    source = summary.get("source") or (metadata or {}).get("source_url")
    return TransitQuality(
        dataset_id="bike",
        quality=QUALITY_PROVISIONAL if cleaned else QUALITY_INVALID,
        rankable=False,
        record_count=len(cleaned),
        source=str(source) if source else None,
        license_status=_license_from_metadata(metadata),
        last_updated=None,
        reasons=("display_only", "license_not_recorded"),
        notice="共享骑行仅用于绿色出行展示，不参与医疗推荐排序。",
        metadata=metadata,
    )


class TransitQualityGate:
    def __init__(self, qualities: dict[str, TransitQuality]) -> None:
        self._qualities = qualities

    @classmethod
    def from_datasets(
        cls,
        *,
        bus_rows: Sequence[Mapping[str, Any]],
        bus_summary: Mapping[str, Any] | None = None,
        taxi_rows: Sequence[Mapping[str, Any]] | None = None,
        taxi_summary: Mapping[str, Any] | None = None,
        bike_rows: Sequence[Mapping[str, Any]] | None = None,
        bike_summary: Mapping[str, Any] | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> "TransitQualityGate":
        return cls({
            "bus_stations": classify_bus_stations(
                bus_rows, bus_summary, _dataset_metadata(metadata, "bus_stations")
            ),
            "taxi_operations": classify_taxi_operations(
                taxi_rows or [], taxi_summary, _dataset_metadata(metadata, "taxi_operations")
            ),
            "bike": classify_bike_dataset(
                bike_rows or [], bike_summary, _dataset_metadata(metadata, "bike")
            ),
        })

    def quality(self, dataset_id: str) -> TransitQuality:
        return self._qualities.get(dataset_id) or TransitQuality(
            dataset_id=dataset_id,
            quality=QUALITY_INVALID,
            rankable=False,
            record_count=0,
            source=None,
            license_status="not_recorded",
            last_updated=None,
            reasons=("dataset_missing",),
            notice="交通数据不可用，可达性回退为直线距离。",
        )

    def can_rank(self, dataset_id: str) -> bool:
        return self.quality(dataset_id).rankable

    def payload(self) -> dict[str, Any]:
        return {
            dataset_id: quality.to_payload()
            for dataset_id, quality in self._qualities.items()
        }

    def ranking_notice(self) -> str:
        if all(item.rankable for item in self._qualities.values() if item.record_count):
            return "交通特征已通过质量门。"
        return "交通数据未全部通过质量门，可达性主要按直线距离估算；站点信息仅作参考。"
