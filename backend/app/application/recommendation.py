"""Application orchestration for legacy and versioned recommendations.

The service receives an already-resolved context and composes existing
recommendation functions. Candidate generation, scoring, traffic handling,
and medical policy remain outside this module.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

from backend.app.domain.recommendation.features import EXCLUDED_EVIDENCE_NOTICES
from backend.app.domain.recommendation.scoring import rebalance_weights
from backend.app.domain.recommendation.routing_preferences import normalize_routing_preferences
from backend.app.domain.recommendation.visit_intent import ranking_scenario_for_visit_intent


@dataclass(frozen=True)
class RecommendationContext:
    condition: str
    scenario: str
    district: str | None
    expert_preference: str
    user_lat: float | None
    user_lng: float | None
    location_source: str = "unknown"
    followup_answers: tuple[dict[str, Any], ...] = ()
    visit_intent: str | None = None
    routing_preferences: dict[str, Any] | None = None
    favorite_doctor_ids: tuple[int, ...] = ()


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
        if context.followup_answers:
            triage = dict(self.analyze_triage(context.condition, context.scenario, context.followup_answers))
        else:
            triage = dict(self.analyze_triage(context.condition, context.scenario))
        # Visit intent never replaces triage rules; it only picks ranking weights.
        triage_scenario = triage.get("recommended_scenario") or context.scenario
        ranking_scenario = ranking_scenario_for_visit_intent(context.visit_intent, triage_scenario)
        effective_scenario = ranking_scenario
        preferences = normalize_routing_preferences(context.routing_preferences)
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
        if preferences["continuity_preference"] and context.favorite_doctor_ids:
            favorite_ids = set(context.favorite_doctor_ids)
            boosted = []
            for item in doctors:
                doctor_id = (item.get("doctor") or {}).get("id")
                if doctor_id in favorite_ids:
                    item = dict(item)
                    item["match_score"] = round(min(1.0, float(item.get("match_score") or 0.0) + 0.05), 4)
                    notes = list(item.get("reasons") or [])
                    notes.append("已按连续复诊偏好优先展示收藏医生")
                    item["reasons"] = notes[:4]
                boosted.append(item)
            doctors = sorted(boosted, key=lambda row: -float(row.get("match_score") or 0.0))
        matched_department = triage.get("matched_department") or self.match_department(context.condition)
        doctor_weights = self.enhanced_weights.get(effective_scenario, self.enhanced_weights["surgery"])
        if preferences["distance_preference"] == "prefer_nearby" and "access" in doctor_weights:
            doctor_weights = {**doctor_weights, "access": doctor_weights.get("access", 0.0) + 0.04}
            total = sum(doctor_weights.values()) or 1.0
            doctor_weights = {key: round(value / total, 6) for key, value in doctor_weights.items()}
        if context.user_lat is None or context.user_lng is None:
            doctor_weights = rebalance_weights(doctor_weights, {"access"})
        hospital_weights = (
            hospitals[0].get("ranking_weights")
            if hospitals and isinstance(hospitals[0].get("ranking_weights"), Mapping)
            else self.hospital_weights.get(triage.get("level", "routine"), self.hospital_weights["routine"])
        )
        result: dict[str, Any] = {
            "condition": context.condition,
            "scenario": context.scenario,
            "visit_intent": context.visit_intent,
            "routing_preferences": preferences,
            "effective_scenario": effective_scenario,
            "triage_scenario": triage_scenario,
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
                "source": context.location_source,
            },
            "feature_availability": {
                "location": context.user_lat is not None and context.user_lng is not None,
                "distance": context.user_lat is not None and context.user_lng is not None,
                "transit": context.user_lat is not None and context.user_lng is not None,
            },
            "followup_answers": list(context.followup_answers),
            "recommended_hospitals": hospitals,
            "recommended_doctors": doctors,
            "excluded_evidence": list(EXCLUDED_EVIDENCE_NOTICES),
            "weights_used": doctor_weights,
            "hospital_weights_used": hospital_weights,
            "ranking_model": self.ranking_model,
            "data_source": "real_data" if enhanced else ("real" if self.has_real_doctors else "mock"),
        }
        if context.user_lat is None or context.user_lng is None:
            result["ranking_notice"] = "未提供精确位置，本次排序未使用距离和交通可达性；如需比较到院距离，请主动提供定位或选择区域。"
        if not enhanced:
            result["total_real_doctors"] = self.real_doctor_count
        if safety_first:
            return dict(self.publish_safety_first(result, triage))
        return result
