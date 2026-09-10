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

    def test_legacy_adapter_resolves_handlers_lazily(self):
        handler = resolve_legacy_handler("api_v1_triage")
        self.assertTrue(callable(handler))
