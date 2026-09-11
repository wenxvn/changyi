from __future__ import annotations

from unittest import TestCase

import app as application_entry
from backend.app.domain.triage.publication import (
    publish_safety_first,
    safety_first_htriage_payload,
    safety_first_prediction,
    safety_first_triage,
)
from backend.app.domain.triage.safety_gate import evaluate_safety_gate


class SafetyFirstPublicationTests(TestCase):
    def setUp(self):
        self.client = application_entry.app.test_client()

    def test_v1_emergency_triage_abstains_before_public_disease_candidates(self):
        response = self.client.post(
            "/api/v1/triage",
            json={"condition": "胸痛并且呼吸困难"},
        )

        self.assertEqual(response.status_code, 200)
        data = response.get_json()["data"]
        self.assertEqual(data["triage_status"], "EMERGENCY")
        self.assertEqual(data["disease_prediction"]["disease"], "")
        self.assertEqual(data["disease_prediction"]["predictions"], [])
        self.assertTrue(data["disease_prediction"]["abstained"])
        self.assertEqual(data["triage"]["disease_candidates"], [])
        self.assertEqual(data["htriage_analysis"]["disease_candidates"], [])
        self.assertTrue(data["triage"]["red_flag_tags"])
        self.assertFalse(data["triage"]["followup"]["needed"])
        self.assertIn("急诊", data["triage"]["care_level"])

    def test_v1_recommendations_keep_emergency_action_without_disease_anchor(self):
        response = self.client.post(
            "/api/v1/recommendations",
            json={"condition": "胸痛并且呼吸困难", "district": "天宁区"},
        )

        self.assertEqual(response.status_code, 200)
        data = response.get_json()["data"]
        self.assertEqual(data["triage"]["level"], "emergency")
        self.assertEqual(data["triage"]["disease_candidates"], [])
        self.assertEqual(data["htriage_analysis"]["model_disease_prediction"]["predictions"], [])
        self.assertTrue(data["triage"]["red_flag_tags"])
        self.assertTrue(data["recommended_hospitals"])

    def test_publication_helpers_redact_emergency_outputs_only(self):
        triage = {
            "level": "emergency",
            "severity_bucket": "大病/重症风险",
            "disease_candidates": [{"name": "示例疾病"}],
            "disease_categories": [{"primary": "示例"}],
            "model_disease_prediction": {"disease": "示例疾病", "predictions": [{"name": "示例疾病"}]},
            "followup": {"needed": True, "questions": ["是否发热"]},
        }
        decision = evaluate_safety_gate(triage)
        public = safety_first_triage(triage, decision)
        htriage = safety_first_htriage_payload(
            {"disease_candidates": [{"name": "示例疾病"}], "model_disease_prediction": {"disease": "示例疾病"}},
            decision,
        )
        self.assertEqual(public["disease_candidates"], [])
        self.assertEqual(public["disease_categories"], [])
        self.assertEqual(public["model_disease_prediction"]["predictions"], [])
        self.assertEqual(public["followup"]["questions"], [])
        self.assertEqual(htriage["disease_candidates"], [])
        self.assertTrue(htriage["model_disease_prediction"]["abstained"])
        self.assertEqual(safety_first_prediction(None)["disease"], "")

    def test_publication_helpers_keep_routine_payload_identity(self):
        payload = {"triage": {"level": "routine"}, "disease_prediction": {"disease": "示例"}}
        triage = {"level": "routine", "severity_bucket": "小病/常见病倾向"}
        result = publish_safety_first(payload, triage, lambda _: (_ for _ in ()).throw(AssertionError()))
        self.assertIs(result, payload)
