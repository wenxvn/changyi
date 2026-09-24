"""Competition golden E2E behavior boundaries via the v1 API.

These tests pin structural safety/routing contracts, not brittle scores.
"""

from __future__ import annotations

from unittest import TestCase

import app as application_entry


class CompetitionGoldenE2ETests(TestCase):
    def setUp(self):
        self.client = application_entry.app.test_client()

    def test_ordinary_clear_path_returns_assistive_routing(self):
        triage = self.client.post(
            "/api/v1/triage",
            json={"condition": "咳嗽三天，有点低烧，没有胸痛"},
        ).get_json()["data"]
        self.assertIn(triage["triage_status"], ("ROUTINE", "URGENT"))
        self.assertNotEqual(triage["triage_status"], "EMERGENCY")

        rec = self.client.post(
            "/api/v1/recommendations",
            json={"condition": "咳嗽三天，有点低烧，没有胸痛", "location_source": "unknown"},
        ).get_json()["data"]
        self.assertGreater(len(rec["recommended_hospitals"]), 0)
        self.assertGreater(len(rec["recommended_doctors"]), 0)
        self.assertIn(rec["resource_strategy"]["code"], {
            "routine_outpatient", "routine_must_expert", "specialty_priority", "specialty_followup",
        })
        self.assertTrue(rec["ranking_notice"] or rec["hospital_weights_used"])
        self.assertTrue(all("notice" in item or "reasons" in item or "hospital" in item for item in rec["recommended_hospitals"][:1]))

    def test_vague_input_insufficient_then_structured_followup_keeps_original_condition(self):
        vague = self.client.post("/api/v1/triage", json={"condition": "不舒服"}).get_json()["data"]
        self.assertEqual(vague["triage_status"], "INSUFFICIENT_INFORMATION")
        self.assertTrue(vague["disease_prediction"].get("abstained"))
        self.assertEqual(vague["original_condition"], "不舒服")

        followups = self.client.post(
            "/api/v1/triage/followups", json={"condition": "不舒服"}
        ).get_json()["data"]
        self.assertGreater(len(followups["followup"]["questions"]), 0)

        answered = self.client.post(
            "/api/v1/triage",
            json={
                "condition": "不舒服",
                "followup_answers": [
                    {"question_id": "duration", "value": "lt_1_week"},
                    {"question_id": "red_flag_check", "value": "none"},
                ],
            },
        ).get_json()["data"]
        self.assertEqual(answered["condition"], "不舒服")
        self.assertEqual(answered["original_condition"], "不舒服")
        self.assertNotIn("lt_1_week", answered["condition"])
        self.assertEqual(len(answered["followup_answers"]), 2)

        # Re-route attempt with richer structured answers must not invent diagnosis.
        reroute = self.client.post(
            "/api/v1/recommendations",
            json={
                "condition": "不舒服",
                "location_source": "unknown",
                "followup_answers": [
                    {"question_id": "duration", "value": "lt_1_week"},
                    {"question_id": "red_flag_check", "value": "none"},
                ],
            },
        ).get_json()["data"]
        self.assertEqual(reroute["condition"], "不舒服")
        self.assertIn("abstain", str(reroute.get("disease_prediction", {})).lower() + str(reroute.get("triage", {})).lower())

    def test_emergency_short_circuits_ordinary_ranking_and_exits_to_safety(self):
        triage = self.client.post(
            "/api/v1/triage",
            json={"condition": "持续胸痛，喘不上气，出冷汗"},
        ).get_json()["data"]
        self.assertEqual(triage["triage_status"], "EMERGENCY")
        self.assertTrue(triage["disease_prediction"].get("abstained"))
        followup = triage["triage"].get("followup") or {}
        self.assertFalse(followup.get("needed", False))

        rec = self.client.post(
            "/api/v1/recommendations",
            json={"condition": "持续胸痛，喘不上气", "location_source": "unknown"},
        ).get_json()["data"]
        self.assertEqual(rec["triage"]["level"], "emergency")
        self.assertEqual(rec["resource_strategy"]["code"], "emergency_fast_track")
        self.assertFalse(rec["resource_strategy"]["expert_enabled"])

        evidence = self.client.get("/api/v1/evidence").get_json()["data"]["safety"]
        self.assertEqual(evidence["case_count"], 142)
        self.assertEqual(evidence["red_flag_recall"], 1.0)
        self.assertEqual(evidence["emergency_false_negative"], 0)

    def test_safety_gate_precedes_learning_model_on_conflict(self):
        # Red-flag follow-up present must escalate even if the free text is vague.
        payload = self.client.post(
            "/api/v1/triage",
            json={
                "condition": "不舒服",
                "followup_answers": [{"question_id": "red_flag_check", "value": "present"}],
            },
        ).get_json()["data"]
        self.assertEqual(payload["triage_status"], "EMERGENCY")
        self.assertTrue(payload["disease_prediction"].get("abstained"))
