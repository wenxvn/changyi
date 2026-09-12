from __future__ import annotations

from unittest import TestCase

from backend.app.api.v1.schemas.recommendation import RecommendationRequest, RequestValidationError
from backend.app.domain.recommendation.visit_intent import (
    ranking_scenario_for_visit_intent,
)


class VisitIntentContractTests(TestCase):
    def test_visit_intent_maps_to_ranking_scenario_only(self):
        self.assertEqual(ranking_scenario_for_visit_intent("first_visit", "common"), "first_visit")
        self.assertEqual(ranking_scenario_for_visit_intent("follow_up", "common"), "complex")
        self.assertEqual(ranking_scenario_for_visit_intent("review_results", "common"), "complex")
        self.assertEqual(ranking_scenario_for_visit_intent("procedure_consult", "common"), "surgery")
        self.assertEqual(ranking_scenario_for_visit_intent("unsure", "common"), "common")
        self.assertEqual(ranking_scenario_for_visit_intent(None, "surgery"), "surgery")

    def test_recommendation_request_accepts_visit_intent(self):
        parsed = RecommendationRequest.parse({
            "condition": "咳嗽两天",
            "scenario": "common",
            "visit_intent": "procedure_consult",
        })
        self.assertEqual(parsed.visit_intent, "procedure_consult")

    def test_invalid_visit_intent_is_rejected(self):
        with self.assertRaises(RequestValidationError) as error:
            RecommendationRequest.parse({
                "condition": "咳嗽两天",
                "visit_intent": "chatbot",
            })
        self.assertEqual(error.exception.code, "INVALID_VISIT_INTENT")


class VisitIntentSafetyIsolationTests(TestCase):
    def test_visit_intent_does_not_change_triage_or_bypass_emergency(self):
        from backend.app.application.recommendation import (
            RecommendationApplicationService,
            RecommendationContext,
        )
        from backend.app.composition import analyze_medical_triage
        from backend.app.domain.triage.safety_gate import triage_status_from_legacy

        calls = []

        def analyze(condition, scenario, followup=None):
            calls.append(("triage", condition, scenario))
            return analyze_medical_triage(condition, scenario, followup)

        service = RecommendationApplicationService(
            analyze_triage=analyze,
            resource_strategy=lambda triage, expert: {"visit_path": "assistive"},
            recommend_hospitals=lambda *args, **kwargs: [],
            enhanced_recommend_doctors=lambda *args, **kwargs: [],
            legacy_recommend_doctors=lambda condition: [],
            match_department=lambda condition: "急诊医学科",
            build_public_htriage=lambda triage: {},
            predict_disease=lambda *args, **kwargs: {},
            publish_safety_first=lambda payload, triage: payload,
            enhanced_weights={
                "common": {"specialty": 1.0},
                "complex": {"specialty": 1.0},
                "surgery": {"specialty": 1.0},
                "first_visit": {"specialty": 1.0},
            },
            hospital_weights={"routine": {}},
            ranking_model="test",
            has_real_doctors=False,
            real_doctor_count=0,
        )

        emergency = service.build(
            RecommendationContext(
                condition="喘不上气",
                scenario="common",
                district=None,
                expert_preference="system",
                user_lat=None,
                user_lng=None,
                visit_intent="unsure",
            ),
            enhanced=False,
            safety_first=False,
        )
        routine = service.build(
            RecommendationContext(
                condition="轻微咳嗽两天",
                scenario="common",
                district=None,
                expert_preference="system",
                user_lat=None,
                user_lng=None,
                visit_intent="procedure_consult",
            ),
            enhanced=False,
            safety_first=False,
        )

        self.assertEqual(triage_status_from_legacy(emergency["triage"]).value, "EMERGENCY")
        self.assertEqual(emergency["triage"]["level"], "emergency")
        self.assertEqual(emergency["visit_intent"], "unsure")
        self.assertEqual(routine["triage"]["level"], "routine")
        self.assertEqual(routine["visit_intent"], "procedure_consult")
        self.assertEqual(routine["effective_scenario"], "surgery")
        self.assertEqual(routine["triage_scenario"], "common")
        # Triage is always analyzed with the request scenario, never visit intent.
        self.assertTrue(all(call[2] == "common" for call in calls if call[0] == "triage"))
