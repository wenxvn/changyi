from __future__ import annotations

from unittest import TestCase

import app as application_entry
from backend.app.api.v1.schemas.recommendation import RecommendationRequest, RequestValidationError
from backend.app.domain.recommendation.features import hospital_availability_score


class P0CorrectnessCompletionTests(TestCase):
    def setUp(self):
        self.client = application_entry.app.test_client()

    def test_location_source_has_explicit_unknown_district_and_geolocation_semantics(self):
        unknown = RecommendationRequest.parse({"condition": "咳嗽"})
        district = RecommendationRequest.parse({"condition": "咳嗽", "district": "武进区"})
        precise = RecommendationRequest.parse({
            "condition": "咳嗽",
            "lat": 31.77,
            "lng": 119.96,
            "location_source": "geolocation",
        })

        self.assertEqual((unknown.location_source, unknown.lat, unknown.lng), ("unknown", None, None))
        self.assertEqual((district.location_source, district.lat, district.lng), ("district", None, None))
        self.assertEqual((precise.location_source, precise.lat, precise.lng), ("geolocation", 31.77, 119.96))
        for payload in (
            {"condition": "咳嗽", "location_source": "unknown", "district": "武进区"},
            {"condition": "咳嗽", "location_source": "geolocation", "lat": 31.77, "lng": 119.96, "district": "武进区"},
            {"condition": "咳嗽", "location_source": "district"},
        ):
            with self.assertRaises(RequestValidationError):
                RecommendationRequest.parse(payload)

    def test_recommendation_does_not_invent_location_or_rank_on_unavailable_facts(self):
        unknown = self.client.post("/api/v1/recommendations", json={"condition": "咳嗽"})
        unknown_payload = unknown.get_json()["data"]
        self.assertEqual(unknown.status_code, 200)
        self.assertEqual(unknown_payload["user_location"], {
            "district": None,
            "lat": None,
            "lng": None,
            "source": "unknown",
        })
        self.assertFalse(unknown_payload["feature_availability"]["distance"])
        self.assertTrue(all(item["distance"] is None for item in unknown_payload["recommended_hospitals"]))
        self.assertEqual(unknown_payload["hospital_weights_used"]["accessibility"], 0.0)
        self.assertEqual(unknown_payload["hospital_weights_used"]["availability"], 0.0)

        district = self.client.post(
            "/api/v1/recommendations",
            json={"condition": "咳嗽", "district": "武进区"},
        ).get_json()["data"]
        self.assertEqual(district["user_location"]["source"], "district")
        self.assertEqual(district["user_location"]["lat"], 31.73)
        self.assertTrue(all(item["distance"] is not None for item in district["recommended_hospitals"]))
        self.assertEqual(district["recommended_hospitals"][0]["ranking_weights"]["availability"], 0.0)

    def test_structured_followup_answers_never_contaminate_original_condition(self):
        response = self.client.post(
            "/api/v1/triage",
            json={
                "condition": "最近头晕",
                "followup_answers": [
                    {"question_id": "duration", "value": "lt_1_week"},
                    {"question_id": "red_flag_check", "value": "none"},
                ],
            },
        )
        payload = response.get_json()["data"]
        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["condition"], "最近头晕")
        self.assertEqual(payload["htriage_analysis"]["original_condition"], "最近头晕")
        self.assertEqual(len(payload["followup_answers"]), 2)
        self.assertNotIn("lt_1_week", payload["condition"])
        self.assertNotIn("duration", payload["condition"])

        present = self.client.post(
            "/api/v1/triage",
            json={
                "condition": "最近头晕",
                "followup_answers": [{"question_id": "red_flag_check", "value": "present"}],
            },
        ).get_json()["data"]
        unknown = self.client.post(
            "/api/v1/triage",
            json={
                "condition": "最近头晕",
                "followup_answers": [{"question_id": "red_flag_check", "value": "unknown"}],
            },
        ).get_json()["data"]
        self.assertEqual(present["triage_status"], "EMERGENCY")
        self.assertEqual(unknown["triage_status"], "INSUFFICIENT_INFORMATION")
        self.assertEqual(unknown["triage"]["severity_bucket"], "信息不足")

    def test_followup_options_are_structured_and_answered_questions_are_removed(self):
        initial = self.client.post("/api/v1/triage/followups", json={"condition": "不舒服"}).get_json()["data"]
        options = [option for question in initial["followup"]["questions"] for option in question["options"]]
        self.assertTrue(options)
        self.assertTrue(all(set(option) == {"label", "value"} for option in options))

        next_payload = self.client.post(
            "/api/v1/triage/followups",
            json={
                "condition": "不舒服",
                "followup_answers": [{"question_id": "duration", "value": "lt_1_week"}],
            },
        ).get_json()["data"]
        question_ids = {question["id"] for question in next_payload["followup"]["questions"]}
        self.assertNotIn("duration", question_ids)

    def test_hospital_catalog_separates_derived_and_unsupported_fields(self):
        detail = self.client.get("/api/v1/hospitals/1").get_json()["data"]
        resource = detail["resource"]
        self.assertNotIn("beds", resource)
        self.assertNotIn("daily_outpatients", resource)
        self.assertNotIn("rating", resource)
        self.assertNotIn("description", resource)
        self.assertIn("derived_capability_areas", resource)
        self.assertEqual(detail["derived_capability"]["status"], "provisional")
        self.assertTrue(detail["related"]["doctors"])

        self.assertEqual(hospital_availability_score({"emergency": True}), 0.0)

    def test_map_location_contract_keeps_unknown_and_reference_distance_distinct(self):
        unknown = self.client.get("/api/v1/map").get_json()["data"]
        self.assertEqual(unknown["user_location"], {"lat": None, "lng": None, "source": "unknown"})
        self.assertIsNone(unknown["distance_method"])
        self.assertTrue(all(item["distance_km"] is None for item in unknown["items"]))

        district = self.client.get("/api/v1/map?district=武进区&location_source=district").get_json()["data"]
        self.assertEqual(district["user_location"]["source"], "district")
        self.assertEqual(district["distance_method"], "haversine_reference_point_km")
        self.assertIn("区域参考点估算", district["notice"])

        ambiguous = self.client.get("/api/v1/map?district=武进区&lat=31.73&lng=119.95")
        self.assertEqual(ambiguous.status_code, 400)
        self.assertEqual(ambiguous.get_json()["error"]["code"], "INVALID_LOCATION")
