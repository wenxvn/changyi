from __future__ import annotations

from unittest import TestCase

from backend.app.application.recommendation import (
    RecommendationApplicationService,
    RecommendationContext,
)
from backend.app.domain.recommendation.routing_preferences import normalize_routing_preferences
from backend.app.domain.triage.safety_gate import triage_status_from_legacy


def _service():
    def enhanced_doctors(condition, scenario, **kwargs):
        return [
            {"doctor": {"id": 1, "name": "收藏医生"}, "match_score": 0.78, "reasons": []},
            {"doctor": {"id": 2, "name": "普通医生"}, "match_score": 0.80, "reasons": []},
        ]

    return RecommendationApplicationService(
        analyze_triage=lambda condition, scenario, followup=None: {
            "level": "emergency",
            "severity_bucket": "大病/重症风险",
            "recommended_scenario": "surgery",
            "matched_department": "急诊医学科",
        }
        if "喘不上气" in condition
        else {
            "level": "routine",
            "severity_bucket": "小病/常见病倾向",
            "recommended_scenario": "common",
            "matched_department": "呼吸内科",
        },
        resource_strategy=lambda triage, expert: {"visit_path": "assistive"},
        recommend_hospitals=lambda *args, **kwargs: [],
        enhanced_recommend_doctors=enhanced_doctors,
        legacy_recommend_doctors=lambda condition: [],
        match_department=lambda condition: "呼吸内科",
        build_public_htriage=lambda triage: {},
        predict_disease=lambda *args, **kwargs: {},
        publish_safety_first=lambda payload, triage: payload,
        enhanced_weights={
            "common": {"specialty": 0.5, "access": 0.5},
            "complex": {"specialty": 0.5, "access": 0.5},
            "surgery": {"specialty": 0.5, "access": 0.5},
            "first_visit": {"specialty": 0.5, "access": 0.5},
        },
        hospital_weights={"routine": {}},
        ranking_model="test",
        has_real_doctors=True,
        real_doctor_count=2,
    )


class RoutingPreferenceTests(TestCase):
    def test_defaults_are_off_and_unknown_values_are_normalized(self):
        self.assertEqual(
            normalize_routing_preferences(None),
            {
                "district_preference": "any_district",
                "distance_preference": "distance_flexible",
                "continuity_preference": False,
            },
        )
        self.assertEqual(
            normalize_routing_preferences({
                "district_preference": "prefer_home_district",
                "distance_preference": "prefer_nearby",
                "continuity_preference": True,
            })["continuity_preference"],
            True,
        )

    def test_emergency_stays_emergency_with_nearby_preference(self):
        service = _service()
        payload = service.build(
            RecommendationContext(
                condition="喘不上气",
                scenario="common",
                district=None,
                expert_preference="system",
                user_lat=None,
                user_lng=None,
                routing_preferences={"distance_preference": "prefer_nearby"},
            ),
            enhanced=True,
            safety_first=False,
        )
        self.assertEqual(triage_status_from_legacy(payload["triage"]).value, "EMERGENCY")
        self.assertEqual(payload["triage"]["level"], "emergency")
        self.assertEqual(payload["routing_preferences"]["distance_preference"], "prefer_nearby")

    def test_continuity_boosts_favorites_only_when_enabled(self):
        service = _service()
        off = service.build(
            RecommendationContext(
                condition="轻微咳嗽",
                scenario="common",
                district=None,
                expert_preference="system",
                user_lat=31.77,
                user_lng=119.95,
                favorite_doctor_ids=(1,),
            ),
            enhanced=True,
            safety_first=False,
        )
        on = service.build(
            RecommendationContext(
                condition="轻微咳嗽",
                scenario="common",
                district=None,
                expert_preference="system",
                user_lat=31.77,
                user_lng=119.95,
                routing_preferences={"continuity_preference": True},
                favorite_doctor_ids=(1,),
            ),
            enhanced=True,
            safety_first=False,
        )
        off_by_id = {item["doctor"]["id"]: item for item in off["recommended_doctors"]}
        on_by_id = {item["doctor"]["id"]: item for item in on["recommended_doctors"]}
        self.assertEqual(on["recommended_doctors"][0]["doctor"]["id"], 1)
        self.assertEqual(off["recommended_doctors"][0]["doctor"]["id"], 2)
        self.assertGreater(on_by_id[1]["match_score"], off_by_id[1]["match_score"])
        self.assertEqual(on_by_id[2]["match_score"], off_by_id[2]["match_score"])
        self.assertIn("已按连续复诊偏好优先展示收藏医生", on_by_id[1]["reasons"])
        self.assertNotIn("已按连续复诊偏好优先展示收藏医生", off_by_id[1]["reasons"])
