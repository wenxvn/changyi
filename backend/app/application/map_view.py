"""Build the read-only map view from public resource coordinates."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
import math
from typing import Any


class MapLocationError(ValueError):
    """Raised when an optional user coordinate is incomplete or invalid."""


def parse_coordinate(value: str | None, field: str, minimum: float, maximum: float) -> float | None:
    if value is None or value.strip() == "":
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise MapLocationError(f"{field} 必须是有效坐标") from exc
    if not math.isfinite(parsed) or not minimum <= parsed <= maximum:
        raise MapLocationError(f"{field} 超出有效范围")
    return parsed


def _distance_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    radius_km = 6371.0088
    lat1_rad, lat2_rad = math.radians(lat1), math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lng = math.radians(lng2 - lng1)
    haversine = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lng / 2) ** 2
    )
    return round(radius_km * 2 * math.asin(math.sqrt(haversine)), 2)


def _project_points(items: list[dict[str, Any]]) -> None:
    if not items:
        return
    lats = [item["lat"] for item in items]
    lngs = [item["lng"] for item in items]
    min_lat, max_lat = min(lats), max(lats)
    min_lng, max_lng = min(lngs), max(lngs)
    lat_span = max(max_lat - min_lat, 0.001)
    lng_span = max(max_lng - min_lng, 0.001)
    for item in items:
        item["map_point"] = {
            "x": round(8 + ((item["lng"] - min_lng) / lng_span) * 84, 2),
            "y": round(88 - ((item["lat"] - min_lat) / lat_span) * 76, 2),
        }


def build_map_payload(
    hospitals: Iterable[Mapping[str, Any]],
    *,
    region_code: str,
    region_name: str,
    region_pack_version: str,
    user_lat: float | None = None,
    user_lng: float | None = None,
) -> dict[str, Any]:
    if (user_lat is None) != (user_lng is None):
        raise MapLocationError("lat 和 lng 必须同时提供")

    items: list[dict[str, Any]] = []
    for source in hospitals:
        lat, lng = source.get("lat"), source.get("lng")
        if not isinstance(lat, (int, float)) or not isinstance(lng, (int, float)):
            continue
        if not math.isfinite(float(lat)) or not math.isfinite(float(lng)):
            continue
        item = {
            "id": source.get("id"),
            "name": source.get("name"),
            "alias": source.get("alias"),
            "level": source.get("level"),
            "type": source.get("type"),
            "address": source.get("address"),
            "lat": float(lat),
            "lng": float(lng),
            "emergency": source.get("emergency") is True,
            "marker_type": "EMERGENCY_CAPABLE" if source.get("emergency") is True else "NORMAL",
            "map_reason": (
                "接口标记含急诊字段；不等于实时急诊可用性。"
                if source.get("emergency") is True
                else "公开资源地图索引；不代表官方推荐。"
            ),
            "distance_km": None,
        }
        if user_lat is not None and user_lng is not None:
            item["distance_km"] = _distance_km(user_lat, user_lng, float(lat), float(lng))
        items.append(item)

    _project_points(items)
    if user_lat is not None:
        items.sort(key=lambda item: (item["distance_km"], str(item.get("name") or "")))

    return {
        "region": {
            "code": region_code,
            "name": region_name,
            "region_pack_version": region_pack_version,
        },
        "items": items,
        "count": len(items),
        "source": "legacy_catalog_pending_provenance",
        "distance_method": "haversine_straight_line_km" if user_lat is not None else None,
        "notice": "地图为资源位置示意，不是导航地图；医院来源逐字段 provenance 仍在迁移中。",
    }


class MapViewApplicationService:
    """Compose the public map projection from the active region and hospital catalog."""

    def __init__(self, *, hospitals: Callable[[], Iterable[Mapping[str, Any]]], region: Callable[[str], Any]) -> None:
        self._hospitals = hospitals
        self._region = region

    def build(
        self,
        *,
        region_code: str,
        user_lat: float | None = None,
        user_lng: float | None = None,
    ) -> dict[str, Any]:
        region = self._region(region_code)
        return build_map_payload(
            self._hospitals(),
            region_code=region_code,
            region_name=region.name if region else "常州市",
            region_pack_version=region.version if region else "unknown",
            user_lat=user_lat,
            user_lng=user_lng,
        )
