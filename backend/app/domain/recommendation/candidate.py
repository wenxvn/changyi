"""Pure recommendation candidate result builders.

The legacy application still owns candidate discovery and scoring inputs.
These builders only turn explicit, already-computed values into the stable
doctor recommendation payload and its short explanation list.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
import math
from typing import Any

from .candidates import hospital_supports_emergency_fallback, resolve_hospital_candidate_match
from .features import (
    continuity_score,
    fairness_score,
    hospital_availability_score,
    hospital_quality_score,
    hospital_recommend_reasons,
    hospital_risk_penalty,
    hospital_strength_for_department,
    special_population_fit,
)
from .scoring import clamp, score_hospital_candidate


def doctor_recommendation_reasons(
    specialty_score: float,
    surgery_score: float,
    academic_score: float,
    access_score: float,
    availability_score: float,
    penalty_details: Sequence[dict[str, Any]],
    resource_notes: Sequence[str],
    *,
    expert_preference: str = "system",
) -> list[str]:
    reasons = []
    if specialty_score >= 0.85:
        reasons.append("科室/专长匹配")
    if surgery_score >= 0.55:
        reasons.append("临床经验较强")
    if access_score >= 0.8:
        reasons.append("距离可及性较好")
    if availability_score >= 0.7:
        reasons.append("医院承载能力较好")
    if expert_preference == "wish_expert":
        reasons.append("已按“希望优先专家”偏好综合排序")
    elif expert_preference == "no_expert":
        reasons.append("已按“不特别需要专家”偏好综合排序")
    if penalty_details:
        reasons.append("已应用资源错配惩罚")
    reasons.extend(resource_notes)
    return reasons[:4] or ["按专科匹配、临床经历和可及性综合排序"]


def build_doctor_recommendation_result(
    *,
    doctor: dict[str, Any],
    total_score: float,
    surgery_score: float,
    specialty_score: float,
    academic_score: float,
    title_score: float,
    hospital_score: float,
    access_score: float,
    availability_score: float,
    continuity_score: float,
    fairness_score: float,
    risk_penalty: float,
    mismatch_penalty: float,
    penalty_details: list[dict[str, Any]],
    matched_dept: str | None,
    ranking_model: str,
    hospital_distance: float | None,
    emergency_priority_score: float,
    resource_tier: str,
    visit_path: str | None,
    resource_cap: float,
    resource_notes: Sequence[str],
    expert_preference: str = "system",
) -> dict[str, Any]:
    reasons = doctor_recommendation_reasons(
        specialty_score,
        surgery_score,
        academic_score,
        access_score,
        availability_score,
        penalty_details,
        resource_notes,
        expert_preference=expert_preference,
    )
    return {
        "doctor": doctor,
        "match_score": round(total_score, 4),
        "scores": {
            "surgery": round(surgery_score, 4),
            "specialty": round(specialty_score, 4),
            "academic": round(academic_score, 4),
            "title": round(title_score, 4),
            "hospital": round(hospital_score, 4),
            "access": round(access_score, 4),
            "availability": round(availability_score, 4),
            "continuity": round(continuity_score, 4),
            "fairness": round(fairness_score, 4),
            "risk_penalty": round(risk_penalty + mismatch_penalty, 4),
            "mismatch_penalty": round(mismatch_penalty, 4),
        },
        "capability_indices": {
            "DCI": round(specialty_score, 4),
            "CEI": round(surgery_score, 4),
            "ACI": round(academic_score, 4),
            "HCI": round(hospital_score, 4),
            "AAI": round(access_score, 4),
        },
        "penalty_breakdown": penalty_details,
        "matched_dept": matched_dept,
        "reasons": reasons,
        "ranking_model": ranking_model,
        "hospital_distance_km": hospital_distance,
        "emergency_priority_score": round(emergency_priority_score, 4),
        "resource_tier": resource_tier,
        "visit_path": visit_path,
        "resource_cap": round(resource_cap, 4),
    }


def build_hospital_recommendation_result(
    *,
    hospital: dict[str, Any],
    distance: float | None,
    accessibility: float,
    strength_score: float,
    composite_score: float,
    matched_department: str | None,
    feature_scores: dict[str, Any],
    traffic_access: dict[str, Any],
    ranking_weights: dict[str, float],
    ranking_model: str,
    explanations: list[str],
) -> dict[str, Any]:
    """Build the stable hospital recommendation result from explicit values."""

    return {
        "hospital": hospital,
        "distance": distance,
        "dist_score": round(accessibility * 100, 1),
        "strength_score": strength_score,
        "composite_score": composite_score,
        "matched_department": matched_department,
        "feature_scores": feature_scores,
        "traffic_access": traffic_access,
        "ranking_weights": ranking_weights,
        "ranking_model": ranking_model,
        "explanations": explanations,
    }


def compose_hospital_candidate(
    *,
    hospital: dict[str, Any],
    condition: str,
    target_dept: str | None,
    triage: Mapping[str, Any] | None,
    triage_level: str,
    distance: float | None,
    accessibility: float,
    traffic_access: dict[str, Any],
    ranking_weights: Mapping[str, float],
    ranking_model: str,
    user_district: str | None = None,
    district_preference: str | None = None,
) -> dict[str, Any]:
    """Compose one hospital candidate from explicit prepared context."""

    clinical = hospital_strength_for_department(hospital, target_dept)
    population_fit = special_population_fit(condition, hospital)
    clinical = clamp(clinical * 0.82 + population_fit * 0.18)
    availability = hospital_availability_score(hospital, triage_level)
    quality = hospital_quality_score(hospital)
    continuity = continuity_score(condition, target_dept, hospital)
    fairness = fairness_score(condition, hospital, distance, triage_level)
    emergency = 1.0 if hospital.get("emergency") else 0.55
    risk_penalty = hospital_risk_penalty(condition, target_dept, hospital, triage or {})
    strength_score, matched_department = resolve_hospital_candidate_match(hospital, target_dept)
    composite, feature_scores = score_hospital_candidate(
        clinical=clinical,
        availability=availability,
        accessibility=accessibility,
        continuity=continuity,
        quality=quality,
        fairness=fairness,
        emergency=emergency,
        risk_penalty=risk_penalty,
        weights=ranking_weights,
        traffic_access=traffic_access,
    )
    matched_department = matched_department or target_dept
    return build_hospital_recommendation_result(
        hospital=hospital,
        distance=distance,
        accessibility=accessibility,
        strength_score=strength_score,
        composite_score=composite,
        matched_department=matched_department,
        feature_scores=feature_scores,
        traffic_access=traffic_access,
        ranking_weights=ranking_weights,
        ranking_model=ranking_model,
        explanations=hospital_recommend_reasons(
            hospital,
            feature_scores,
            distance,
            matched_department,
            triage_level,
            district=user_district,
            district_preference=district_preference,
        ),
    )


def build_hospital_candidates(
    *,
    hospitals: Sequence[dict[str, Any]],
    condition: str,
    target_dept: str | None,
    triage: Mapping[str, Any] | None,
    triage_level: str,
    access_context: str,
    user_lat: float | None,
    user_lng: float | None,
    distance_fn: Callable[[float, float, float, float], float],
    access_score_fn: Callable[..., float],
    traffic_access_fn: Callable[[Mapping[str, Any]], dict[str, Any]],
    compose_fn: Callable[..., dict[str, Any]],
    ranking_weights: Mapping[str, float],
    ranking_model: str,
    user_district: str | None = None,
    district_preference: str | None = None,
) -> list[dict[str, Any]]:
    """Build hospital candidates from explicit context and infrastructure callbacks."""

    results = []
    uses_traffic_in_ranking = access_context not in ("emergency", "urgent")
    ranking_policy = (
        "普通/初诊场景使用公交站点和出租车样本辅助可达性测算"
        if uses_traffic_in_ranking
        else "急症/较重病情不使用公交/出租车权重"
    )
    for hospital in hospitals:
        distance = None
        if user_lat is not None and user_lng is not None:
            distance = distance_fn(user_lat, user_lng, hospital["lat"], hospital["lng"])
        accessibility = access_score_fn(hospital, user_lat, user_lng, access_context)
        traffic_access = traffic_access_fn(hospital)
        quality_rankable = traffic_access.get("rankable", True) is not False
        traffic_access["used_in_ranking"] = bool(
            uses_traffic_in_ranking and distance is not None and quality_rankable
        )
        if not quality_rankable:
            traffic_access["ranking_policy"] = (
                "交通数据未通过质量门，可达性按直线距离估算；站点信息仅作参考"
            )
        else:
            traffic_access["ranking_policy"] = ranking_policy
        results.append(
            compose_fn(
                hospital=hospital,
                condition=condition,
                target_dept=target_dept,
                triage=triage,
                triage_level=triage_level,
                distance=distance,
                accessibility=accessibility,
                traffic_access=traffic_access,
                ranking_weights=ranking_weights,
                ranking_model=ranking_model,
                user_district=user_district,
                district_preference=district_preference,
            )
        )
    return results


def build_emergency_doctor_fallback_candidates(
    *,
    doctors: Sequence[dict[str, Any]],
    matched_dept: str | None,
    ranking_model: str,
    user_lat: float | None,
    user_lng: float | None,
    hospital_for_doctor: Callable[[Mapping[str, Any]], Mapping[str, Any] | None],
    access_score_fn: Callable[..., float],
    distance_fn: Callable[[float, float, float, float], float],
    score_fn: Callable[..., Mapping[str, Any]],
    result_fn: Callable[..., dict[str, Any]],
) -> list[dict[str, Any]]:
    """Build the legacy emergency-only doctor fallback candidate list."""

    results = []
    for doctor in doctors:
        hospital = hospital_for_doctor(doctor)
        if not hospital_supports_emergency_fallback(hospital):
            continue
        access_score = access_score_fn(hospital, user_lat, user_lng, "urgent")
        hospital_distance = None
        if user_lat is not None and user_lng is not None:
            hospital_distance = distance_fn(
                float(user_lat),
                float(user_lng),
                hospital["lat"],
                hospital["lng"],
            )
        fallback_scores = score_fn(
            doctor=doctor,
            hospital=hospital,
            access_score=access_score,
            hospital_distance=hospital_distance,
        )
        results.append(
            result_fn(
                doctor=doctor,
                matched_dept=matched_dept,
                ranking_model=ranking_model,
                **fallback_scores,
            )
        )
    return results


def build_emergency_doctor_fallback_result(
    *,
    doctor: dict[str, Any],
    surgery_score: float,
    title_score: float,
    quality_score: float,
    access_score: float,
    availability_score: float,
    matched_dept: str | None,
    ranking_model: str,
    hospital_distance: float | None,
    emergency_priority_score: float,
) -> dict[str, Any]:
    """Build the legacy emergency-only doctor fallback payload.

    This is a result assembly boundary only. Candidate traversal and scoring
    are handled by explicit domain functions; emergency ordering remains
    owned by the compatibility application.
    """

    return {
        "doctor": doctor,
        "match_score": round(emergency_priority_score, 4),
        "scores": {
            "surgery": round(surgery_score, 4),
            "specialty": 0.35,
            "academic": 0.0,
            "title": round(title_score, 4),
            "hospital": round(quality_score, 4),
            "access": round(access_score, 4),
            "availability": round(availability_score, 4),
            "continuity": 0.0,
            "fairness": 0.0,
            "risk_penalty": 0.0,
        },
        "matched_dept": matched_dept,
        "reasons": ["急症兜底召回", "优先支持急诊医院", "综合医生资历与到院距离"],
        "ranking_model": ranking_model,
        "hospital_distance_km": hospital_distance,
        "emergency_priority_score": round(emergency_priority_score, 4),
    }


def score_emergency_doctor_fallback(
    *,
    doctor: Mapping[str, Any],
    hospital: Mapping[str, Any],
    access_score: float,
    hospital_distance: float | None,
) -> dict[str, Any]:
    """Calculate the legacy emergency-only doctor fallback scores."""

    surgery_count = doctor.get("surgery_count")
    if surgery_count:
        surgery_score = min(1.0, math.log(surgery_count + 1) / math.log(7000))
    elif doctor.get("surgery_count_note"):
        surgery_score = 0.35
    else:
        surgery_score = 0.18

    title = doctor.get("title", "") or ""
    if "主任医师" in title and "副主任" not in title:
        title_score = 1.0
    elif "副主任医师" in title:
        title_score = 0.78
    elif "主治医师" in title:
        title_score = 0.50
    else:
        title_score = 0.34

    quality_score = hospital_quality_score(hospital)
    availability_score = hospital_availability_score(hospital, "urgent")
    emergency_priority_score = clamp(
        access_score * 0.38
        + title_score * 0.22
        + quality_score * 0.24
        + surgery_score * 0.16
    )
    return {
        "surgery_score": surgery_score,
        "title_score": title_score,
        "quality_score": quality_score,
        "access_score": access_score,
        "availability_score": availability_score,
        "hospital_distance": hospital_distance,
        "emergency_priority_score": emergency_priority_score,
    }
