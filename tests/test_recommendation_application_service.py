from __future__ import annotations

from unittest import TestCase

from backend.app.application.recommendation import (
    DistanceRerankApplicationService,
    RecommendationApplicationService,
    RecommendationContext,
)


class RecommendationApplicationServiceTests(TestCase):
    def make_service(self, *, has_real_doctors=False):
        calls: list[str] = []

        def analyze(condition, scenario):
            calls.append(f"analyze:{condition}:{scenario}")
            return {"level": "routine", "recommended_scenario": "common", "matched_department": "内科"}

        def hospitals(condition, lat, lng, *, triage):
            calls.append(f"hospitals:{lat}:{lng}")
            return [{"hospital": {"id": 1}}]

        def enhanced_doctors(condition, scenario, **kwargs):
            calls.append(f"enhanced-doctors:{scenario}:{kwargs['top_n']}")
            return [{"doctor": {"id": 1001}}]

        def legacy_doctors(condition):
            calls.append("legacy-doctors")
            return [{"doctor": {"id": 1}}]

        service = RecommendationApplicationService(
            analyze_triage=analyze,
            resource_strategy=lambda triage, preference: {"title": preference},
            recommend_hospitals=hospitals,
            enhanced_recommend_doctors=enhanced_doctors,
            legacy_recommend_doctors=legacy_doctors,
            match_department=lambda condition: "内科",
            build_public_htriage=lambda triage: {"status": triage["level"]},
            predict_disease=lambda condition, *, details: {"available": True, "disease": "示例"},
            publish_safety_first=lambda result, triage: {**result, "published": True},
            enhanced_weights={"common": {"distance": 1.0}, "surgery": {"distance": 0.5}},
            hospital_weights={"routine": {"distance": 1.0}},
            ranking_model="test-ranking-v1",
            has_real_doctors=has_real_doctors,
            real_doctor_count=3,
        )
        return service, calls

    def test_legacy_context_uses_legacy_doctors_and_preserves_payload_shape(self):
        service, calls = self.make_service()
        payload = service.build(RecommendationContext("示例描述", "common", "天宁区", "system", 31.7, 119.9))

        self.assertEqual(payload["effective_scenario"], "common")
        self.assertEqual(payload["data_source"], "mock")
        self.assertEqual(payload["total_real_doctors"], 3)
        self.assertEqual(payload["recommended_doctors"], [{"doctor": {"id": 1}}])
        self.assertEqual(calls, ["analyze:示例描述:common", "hospitals:31.7:119.9", "legacy-doctors"])

    def test_versioned_mode_uses_enhanced_doctors_and_explicit_safety_publication(self):
        service, calls = self.make_service(has_real_doctors=True)
        payload = service.build(
            RecommendationContext("示例描述", "complex", "天宁区", "wish_expert", 31.7, 119.9),
            doctor_top_n=8,
            enhanced=True,
            safety_first=True,
        )

        self.assertTrue(payload["published"])
        self.assertEqual(payload["data_source"], "real_data")
        self.assertEqual(payload["recommended_doctors"], [{"doctor": {"id": 1001}}])
        self.assertEqual(calls, ["analyze:示例描述:complex", "hospitals:31.7:119.9", "enhanced-doctors:common:8"])

    def test_distance_rerank_prefers_real_doctor_and_sorts_by_distance(self):
        service = DistanceRerankApplicationService(
            real_doctors=lambda: [{"id": 1001, "hospital_id": 2, "name": "真实医生"}],
            fallback_doctors=lambda: [{"id": 1, "hospital_id": 1, "name": "兼容医生"}],
            hospitals=lambda: [
                {"id": 1, "name": "近医院", "level": "二级", "address": "近处", "lat": 0, "lng": 0},
                {"id": 2, "name": "远医院", "level": "三级", "address": "远处", "lat": 10, "lng": 10},
            ],
            distance=lambda user_lat, user_lng, lat, lng: abs(lat - user_lat) + abs(lng - user_lng),
        )

        result = service.rerank([1001, 1, 999], district="天宁区", user_lat=0, user_lng=0)

        self.assertEqual(result["count"], 2)
        self.assertEqual(result["ranked_doctors"][0]["doctor"]["id"], 1)
        self.assertEqual(result["ranked_doctors"][1]["doctor"]["id"], 1001)
        self.assertEqual(result["ranked_doctors"][0]["hospital"]["name"], "近医院")
