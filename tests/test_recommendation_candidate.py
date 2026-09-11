from __future__ import annotations

from unittest import TestCase

from backend.app.domain.recommendation.candidate import (
    build_emergency_doctor_fallback_candidates,
    build_hospital_candidates,
    build_emergency_doctor_fallback_result,
    build_doctor_recommendation_result,
    build_hospital_recommendation_result,
    compose_hospital_candidate,
    doctor_recommendation_reasons,
    score_emergency_doctor_fallback,
)


class RecommendationCandidateTests(TestCase):
    def test_emergency_fallback_traversal_filters_hospitals_and_prepares_distance(self):
        doctors = [{"id": 1, "hospital_id": 10}, {"id": 2, "hospital_id": 11}, {"id": 3}]
        hospitals = {
            10: {"id": 10, "lat": 31.1, "lng": 119.1, "emergency": True},
            11: {"id": 11, "lat": 31.2, "lng": 119.2, "emergency": False},
        }
        access_calls = []

        def hospital_for_doctor(doctor):
            return hospitals.get(doctor.get("hospital_id"))

        def access_score_fn(hospital, user_lat, user_lng, context):
            access_calls.append((hospital["id"], user_lat, user_lng, context))
            return 0.6

        def distance_fn(lat1, lng1, lat2, lng2):
            return round(lat2 - lat1, 2)

        def score_fn(**kwargs):
            return {
                "surgery_score": 0.2,
                "title_score": 0.3,
                "quality_score": 0.4,
                "access_score": kwargs["access_score"],
                "availability_score": 0.5,
                "hospital_distance": kwargs["hospital_distance"],
                "emergency_priority_score": 0.5,
            }

        def result_fn(**kwargs):
            return {
                "doctor_id": kwargs["doctor"]["id"],
                "matched_dept": kwargs["matched_dept"],
                "distance": kwargs["hospital_distance"],
            }

        without_location = build_emergency_doctor_fallback_candidates(
            doctors=doctors,
            matched_dept="急诊医学科",
            ranking_model="test_model",
            user_lat=None,
            user_lng=None,
            hospital_for_doctor=hospital_for_doctor,
            access_score_fn=access_score_fn,
            distance_fn=distance_fn,
            score_fn=score_fn,
            result_fn=result_fn,
        )
        self.assertEqual(without_location, [{"doctor_id": 1, "matched_dept": "急诊医学科", "distance": None}])
        self.assertEqual(access_calls, [(10, None, None, "urgent")])

        with_location = build_emergency_doctor_fallback_candidates(
            doctors=doctors[:1],
            matched_dept=None,
            ranking_model="test_model",
            user_lat=30.0,
            user_lng=119.0,
            hospital_for_doctor=hospital_for_doctor,
            access_score_fn=access_score_fn,
            distance_fn=distance_fn,
            score_fn=score_fn,
            result_fn=result_fn,
        )
        self.assertEqual(with_location[0]["distance"], 1.1)

    def test_hospital_candidate_traversal_preserves_order_and_traffic_policy(self):
        hospitals = [
            {"id": 1, "lat": 31.0, "lng": 119.0},
            {"id": 2, "lat": 32.0, "lng": 120.0},
        ]
        access_contexts = []

        def distance_fn(lat1, lng1, lat2, lng2):
            return lat2 - lat1

        def access_score_fn(hospital, user_lat, user_lng, access_context):
            access_contexts.append(access_context)
            return 0.7

        def traffic_access_fn(hospital):
            return {"hospital_id": hospital["id"]}

        def compose_fn(**kwargs):
            return {
                "hospital_id": kwargs["hospital"]["id"],
                "distance": kwargs["distance"],
                "traffic_access": kwargs["traffic_access"],
            }

        urgent = build_hospital_candidates(
            hospitals=hospitals,
            condition="胸痛",
            target_dept="心血管内科",
            triage={"level": "urgent"},
            triage_level="urgent",
            access_context="urgent",
            user_lat=30.0,
            user_lng=119.0,
            distance_fn=distance_fn,
            access_score_fn=access_score_fn,
            traffic_access_fn=traffic_access_fn,
            compose_fn=compose_fn,
            ranking_weights={"clinical": 1.0},
            ranking_model="test",
        )
        self.assertEqual([item["hospital_id"] for item in urgent], [1, 2])
        self.assertEqual([item["distance"] for item in urgent], [1.0, 2.0])
        self.assertEqual(access_contexts, ["urgent", "urgent"])
        self.assertFalse(urgent[0]["traffic_access"]["used_in_ranking"])

        routine = build_hospital_candidates(
            hospitals=hospitals[:1],
            condition="皮肤瘙痒",
            target_dept="皮肤科",
            triage=None,
            triage_level="routine",
            access_context="first_visit",
            user_lat=30.0,
            user_lng=119.0,
            distance_fn=distance_fn,
            access_score_fn=access_score_fn,
            traffic_access_fn=traffic_access_fn,
            compose_fn=compose_fn,
            ranking_weights={"clinical": 1.0},
            ranking_model="test",
        )
        self.assertTrue(routine[0]["traffic_access"]["used_in_ranking"])
        self.assertIn("普通/初诊", routine[0]["traffic_access"]["ranking_policy"])

    def test_explanation_preserves_priority_and_four_item_limit(self):
        reasons = doctor_recommendation_reasons(
            specialty_score=0.9,
            surgery_score=0.8,
            academic_score=0.7,
            access_score=0.9,
            availability_score=0.8,
            penalty_details=[{"code": "access"}],
            resource_notes=["急症按急诊能力与距离优先"],
        )
        self.assertEqual(
            reasons,
            ["科室/专长匹配", "临床经验较强", "距离可及性较好", "医院承载能力较好"],
        )

    def test_explanation_has_explicit_fallback_when_no_signal_is_high(self):
        self.assertEqual(
            doctor_recommendation_reasons(0.2, 0.2, 0.2, 0.2, 0.2, [], []),
            ["按专科匹配、临床经历和可及性综合排序"],
        )

    def test_candidate_builder_preserves_scores_penalties_and_strategy_fields(self):
        penalty_details = [{"code": "underuse", "label": "低层级", "value": 0.08}]
        result = build_doctor_recommendation_result(
            doctor={"id": 7, "name": "示例医生"},
            total_score=0.876543,
            surgery_score=0.7,
            specialty_score=0.9,
            academic_score=0.6,
            title_score=0.72,
            hospital_score=0.8,
            access_score=0.75,
            availability_score=0.8,
            continuity_score=0.55,
            fairness_score=0.7,
            risk_penalty=0.04,
            mismatch_penalty=0.08,
            penalty_details=penalty_details,
            matched_dept="心血管内科",
            ranking_model="test_model",
            hospital_distance=4.2,
            emergency_priority_score=0.83456,
            resource_tier="expert",
            visit_path="专科门诊/专家号",
            resource_cap=0.9,
            resource_notes=["中重症提高专科专家适配"],
        )
        self.assertEqual(result["match_score"], 0.8765)
        self.assertEqual(result["scores"]["risk_penalty"], 0.12)
        self.assertIs(result["penalty_breakdown"], penalty_details)
        self.assertEqual(result["capability_indices"]["DCI"], 0.9)
        self.assertEqual(result["resource_cap"], 0.9)
        self.assertEqual(result["visit_path"], "专科门诊/专家号")

    def test_candidate_builder_keeps_none_distance_and_department(self):
        result = build_doctor_recommendation_result(
            doctor={},
            total_score=0.1,
            surgery_score=0.1,
            specialty_score=0.1,
            academic_score=0.1,
            title_score=0.1,
            hospital_score=0.1,
            access_score=0.1,
            availability_score=0.1,
            continuity_score=0.1,
            fairness_score=0.1,
            risk_penalty=0.0,
            mismatch_penalty=0.0,
            penalty_details=[],
            matched_dept=None,
            ranking_model="test_model",
            hospital_distance=None,
            emergency_priority_score=0.1,
            resource_tier="general",
            visit_path=None,
            resource_cap=1.0,
            resource_notes=[],
        )
        self.assertIsNone(result["matched_dept"])
        self.assertIsNone(result["hospital_distance_km"])
        self.assertIsNone(result["visit_path"])

    def test_hospital_candidate_builder_preserves_scores_and_payload_objects(self):
        hospital = {"id": 3, "name": "示例医院"}
        features = {"clinical": 0.8, "traffic_access": {"used_in_ranking": True}}
        traffic = {"public_transport_score": 0.7}
        weights = {"clinical": 0.3, "accessibility": 0.2}
        explanations = ["科室匹配", "距离近"]
        result = build_hospital_recommendation_result(
            hospital=hospital,
            distance=4.25,
            accessibility=0.87654,
            strength_score=82,
            composite_score=83.4,
            matched_department="心血管内科",
            feature_scores=features,
            traffic_access=traffic,
            ranking_weights=weights,
            ranking_model="test_model",
            explanations=explanations,
        )
        self.assertIs(result["hospital"], hospital)
        self.assertEqual(result["dist_score"], 87.7)
        self.assertEqual(result["composite_score"], 83.4)
        self.assertIs(result["feature_scores"], features)
        self.assertIs(result["traffic_access"], traffic)
        self.assertIs(result["ranking_weights"], weights)
        self.assertIs(result["explanations"], explanations)

    def test_hospital_candidate_builder_keeps_empty_optional_values(self):
        result = build_hospital_recommendation_result(
            hospital={},
            distance=50.0,
            accessibility=0.1,
            strength_score=50,
            composite_score=10.0,
            matched_department=None,
            feature_scores={},
            traffic_access={},
            ranking_weights={},
            ranking_model="test_model",
            explanations=[],
        )
        self.assertIsNone(result["matched_department"])
        self.assertEqual(result["dist_score"], 10.0)
        self.assertEqual(result["explanations"], [])

    def test_hospital_candidate_composition_keeps_feature_score_and_explain_contract(self):
        hospital = {
            "id": 1,
            "name": "示例综合医院",
            "type": "综合医院",
            "level": "三级甲等",
            "rating": 4.5,
            "beds": 1800,
            "daily_outpatients": 1000,
            "emergency": True,
            "strength_scores": {"心血管内科": 90},
            "departments": ["心血管内科"],
        }
        traffic = {"public_transport_score": 0.8, "used_in_ranking": False}
        result = compose_hospital_candidate(
            hospital=hospital,
            condition="胸痛",
            target_dept="心血管内科",
            triage={"level": "emergency"},
            triage_level="emergency",
            distance=3.2,
            accessibility=0.92,
            traffic_access=traffic,
            ranking_weights={
                "clinical": 0.34,
                "availability": 0.10,
                "accessibility": 0.14,
                "continuity": 0.03,
                "quality": 0.20,
                "fairness": 0.04,
                "emergency": 0.15,
            },
            ranking_model="test_model",
        )
        self.assertIs(result["hospital"], hospital)
        self.assertIs(result["traffic_access"], traffic)
        self.assertEqual(result["strength_score"], 75)
        self.assertEqual(result["matched_department"], "心血管内科")
        self.assertEqual(result["feature_scores"]["risk_penalty"], 0.0)
        self.assertIn("具备急诊能力", result["explanations"])

    def test_hospital_candidate_composition_preserves_emergency_risk_penalty(self):
        result = compose_hospital_candidate(
            hospital={"level": "二级", "rating": 4.0, "departments": ["眼科"], "emergency": False},
            condition="胸痛",
            target_dept="心血管内科",
            triage={"level": "emergency"},
            triage_level="emergency",
            distance=20.0,
            accessibility=0.4,
            traffic_access={"public_transport_score": 0.6},
            ranking_weights={
                "clinical": 0.34,
                "availability": 0.10,
                "accessibility": 0.14,
                "continuity": 0.03,
                "quality": 0.20,
                "fairness": 0.04,
                "emergency": 0.15,
            },
            ranking_model="test_model",
        )
        self.assertEqual(result["feature_scores"]["risk_penalty"], 0.45)
        self.assertEqual(result["matched_department"], "心血管内科")

    def test_emergency_fallback_builder_preserves_legacy_payload(self):
        doctor = {"id": 9, "name": "急症示例医生"}
        result = build_emergency_doctor_fallback_result(
            doctor=doctor,
            surgery_score=0.45678,
            title_score=0.78,
            quality_score=0.81234,
            access_score=0.92345,
            availability_score=0.7,
            matched_dept="普外科",
            ranking_model="test_model",
            hospital_distance=3.2,
            emergency_priority_score=0.87654,
        )
        self.assertIs(result["doctor"], doctor)
        self.assertEqual(result["match_score"], 0.8765)
        self.assertEqual(
            result["scores"],
            {
                "surgery": 0.4568,
                "specialty": 0.35,
                "academic": 0.0,
                "title": 0.78,
                "hospital": 0.8123,
                "access": 0.9234,
                "availability": 0.7,
                "continuity": 0.0,
                "fairness": 0.0,
                "risk_penalty": 0.0,
            },
        )
        self.assertEqual(result["reasons"], ["急症兜底召回", "优先支持急诊医院", "综合医生资历与到院距离"])
        self.assertEqual(result["hospital_distance_km"], 3.2)

    def test_emergency_fallback_scoring_keeps_legacy_title_and_priority_weights(self):
        scores = score_emergency_doctor_fallback(
            doctor={"surgery_count": 6999, "title": "主任医师"},
            hospital={"rating": 5.0, "level": "三级甲等", "beds": 1800, "daily_outpatients": 1000, "emergency": True},
            access_score=0.9,
            hospital_distance=2.4,
        )
        self.assertEqual(scores["surgery_score"], 1.0)
        self.assertEqual(scores["title_score"], 1.0)
        self.assertGreater(scores["quality_score"], 0.9)
        self.assertEqual(
            scores["emergency_priority_score"],
            min(1.0, scores["access_score"] * 0.38 + scores["title_score"] * 0.22 + scores["quality_score"] * 0.24 + scores["surgery_score"] * 0.16),
        )

    def test_emergency_fallback_scoring_keeps_missing_experience_defaults(self):
        scores = score_emergency_doctor_fallback(
            doctor={},
            hospital={},
            access_score=0.2,
            hospital_distance=None,
        )
        self.assertEqual(scores["surgery_score"], 0.18)
        self.assertEqual(scores["title_score"], 0.34)
        self.assertIsNone(scores["hospital_distance"])
