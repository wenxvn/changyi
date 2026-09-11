"""Application orchestration for legacy and versioned recommendations.

The service receives an already-resolved context and composes existing
recommendation functions. Candidate generation, scoring, traffic handling,
and medical policy remain outside this module.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RecommendationContext:
    condition: str
    scenario: str
    district: str
    expert_preference: str
    user_lat: float
    user_lng: float


@dataclass(frozen=True)
class RecommendationApplicationService:
    analyze_triage: Callable[[str, str], Mapping[str, Any]]
    resource_strategy: Callable[[Mapping[str, Any], str], Mapping[str, Any]]
    recommend_hospitals: Callable[..., list[dict[str, Any]]]
    enhanced_recommend_doctors: Callable[..., list[dict[str, Any]]]
    legacy_recommend_doctors: Callable[..., list[dict[str, Any]]]
    match_department: Callable[[str], str | None]
    build_public_htriage: Callable[[Mapping[str, Any]], Mapping[str, Any]]
    predict_disease: Callable[..., Mapping[str, Any]]
    publish_safety_first: Callable[[Mapping[str, Any], Mapping[str, Any]], Mapping[str, Any]]
    enhanced_weights: Mapping[str, Mapping[str, float]]
    hospital_weights: Mapping[str, Mapping[str, float]]
    ranking_model: str
    has_real_doctors: bool
    real_doctor_count: int

    def build(
        self,
        context: RecommendationContext,
        *,
        doctor_top_n: int = 8,
        enhanced: bool = False,
        safety_first: bool = False,
    ) -> dict[str, Any]:
        triage = dict(self.analyze_triage(context.condition, context.scenario))
        effective_scenario = triage.get("recommended_scenario") or context.scenario
        resource_strategy = self.resource_strategy(triage, context.expert_preference)
        hospitals = self.recommend_hospitals(
            context.condition,
            context.user_lat,
            context.user_lng,
            triage=triage,
        )
        if enhanced or self.has_real_doctors:
            doctors = self.enhanced_recommend_doctors(
                context.condition,
                effective_scenario,
                top_n=doctor_top_n,
                user_lat=context.user_lat,
                user_lng=context.user_lng,
                triage=triage,
                expert_preference=context.expert_preference,
            )
        else:
            doctors = self.legacy_recommend_doctors(context.condition)
        matched_department = triage.get("matched_department") or self.match_department(context.condition)
        result: dict[str, Any] = {
            "condition": context.condition,
            "scenario": context.scenario,
            "effective_scenario": effective_scenario,
            "expert_preference": context.expert_preference,
            "resource_strategy": resource_strategy,
            "triage": triage,
            "htriage_analysis": self.build_public_htriage(triage),
            "disease_prediction": self.predict_disease(context.condition, details=True),
            "matched_department": matched_department,
            "user_location": {
                "district": context.district,
                "lat": context.user_lat,
                "lng": context.user_lng,
            },
            "recommended_hospitals": hospitals,
            "recommended_doctors": doctors,
            "weights_used": self.enhanced_weights.get(effective_scenario, self.enhanced_weights["surgery"]),
            "hospital_weights_used": self.hospital_weights.get(triage.get("level", "routine"), self.hospital_weights["routine"]),
            "ranking_model": self.ranking_model,
            "data_source": "real_data" if enhanced else ("real" if self.has_real_doctors else "mock"),
        }
        if not enhanced:
            result["total_real_doctors"] = self.real_doctor_count
        if safety_first:
            return dict(self.publish_safety_first(result, triage))
        return result
