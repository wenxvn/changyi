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


VISIT_INTENTS = {
    "first_visit",
    "follow_up",
    "review_results",
    "procedure_consult",
    "unsure",
}


@dataclass(frozen=True)
class RecommendationRequest:
    condition: str
    scenario: str
    district: str | None
    expert_preference: str
    region_code: str
    lat: float | None = None
    lng: float | None = None
    location_source: str = "unknown"
    followup_answers: tuple[dict[str, Any], ...] = ()
    visit_intent: str | None = None
    routing_preferences: dict[str, Any] | None = None
    favorite_doctor_ids: tuple[int, ...] = ()

    @classmethod
    def parse(cls, payload: Any, *, region_code: str = "320400") -> "RecommendationRequest":
        if not isinstance(payload, dict):
            raise RequestValidationError("INVALID_JSON", "请求体必须是 JSON 对象")

        allowed = {
            "condition", "scenario", "district", "expert_preference", "region_code",
            "lat", "lng", "location_source", "followup_answers", "visit_intent",
            "routing_preferences", "favorite_doctor_ids",
        }
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

        raw_visit_intent = payload.get("visit_intent")
        if raw_visit_intent is None or raw_visit_intent == "":
            visit_intent = None
        else:
            visit_intent = str(raw_visit_intent)
            if visit_intent not in VISIT_INTENTS:
                raise RequestValidationError("INVALID_VISIT_INTENT", "visit_intent 不在已声明范围内")

        expert_preference = str(payload.get("expert_preference") or "system")
        if expert_preference not in {"system", "no_expert", "wish_expert", "must_expert", "named_followup"}:
            raise RequestValidationError("INVALID_EXPERT_PREFERENCE", "expert_preference 无效")

        raw_district = payload.get("district")
        if raw_district is None or raw_district == "":
            district = None
        elif not isinstance(raw_district, str) or not raw_district.strip():
            raise RequestValidationError("INVALID_DISTRICT", "district 必须是字符串或省略")
        else:
            district = raw_district.strip()

        raw_prefs = payload.get("routing_preferences")
        if raw_prefs is None:
            routing_preferences = None
        elif not isinstance(raw_prefs, dict):
            raise RequestValidationError("INVALID_ROUTING_PREFERENCES", "routing_preferences 必须是对象")
        else:
            routing_preferences = raw_prefs

        raw_favorites = payload.get("favorite_doctor_ids")
        if raw_favorites is None:
            favorite_doctor_ids: tuple[int, ...] = ()
        elif not isinstance(raw_favorites, list):
            raise RequestValidationError("INVALID_FAVORITE_DOCTOR_IDS", "favorite_doctor_ids 必须是数组")
        else:
            parsed_favorites: list[int] = []
            for item in raw_favorites[:50]:
                try:
                    doctor_id = int(item)
                except (TypeError, ValueError) as exc:
                    raise RequestValidationError("INVALID_FAVORITE_DOCTOR_IDS", "favorite_doctor_ids 必须是整数") from exc
                if doctor_id > 0:
                    parsed_favorites.append(doctor_id)
            favorite_doctor_ids = tuple(parsed_favorites)

        lat, lng = _parse_coordinates(payload.get("lat"), payload.get("lng"))
        location_source = _parse_location_source(payload.get("location_source"), district, lat, lng)
        followup_answers = _parse_followup_answers(payload.get("followup_answers"))
        return cls(
            condition=condition,
            scenario=scenario,
            district=district,
            expert_preference=expert_preference,
            region_code=requested_region,
            lat=lat,
            lng=lng,
            location_source=location_source,
            followup_answers=followup_answers,
            visit_intent=visit_intent,
            routing_preferences=routing_preferences,
            favorite_doctor_ids=favorite_doctor_ids,
        )


def _parse_coordinates(raw_lat: Any, raw_lng: Any) -> tuple[float | None, float | None]:
    if raw_lat is None and raw_lng is None:
        return None, None
    if raw_lat is None or raw_lng is None:
        raise RequestValidationError("INVALID_LOCATION", "lat 和 lng 必须同时提供")
    try:
        lat, lng = float(raw_lat), float(raw_lng)
    except (TypeError, ValueError) as exc:
        raise RequestValidationError("INVALID_LOCATION", "lat/lng 必须是数字") from exc
    if not (-90 <= lat <= 90 and -180 <= lng <= 180):
        raise RequestValidationError("INVALID_LOCATION", "lat/lng 超出地理坐标范围")
    return lat, lng


def _parse_location_source(
    raw_source: Any,
    district: str | None,
    lat: float | None,
    lng: float | None,
) -> str:
    if raw_source is None or raw_source == "":
        if lat is not None:
            return "geolocation"
        if district:
            return "district"
        return "unknown"
    if raw_source not in {"unknown", "geolocation", "district"}:
        raise RequestValidationError("INVALID_LOCATION_SOURCE", "location_source 无效")
    if raw_source == "geolocation" and lat is None:
        raise RequestValidationError("INVALID_LOCATION", "geolocation 必须同时提供 lat/lng")
    if raw_source == "district" and district is None:
        raise RequestValidationError("INVALID_DISTRICT", "district 来源必须提供 district")
    if raw_source == "unknown" and (district is not None or lat is not None):
        raise RequestValidationError("INVALID_LOCATION_SOURCE", "unknown 位置来源不能携带 district 或坐标")
    if raw_source == "geolocation" and district is not None:
        raise RequestValidationError("INVALID_LOCATION_SOURCE", "精确定位请求不能同时声明 district")
    if raw_source == "district" and lat is not None:
        raise RequestValidationError("INVALID_LOCATION_SOURCE", "区域估算请求不能同时声明精确坐标")
    return str(raw_source)


def _parse_followup_answers(raw_answers: Any) -> tuple[dict[str, Any], ...]:
    if raw_answers is None:
        return ()
    if not isinstance(raw_answers, list) or len(raw_answers) > 32:
        raise RequestValidationError("INVALID_FOLLOWUP_ANSWERS", "followup_answers 必须是不超过 32 项的数组")

    parsed: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for answer in raw_answers:
        if not isinstance(answer, dict):
            raise RequestValidationError("INVALID_FOLLOWUP_ANSWERS", "每个 followup answer 必须是 JSON 对象")
        if set(answer) - {"question_id", "value", "text_answer"}:
            raise RequestValidationError("INVALID_FOLLOWUP_ANSWERS", "followup answer 包含未声明字段")
        question_id = answer.get("question_id")
        if not isinstance(question_id, str) or not question_id.strip() or len(question_id) > 100:
            raise RequestValidationError("INVALID_FOLLOWUP_ANSWERS", "question_id 必须是非空字符串")
        question_id = question_id.strip()
        if question_id in seen_ids:
            raise RequestValidationError("INVALID_FOLLOWUP_ANSWERS", "question_id 不能重复")
        seen_ids.add(question_id)
        value = answer.get("value")
        text_answer = answer.get("text_answer")
        if (value is None) == (text_answer is None):
            raise RequestValidationError("INVALID_FOLLOWUP_ANSWERS", "value 与 text_answer 必须二选一")
        selected = value if value is not None else text_answer
        if not isinstance(selected, str) or not selected.strip() or len(selected) > 500:
            raise RequestValidationError("INVALID_FOLLOWUP_ANSWERS", "followup answer 内容无效")
        parsed.append({
            "question_id": question_id,
            "value": value.strip() if isinstance(value, str) else None,
            "text_answer": text_answer.strip() if isinstance(text_answer, str) else None,
        })
    return tuple(parsed)
