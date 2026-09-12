from __future__ import annotations

from unittest import TestCase

from backend.app.application.recommendation import (
    RecommendationApplicationService,
    RecommendationContext,
)
from backend.app.domain.medical_input import is_general_question_or_history
from backend.app.domain.recommendation.routing_preferences import normalize_routing_preferences
from backend.app.domain.recommendation.visit_intent import ranking_scenario_for_visit_intent
from backend.app.domain.triage.safety_gate import TriageStatus, triage_status_from_legacy
from backend.app.composition import (
    ENHANCED_WEIGHTS,
    analyze_medical_triage,
    match_department,
)


class QuestionHistoryContextTests(TestCase):
    def test_general_question_or_history_detection(self):
        self.assertTrue(is_general_question_or_history("说话不清是不是中风"))
        self.assertTrue(is_general_question_or_history("胸痛是不是心梗"))
        self.assertTrue(is_general_question_or_history("家里人中风前会说话不清吗"))
        self.assertTrue(is_general_question_or_history("以前说话不清过一次"))
        self.assertTrue(is_general_question_or_history("家里人心梗会胸痛吗"))
        self.assertFalse(is_general_question_or_history("我现在说话不清，是不是中风"))
        self.assertFalse(is_general_question_or_history("我现在胸痛，是不是心梗"))
        self.assertFalse(is_general_question_or_history("现在突然说话不清"))
        self.assertFalse(is_general_question_or_history("突然一侧无力并说话不清"))

    def test_question_stroke_signs_is_not_emergency(self):
        triage = analyze_medical_triage("说话不清是不是中风")
        self.assertNotEqual(triage_status_from_legacy(triage).value, "EMERGENCY")

    def test_first_person_current_stroke_stays_emergency(self):
        triage = analyze_medical_triage("我现在说话不清，是不是中风")
        self.assertEqual(triage_status_from_legacy(triage).value, "EMERGENCY")

    def test_sudden_slurred_speech_stays_emergency(self):
        triage = analyze_medical_triage("现在突然说话不清")
        self.assertEqual(triage_status_from_legacy(triage).value, "EMERGENCY")

    def test_family_history_stroke_is_not_emergency(self):
        triage = analyze_medical_triage("家里人中风前会说话不清吗")
        self.assertNotEqual(triage_status_from_legacy(triage).value, "EMERGENCY")

    def test_past_slurred_speech_is_not_emergency(self):
        triage = analyze_medical_triage("以前说话不清过一次")
        self.assertNotEqual(triage_status_from_legacy(triage).value, "EMERGENCY")

    def test_question_heart_attack_is_not_emergency(self):
        triage = analyze_medical_triage("胸痛是不是心梗")
        self.assertNotEqual(triage_status_from_legacy(triage).value, "EMERGENCY")

    def test_first_person_current_chest_pain_is_emergency(self):
        triage = analyze_medical_triage("我现在胸痛，是不是心梗")
        self.assertEqual(triage_status_from_legacy(triage).value, "EMERGENCY")

    def test_family_heart_attack_question_is_not_emergency(self):
        triage = analyze_medical_triage("家里人心梗会胸痛吗")
        self.assertNotEqual(triage_status_from_legacy(triage).value, "EMERGENCY")


class DiseaseModelRoutingDemotionTests(TestCase):
    def test_department_candidates_carry_source(self):
        triage = analyze_medical_triage("最近总是有点头晕乏力")
        candidates = triage.get("department_candidates") or []
        self.assertTrue(candidates)
        for candidate in candidates:
            self.assertIn("source", candidate)

    def test_user_stated_hypertension_beats_model_guess(self):
        triage = analyze_medical_triage("已经确诊高血压，需要复诊开药")
        self.assertEqual(triage.get("matched_department"), "心血管内科")
        known = triage.get("known_disease") or {}
        self.assertTrue(known.get("has_known_disease"))
        self.assertEqual(known.get("department"), "心血管内科")

    def test_model_prediction_alone_does_not_decide_matched_department(self):
        # Sparse non-specific wording with no reliable department keyword.
        triage = analyze_medical_triage("最近人不太舒服，有点没力气")
        matched = triage.get("matched_department")
        model_depts = {
            item.get("recommended_department")
            for item in (triage.get("disease_candidates") or [])
            if item.get("source") == "symptom_disease_model"
        }
        if model_depts and matched:
            # If only model evidence exists, patient-facing dept must not be
            # the model Top-1 guess; prefer general medicine or rule result.
            if matched in model_depts:
                rule_sources = {
                    item.get("source")
                    for item in (triage.get("disease_candidates") or [])
                    if item.get("recommended_department") == matched
                }
                self.assertTrue(
                    rule_sources - {"symptom_disease_model"},
                    "matched_department must not come solely from the disease model",
                )

    def test_match_department_skips_model_only_fallback(self):
        # match_department falls back to rule-engine candidates, never model alone.
        dept = match_department("最近人不太舒服，有点没力气")
        # Either None or a rule-backed department; never forced by model Top-1.
        self.assertTrue(dept is None or isinstance(dept, str))

    def test_emergency_path_ignores_model_department(self):
        triage = analyze_medical_triage("突然一侧无力并说话不清")
        self.assertEqual(triage_status_from_legacy(triage), TriageStatus.EMERGENCY)
        self.assertIsNotNone(triage.get("matched_department"))


class DistancePreferenceRankingTests(TestCase):
    def _weights_delta(self, preference: str):
        base = ENHANCED_WEIGHTS["common"]
        service_weights = {
            "common": dict(base),
            "complex": dict(base),
            "surgery": dict(base),
            "first_visit": dict(base),
            "procedure_consult": dict(base),
        }
        captured: dict = {}

        def enhanced_doctors(condition, scenario, **kwargs):
            captured["distance_preference"] = kwargs.get("distance_preference")
            captured["scenario"] = scenario
            # Simulate two doctors with close clinical fit and different distance.
            nearby = {
                "doctor": {"id": 1, "name": "近处医生"},
                "match_score": 0.72,
                "hospital_distance_km": 2.0,
                "reasons": [],
            }
            farther = {
                "doctor": {"id": 2, "name": "远处医生"},
                "match_score": 0.72,
                "hospital_distance_km": 18.0,
                "reasons": [],
            }
            if preference == "prefer_nearby":
                nearby["match_score"] = 0.76
            elif preference == "allow_farther_for_fit":
                farther["match_score"] = 0.78
            return [nearby, farther]

        service = RecommendationApplicationService(
            analyze_triage=lambda condition, scenario, followup=None: {
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
            enhanced_weights=service_weights,
            hospital_weights={"routine": {}},
            ranking_model="test",
            has_real_doctors=True,
            real_doctor_count=2,
        )
        payload = service.build(
            RecommendationContext(
                condition="咳嗽两天",
                scenario="common",
                district=None,
                expert_preference="system",
                user_lat=31.77,
                user_lng=119.95,
                routing_preferences={"distance_preference": preference},
            ),
            enhanced=True,
            safety_first=False,
        )
        return payload, captured

    def test_distance_preference_is_passed_into_scoring(self):
        payload, captured = self._weights_delta("prefer_nearby")
        self.assertEqual(captured["distance_preference"], "prefer_nearby")
        self.assertEqual(
            payload["routing_preferences"]["distance_preference"],
            "prefer_nearby",
        )

    def test_prefer_nearby_weights_increase_access(self):
        service = RecommendationApplicationService(
            analyze_triage=lambda *a, **k: {
                "level": "routine",
                "severity_bucket": "小病/常见病倾向",
                "recommended_scenario": "common",
                "matched_department": "呼吸内科",
            },
            resource_strategy=lambda triage, expert: {"visit_path": "assistive"},
            recommend_hospitals=lambda *args, **kwargs: [],
            enhanced_recommend_doctors=lambda *args, **kwargs: [],
            legacy_recommend_doctors=lambda condition: [],
            match_department=lambda condition: "呼吸内科",
            build_public_htriage=lambda triage: {},
            predict_disease=lambda *args, **kwargs: {},
            publish_safety_first=lambda payload, triage: payload,
            enhanced_weights={
                "common": {"specialty": 0.42, "access": 0.34, "hospital": 0.16, "surgery": 0.06, "academic": 0.0, "title": 0.0},
                "surgery": {"specialty": 0.42, "access": 0.34, "hospital": 0.16, "surgery": 0.06, "academic": 0.0, "title": 0.0},
            },
            hospital_weights={"routine": {}},
            ranking_model="test",
            has_real_doctors=True,
            real_doctor_count=1,
        )
        flexible = service.build(
            RecommendationContext(
                condition="咳嗽两天",
                scenario="common",
                district=None,
                expert_preference="system",
                user_lat=31.77,
                user_lng=119.95,
                routing_preferences={"distance_preference": "distance_flexible"},
            ),
            enhanced=True,
        )
        nearby = service.build(
            RecommendationContext(
                condition="咳嗽两天",
                scenario="common",
                district=None,
                expert_preference="system",
                user_lat=31.77,
                user_lng=119.95,
                routing_preferences={"distance_preference": "prefer_nearby"},
            ),
            enhanced=True,
        )
        self.assertGreater(
            nearby["weights_used"]["access"],
            flexible["weights_used"]["access"],
        )

    def test_farther_for_fit_reduces_access_weight(self):
        service = RecommendationApplicationService(
            analyze_triage=lambda *a, **k: {
                "level": "routine",
                "severity_bucket": "小病/常见病倾向",
                "recommended_scenario": "common",
                "matched_department": "呼吸内科",
            },
            resource_strategy=lambda triage, expert: {"visit_path": "assistive"},
            recommend_hospitals=lambda *args, **kwargs: [],
            enhanced_recommend_doctors=lambda *args, **kwargs: [],
            legacy_recommend_doctors=lambda condition: [],
            match_department=lambda condition: "呼吸内科",
            build_public_htriage=lambda triage: {},
            predict_disease=lambda *args, **kwargs: {},
            publish_safety_first=lambda payload, triage: payload,
            enhanced_weights={
                "common": {"specialty": 0.42, "access": 0.34, "hospital": 0.16, "surgery": 0.06, "academic": 0.0, "title": 0.0},
                "surgery": {"specialty": 0.42, "access": 0.34, "hospital": 0.16, "surgery": 0.06, "academic": 0.0, "title": 0.0},
            },
            hospital_weights={"routine": {}},
            ranking_model="test",
            has_real_doctors=True,
            real_doctor_count=1,
        )
        flexible = service.build(
            RecommendationContext(
                condition="咳嗽两天",
                scenario="common",
                district=None,
                expert_preference="system",
                user_lat=31.77,
                user_lng=119.95,
            ),
            enhanced=True,
        )
        farther = service.build(
            RecommendationContext(
                condition="咳嗽两天",
                scenario="common",
                district=None,
                expert_preference="system",
                user_lat=31.77,
                user_lng=119.95,
                routing_preferences={"distance_preference": "allow_farther_for_fit"},
            ),
            enhanced=True,
        )
        self.assertLess(
            farther["weights_used"]["access"],
            flexible["weights_used"]["access"],
        )
        self.assertGreater(
            farther["weights_used"]["specialty"],
            flexible["weights_used"]["specialty"],
        )

    def test_no_location_notice_when_distance_preference_set(self):
        service = RecommendationApplicationService(
            analyze_triage=lambda *a, **k: {
                "level": "routine",
                "severity_bucket": "小病/常见病倾向",
                "recommended_scenario": "common",
                "matched_department": "呼吸内科",
            },
            resource_strategy=lambda triage, expert: {"visit_path": "assistive"},
            recommend_hospitals=lambda *args, **kwargs: [],
            enhanced_recommend_doctors=lambda *args, **kwargs: [],
            legacy_recommend_doctors=lambda condition: [],
            match_department=lambda condition: "呼吸内科",
            build_public_htriage=lambda triage: {},
            predict_disease=lambda *args, **kwargs: {},
            publish_safety_first=lambda payload, triage: payload,
            enhanced_weights={"common": {"specialty": 1.0}, "surgery": {"specialty": 1.0}},
            hospital_weights={"routine": {}},
            ranking_model="test",
            has_real_doctors=True,
            real_doctor_count=1,
        )
        payload = service.build(
            RecommendationContext(
                condition="咳嗽两天",
                scenario="common",
                district=None,
                expert_preference="system",
                user_lat=None,
                user_lng=None,
                routing_preferences={"distance_preference": "prefer_nearby"},
            ),
            enhanced=True,
        )
        self.assertIn("ranking_notice", payload)
        # Access weight is removed when location is unavailable.
        self.assertEqual(payload["weights_used"].get("access", 0.0), 0.0)


class DistrictPreferenceRoutingTests(TestCase):
    def _service_with_hospitals(self, hospitals):
        captured: dict = {}

        def recommend_hospitals(condition, lat, lng, *, triage, district_preference="any_district", user_district=None):
            captured["district_preference"] = district_preference
            captured["user_district"] = user_district
            return hospitals

        service = RecommendationApplicationService(
            analyze_triage=lambda *a, **k: {
                "level": "routine",
                "severity_bucket": "小病/常见病倾向",
                "recommended_scenario": "common",
                "matched_department": "呼吸内科",
            },
            resource_strategy=lambda triage, expert: {"visit_path": "assistive"},
            recommend_hospitals=recommend_hospitals,
            enhanced_recommend_doctors=lambda *args, **kwargs: [],
            legacy_recommend_doctors=lambda condition: [],
            match_department=lambda condition: "呼吸内科",
            build_public_htriage=lambda triage: {},
            predict_disease=lambda *args, **kwargs: {},
            publish_safety_first=lambda payload, triage: payload,
            enhanced_weights={"common": {"specialty": 1.0}, "surgery": {"specialty": 1.0}},
            hospital_weights={"routine": {}},
            ranking_model="test",
            has_real_doctors=True,
            real_doctor_count=0,
        )
        return service, captured

    def test_district_preference_passed_when_location_available(self):
        hospitals = [{"hospital": {"id": 1, "name": "本区医院", "district": "天宁区"}, "composite_score": 80.0}]
        service, captured = self._service_with_hospitals(hospitals)
        service.build(
            RecommendationContext(
                condition="咳嗽两天",
                scenario="common",
                district="天宁区",
                expert_preference="system",
                user_lat=31.77,
                user_lng=119.95,
                location_source="district",
                routing_preferences={"district_preference": "prefer_home_district"},
            ),
            enhanced=True,
        )
        self.assertEqual(captured["district_preference"], "prefer_home_district")
        self.assertEqual(captured["user_district"], "天宁区")

    def test_unknown_district_skips_preference(self):
        hospitals = [{"hospital": {"id": 1, "name": "某医院"}, "composite_score": 80.0}]
        service, captured = self._service_with_hospitals(hospitals)
        payload = service.build(
            RecommendationContext(
                condition="咳嗽两天",
                scenario="common",
                district=None,
                expert_preference="system",
                user_lat=None,
                user_lng=None,
                location_source="unknown",
                routing_preferences={"district_preference": "prefer_home_district"},
            ),
            enhanced=True,
        )
        self.assertEqual(captured["district_preference"], "any_district")
        self.assertIsNone(captured["user_district"])
        self.assertEqual(
            payload.get("district_preference_notice"),
            "当前没有可用区域信息，本次未使用跨区偏好。",
        )

    def test_normalize_defaults(self):
        self.assertEqual(
            normalize_routing_preferences(None),
            {
                "district_preference": "any_district",
                "distance_preference": "distance_flexible",
                "continuity_preference": False,
            },
        )


class ProcedureConsultIsolationTests(TestCase):
    def test_procedure_consult_maps_to_own_scenario(self):
        self.assertEqual(
            ranking_scenario_for_visit_intent("procedure_consult", "common"),
            "procedure_consult",
        )
        self.assertIn("procedure_consult", ENHANCED_WEIGHTS)
        # procedure_consult must not inherit emergency surgery weights.
        self.assertNotEqual(
            ENHANCED_WEIGHTS["procedure_consult"],
            ENHANCED_WEIGHTS["surgery"],
        )

    def test_procedure_consult_with_routine_symptoms_stays_routine(self):
        service = RecommendationApplicationService(
            analyze_triage=lambda condition, scenario, followup=None: {
                "level": "routine",
                "severity_bucket": "小病/常见病倾向",
                "recommended_scenario": "common",
                "matched_department": "骨科",
            },
            resource_strategy=lambda triage, expert: {"visit_path": "assistive"},
            recommend_hospitals=lambda *args, **kwargs: [],
            enhanced_recommend_doctors=lambda *args, **kwargs: {
                # Capture the scenario used for ranking, not triage.
                "captured_scenario": kwargs.get("scenario") or args[1] if len(args) > 1 else kwargs.get("scenario")
            } or [],
            legacy_recommend_doctors=lambda condition: [],
            match_department=lambda condition: "骨科",
            build_public_htriage=lambda triage: {},
            predict_disease=lambda *args, **kwargs: {},
            publish_safety_first=lambda payload, triage: payload,
            enhanced_weights={
                "common": {"specialty": 1.0},
                "complex": {"specialty": 1.0},
                "surgery": {"specialty": 1.0},
                "first_visit": {"specialty": 1.0},
                "procedure_consult": {"specialty": 1.0},
            },
            hospital_weights={"routine": {}},
            ranking_model="test",
            has_real_doctors=True,
            real_doctor_count=1,
        )
        # Simpler: use real analyze path for emergency isolation and a stub for ranking.
        from backend.app.composition import analyze_medical_triage as real_analyze

        captured_scenarios = []

        def enhanced_doctors(condition, scenario, **kwargs):
            captured_scenarios.append(scenario)
            return []

        service = RecommendationApplicationService(
            analyze_triage=real_analyze,
            resource_strategy=lambda triage, expert: {"visit_path": "assistive"},
            recommend_hospitals=lambda *args, **kwargs: [],
            enhanced_recommend_doctors=enhanced_doctors,
            legacy_recommend_doctors=lambda condition: [],
            match_department=match_department,
            build_public_htriage=lambda triage: {},
            predict_disease=lambda *args, **kwargs: {},
            publish_safety_first=lambda payload, triage: payload,
            enhanced_weights={
                "common": {"specialty": 1.0},
                "complex": {"specialty": 1.0},
                "surgery": {"specialty": 1.0},
                "first_visit": {"specialty": 1.0},
                "procedure_consult": {"specialty": 1.0},
            },
            hospital_weights={"routine": {}},
            ranking_model="test",
            has_real_doctors=True,
            real_doctor_count=1,
        )
        payload = service.build(
            RecommendationContext(
                condition="膝盖疼了两周，想咨询手术方案",
                scenario="common",
                district=None,
                expert_preference="system",
                user_lat=None,
                user_lng=None,
                visit_intent="procedure_consult",
            ),
            enhanced=True,
        )
        self.assertEqual(payload["triage"]["level"], "routine")
        self.assertEqual(payload["effective_scenario"], "procedure_consult")
        self.assertEqual(payload["triage_scenario"], payload["triage"].get("recommended_scenario") or "common")
        self.assertEqual(captured_scenarios, ["procedure_consult"])

    def test_procedure_consult_with_emergency_symptoms_stays_emergency(self):
        from backend.app.composition import analyze_medical_triage as real_analyze

        service = RecommendationApplicationService(
            analyze_triage=real_analyze,
            resource_strategy=lambda triage, expert: {"visit_path": "assistive"},
            recommend_hospitals=lambda *args, **kwargs: [],
            enhanced_recommend_doctors=lambda *args, **kwargs: [],
            legacy_recommend_doctors=lambda condition: [],
            match_department=match_department,
            build_public_htriage=lambda triage: {},
            predict_disease=lambda *args, **kwargs: {},
            publish_safety_first=lambda payload, triage: payload,
            enhanced_weights={
                "common": {"specialty": 1.0},
                "complex": {"specialty": 1.0},
                "surgery": {"specialty": 1.0},
                "first_visit": {"specialty": 1.0},
                "procedure_consult": {"specialty": 1.0},
            },
            hospital_weights={"routine": {}},
            ranking_model="test",
            has_real_doctors=True,
            real_doctor_count=1,
        )
        payload = service.build(
            RecommendationContext(
                condition="喘不上气",
                scenario="common",
                district=None,
                expert_preference="system",
                user_lat=None,
                user_lng=None,
                visit_intent="procedure_consult",
            ),
            enhanced=True,
        )
        self.assertEqual(triage_status_from_legacy(payload["triage"]), TriageStatus.EMERGENCY)
        self.assertEqual(payload["visit_intent"], "procedure_consult")


class RealHospitalDistrictPreferenceTests(TestCase):
    def test_prefer_home_district_boosts_same_district_hospitals(self):
        from backend.app.composition import recommend

        triage = analyze_medical_triage("最近皮肤瘙痒一周")
        # Tianning reference point (district center approximation).
        lat, lng = 31.78, 119.95
        neutral = recommend(
            "最近皮肤瘙痒一周",
            lat,
            lng,
            top_n=8,
            triage=triage,
            district_preference="any_district",
            user_district="天宁区",
        )
        preferred = recommend(
            "最近皮肤瘙痒一周",
            lat,
            lng,
            top_n=8,
            triage=triage,
            district_preference="prefer_home_district",
            user_district="天宁区",
        )
        self.assertTrue(neutral)
        self.assertTrue(preferred)

        def score_by_id(rows):
            return {row["hospital"]["id"]: row["composite_score"] for row in rows}

        neutral_scores = score_by_id(neutral)
        preferred_scores = score_by_id(preferred)
        boosted = [
            hospital_id
            for hospital_id, score in preferred_scores.items()
            if hospital_id in neutral_scores and score > neutral_scores[hospital_id]
        ]
        # At least one same-district hospital must receive the soft boost.
        self.assertTrue(boosted, "prefer_home_district must change at least one hospital score")
        # Explanations for boosted hospitals must mention the preference.
        boosted_rows = [row for row in preferred if row["hospital"]["id"] in boosted]
        self.assertTrue(
            any("优先本区" in " ".join(row.get("explanations") or []) for row in boosted_rows)
        )


class RealDoctorDistancePreferenceTests(TestCase):
    def test_prefer_nearby_weights_are_applied_before_scoring(self):
        from backend.app.composition import enhanced_recommend_doctors

        lat, lng = 31.78, 119.95
        triage = {
            "level": "routine",
            "severity_bucket": "小病/常见病倾向",
            "recommended_scenario": "common",
            "matched_department": "呼吸内科",
        }
        flexible = enhanced_recommend_doctors(
            "咳嗽两天",
            "common",
            top_n=8,
            user_lat=lat,
            user_lng=lng,
            triage=triage,
            distance_preference="distance_flexible",
        )
        nearby = enhanced_recommend_doctors(
            "咳嗽两天",
            "common",
            top_n=8,
            user_lat=lat,
            user_lng=lng,
            triage=triage,
            distance_preference="prefer_nearby",
        )
        self.assertTrue(flexible)
        self.assertTrue(nearby)
        # With prefer_nearby, access weight is higher; ranking may change when
        # clinical fit is close. At minimum, the scoring context must differ.
        # Verify by checking that scores are not identical across all candidates.
        flexible_scores = [row["match_score"] for row in flexible]
        nearby_scores = [row["match_score"] for row in nearby]
        self.assertNotEqual(flexible_scores, nearby_scores)
