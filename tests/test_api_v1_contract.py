from __future__ import annotations

from unittest import TestCase

import app as legacy_app
from backend.app.api.v1.legacy_adapter import resolve_legacy_handler


class ApiV1ContractTests(TestCase):
    def setUp(self):
        self.client = legacy_app.app.test_client()

    def test_invalid_json_uses_stable_error_envelope(self):
        response = self.client.post(
            "/api/v1/triage",
            data="not-json",
            content_type="application/json",
        )
        body = response.get_json()
        self.assertEqual(response.status_code, 400)
        self.assertEqual(set(body), {"data", "meta", "error"})
        self.assertIsNone(body["data"])
        self.assertEqual(body["error"]["code"], "INVALID_JSON")
        self.assertEqual(body["meta"]["region_code"], "320400")

    def test_undeclared_field_is_rejected_with_details(self):
        response = self.client.post(
            "/api/v1/recommendations",
            json={"condition": "咳嗽", "unexpected": True},
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["error"], {
            "code": "UNEXPECTED_FIELD",
            "message": "请求包含未声明字段",
            "details": ["unexpected"],
        })

    def test_location_and_region_boundaries_are_rejected(self):
        location = self.client.post(
            "/api/v1/recommendations",
            json={"condition": "咳嗽", "lat": 31.7},
        )
        region = self.client.post(
            "/api/v1/recommendations",
            json={"condition": "咳嗽", "region_code": "320500"},
        )
        self.assertEqual(location.status_code, 400)
        self.assertEqual(location.get_json()["error"]["code"], "INVALID_LOCATION")
        self.assertEqual(region.status_code, 400)
        self.assertEqual(region.get_json()["error"]["code"], "REGION_NOT_ACTIVE")

    def test_v1_and_legacy_triage_keep_emergency_status(self):
        payload = {"condition": "突发胸痛伴呼吸困难"}
        v1 = self.client.post("/api/v1/triage", json=payload)
        legacy = self.client.post("/api/triage", json=payload)
        self.assertEqual(v1.status_code, 200)
        self.assertEqual(legacy.status_code, 200)
        self.assertEqual(v1.get_json()["data"]["triage_status"], "EMERGENCY")
        self.assertEqual(legacy.get_json()["data"]["triage"]["level"], "emergency")

    def test_catalog_adapter_preserves_public_source_markers(self):
        hospitals = self.client.get("/api/v1/hospitals").get_json()["data"]
        doctors = self.client.get("/api/v1/doctors").get_json()["data"]
        self.assertEqual(hospitals["source"], "legacy_catalog_pending_provenance")
        self.assertEqual(hospitals["count"], len(hospitals["items"]))
        self.assertEqual(doctors["count"], len(doctors["items"]))

    def test_resource_detail_is_allowlisted_and_provenance_explicit(self):
        hospital_response = self.client.get("/api/v1/hospitals/1")
        hospital = hospital_response.get_json()["data"]
        self.assertEqual(hospital_response.status_code, 200)
        self.assertEqual(hospital["resource_type"], "hospital")
        self.assertEqual(hospital["provenance"]["status"], "migration_pending")
        self.assertIsNone(hospital["provenance"]["last_updated"])
        self.assertNotIn("beds", hospital["resource"])
        self.assertNotIn("rating", hospital["resource"])

        doctors = self.client.get("/api/v1/doctors").get_json()["data"]["items"]
        doctor_response = self.client.get(f"/api/v1/doctors/{doctors[0]['id']}")
        doctor = doctor_response.get_json()["data"]
        self.assertEqual(doctor_response.status_code, 200)
        self.assertEqual(doctor["resource_type"], "doctor")
        self.assertEqual(doctor["provenance"]["source_class"], "public_source_mixed")
        self.assertNotIn("achievements", doctor["resource"])
        self.assertNotIn("doctor_page_url", doctor["resource"])
        self.assertIsNotNone(doctor["related"]["hospital"])

        missing = self.client.get("/api/v1/hospitals/999999")
        self.assertEqual(missing.status_code, 404)
        self.assertEqual(missing.get_json()["error"]["code"], "RESOURCE_NOT_FOUND")

    def test_evidence_endpoint_exposes_provisional_runtime_facts(self):
        response = self.client.get("/api/v1/evidence")
        body = response.get_json()
        evidence = body["data"]
        self.assertEqual(response.status_code, 200)
        self.assertEqual(evidence["status"], "provisional")
        self.assertEqual(evidence["safety"]["case_count"], 16)
        self.assertEqual(evidence["model"]["class_count"], 41)
        self.assertGreaterEqual(evidence["data_quality"]["issue_count"], 0)
        self.assertTrue(evidence["dataset_manifest"])
        self.assertTrue(all(len(item["sha256"]) == 64 for item in evidence["dataset_manifest"]))
        self.assertIn("不代表临床验证", evidence["disclaimer"])

    def test_map_endpoint_keeps_resource_and_coordinate_contract(self):
        response = self.client.get("/api/v1/map")
        body = response.get_json()
        payload = body["data"]
        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["count"], len(payload["items"]))
        self.assertEqual(payload["distance_method"], None)
        self.assertTrue(all(item["map_point"] for item in payload["items"]))
        self.assertTrue(any(item["marker_type"] == "EMERGENCY_CAPABLE" for item in payload["items"]))

        located = self.client.get("/api/v1/map?lat=31.77&lng=119.96").get_json()["data"]
        self.assertEqual(located["distance_method"], "haversine_straight_line_km")
        self.assertTrue(all(item["distance_km"] is not None for item in located["items"]))

        invalid = self.client.get("/api/v1/map?lat=31.77")
        self.assertEqual(invalid.status_code, 400)
        self.assertEqual(invalid.get_json()["error"]["code"], "INVALID_LOCATION")

    def test_legacy_adapter_resolves_handlers_lazily(self):
        handler = resolve_legacy_handler("api_v1_triage")
        self.assertTrue(callable(handler))
