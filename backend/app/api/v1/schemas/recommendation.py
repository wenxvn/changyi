"""Validation for the single versioned recommendation request."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class RequestValidationError(ValueError):
    def __init__(self, code: str, message: str, details: Any = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details


@dataclass(frozen=True)
class RecommendationRequest:
    condition: str
    scenario: str
    district: str
    expert_preference: str
    region_code: str
    lat: float | None = None
    lng: float | None = None

    @classmethod
    def parse(cls, payload: Any, *, region_code: str = "320400") -> "RecommendationRequest":
        if not isinstance(payload, dict):
            raise RequestValidationError("INVALID_JSON", "请求体必须是 JSON 对象")

        allowed = {"condition", "scenario", "district", "expert_preference", "region_code", "lat", "lng"}
        unexpected = sorted(set(payload) - allowed)
        if unexpected:
            raise RequestValidationError("UNEXPECTED_FIELD", "请求包含未声明字段", unexpected)

        condition = payload.get("condition")
        if not isinstance(condition, str) or not condition.strip():
            raise RequestValidationError("INVALID_CONDITION", "condition 不能为空")
        condition = condition.strip()
        if len(condition) > 2000:
            raise RequestValidationError("INVALID_CONDITION", "condition 超过 2000 个字符")

        requested_region = str(payload.get("region_code") or region_code)
        if requested_region != region_code:
            raise RequestValidationError("REGION_NOT_ACTIVE", "当前仅支持已激活的常州 Region Pack", {"region_code": requested_region})

        scenario = str(payload.get("scenario") or "common")
        if scenario not in {"common", "complex", "surgery", "first_visit"}:
            raise RequestValidationError("INVALID_SCENARIO", "scenario 不在已声明的就诊场景范围内")

        expert_preference = str(payload.get("expert_preference") or "system")
        if expert_preference not in {"system", "no_expert", "wish_expert", "must_expert", "named_followup"}:
            raise RequestValidationError("INVALID_EXPERT_PREFERENCE", "expert_preference 无效")

        district = payload.get("district") or "天宁区"
        if not isinstance(district, str) or not district.strip():
            raise RequestValidationError("INVALID_DISTRICT", "district 必须是非空字符串")

        lat, lng = _parse_coordinates(payload.get("lat"), payload.get("lng"))
        return cls(condition, scenario, district.strip(), expert_preference, requested_region, lat, lng)


def _parse_coordinates(raw_lat: Any, raw_lng: Any) -> tuple[float | None, float | None]:
    if raw_lat is None and raw_lng is None:
        return None, None
    if raw_lat is None or raw_lng is None:
        raise RequestValidationError("INVALID_LOCATION", "lat 和 lng 必须同时提供")
    try:
        lat, lng = float(raw_lat), float(raw_lng)
    except (TypeError, ValueError) as exc:
        raise RequestValidationError("INVALID_LOCATION", "lat/lng 必须是数字") from exc
    if not -90 <= lat <= 90 or not -180 <= lng <= 180:
        raise RequestValidationError("INVALID_LOCATION", "lat/lng 超出地理坐标范围")
    return lat, lng
