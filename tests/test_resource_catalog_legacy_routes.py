from __future__ import annotations

from unittest import TestCase

import app as legacy_app


class LegacyResourceCatalogRouteTests(TestCase):
    def setUp(self):
        self.client = legacy_app.app.test_client()

    def test_legacy_indexes_keep_their_response_shapes_and_sources(self):
        hospitals = self.client.get("/api/hospitals")
        real_doctors = self.client.get("/api/doctors")
        mock_doctors = self.client.get("/api/doctors?real=0")

        self.assertEqual(hospitals.status_code, 200)
        self.assertEqual(hospitals.get_json()["data"], legacy_app.HOSPITALS)
        self.assertEqual(hospitals.get_json()["count"], len(legacy_app.HOSPITALS))
        self.assertEqual(real_doctors.get_json()["source"], "real")
        self.assertEqual(real_doctors.get_json()["count"], len(legacy_app.REAL_DOCTORS))
        self.assertEqual(mock_doctors.get_json()["source"], "mock")
        self.assertEqual(mock_doctors.get_json()["data"], legacy_app.DOCTORS)

    def test_legacy_resource_details_keep_fallback_and_404_behavior(self):
        hospital = self.client.get("/api/hospitals/1")
        hospital_missing = self.client.get("/api/hospitals/999999")
        doctor_id = legacy_app.DOCTORS[0]["id"]
        doctor = self.client.get(f"/api/doctors/{doctor_id}")
        doctor_missing = self.client.get("/api/doctors/999999")

        self.assertEqual(hospital.status_code, 200)
        self.assertEqual(hospital.get_json()["data"]["hospital"]["id"], 1)
        self.assertEqual(hospital.get_json()["data"]["source"], "real")
        self.assertEqual(hospital_missing.status_code, 404)
        self.assertEqual(doctor.status_code, 200)
        self.assertEqual(doctor.get_json()["data"]["doctor"]["id"], doctor_id)
        self.assertEqual(doctor_missing.status_code, 404)

    def test_legacy_relations_and_enhanced_detail_use_catalog_service(self):
        hospital_id = legacy_app.REAL_DOCTORS[0]["hospital_id"]
        relation = self.client.get(f"/api/hospitals/{hospital_id}/doctors")
        enhanced_real_id = legacy_app.REAL_DOCTORS[0]["id"]
        enhanced_real = self.client.get(f"/api/doctors/detail/{enhanced_real_id}")
        enhanced_mock_id = legacy_app.DOCTORS[0]["id"]
        enhanced_mock = self.client.get(f"/api/doctors/detail/{enhanced_mock_id}")

        self.assertEqual(relation.status_code, 200)
        self.assertEqual(relation.get_json()["data"]["hospital"]["id"], hospital_id)
        self.assertEqual(relation.get_json()["data"]["source"], "real")
        self.assertEqual(enhanced_real.status_code, 200)
        self.assertEqual(enhanced_real.get_json()["data"], legacy_app.REAL_DOCTORS[0])
        self.assertEqual(enhanced_mock.status_code, 200)
        self.assertEqual(enhanced_mock.get_json()["data"]["doctor"]["id"], enhanced_mock_id)
