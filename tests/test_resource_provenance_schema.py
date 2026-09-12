from __future__ import annotations

import json
from pathlib import Path
from unittest import TestCase


ROOT = Path(__file__).resolve().parents[1]


class DoctorPhotoProvenanceSchemaTests(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload = json.loads(
            (ROOT / "data" / "resource_provenance" / "doctor_photos.json").read_text(encoding="utf-8")
        )

    def test_schema_version_and_policy_distinguish_public_from_original_source(self):
        self.assertEqual(self.payload["schema_version"], "doctor-photo-provenance/v2")
        policy = self.payload["policy"]
        self.assertTrue(policy["public_url_is_not_original_source"])
        self.assertTrue(policy["unverified_not_written_to_photo_url"])
        self.assertEqual(
            set(policy["displayable_statuses"]),
            {"SOURCE_VERIFIED", "LEGACY_EXACT_MATCH", "MANUAL_CONFIRMED"},
        )

    def test_entries_carry_required_fields_without_faking_original_source(self):
        required = {
            "doctor_name",
            "hospital_id",
            "local_path",
            "public_url",
            "doctor_page_url",
            "original_image_url",
            "source_provider",
            "license_status",
            "reuse_status",
            "mapping_method",
            "verification_status",
        }
        self.assertEqual(self.payload["count"], len(self.payload["entries"]))
        for entry in self.payload["entries"]:
            self.assertTrue(required.issubset(entry.keys()))
            self.assertTrue(str(entry["public_url"]).startswith("/static/"))
            # public_url is the app-hosted path, never the original source.
            self.assertIsNone(entry["original_image_url"])
            self.assertIsNone(entry["original_source_url"])
            self.assertNotEqual(entry["verification_status"], "SOURCE_VERIFIED")
            self.assertIn(
                entry["verification_status"],
                {"LEGACY_EXACT_MATCH", "MANUAL_CONFIRMED", "UNVERIFIED", "SOURCE_VERIFIED"},
            )


class HospitalCatalogFieldProvenanceTests(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = json.loads(
            (ROOT / "data" / "regions" / "320400" / "hospitals" / "catalog.json").read_text(encoding="utf-8")
        )

    def test_dataset_exposes_field_provenance_for_key_public_facts(self):
        fields = self.catalog["field_provenance"]
        for key in ("name", "level", "type", "address", "district", "phone", "departments", "emergency"):
            self.assertIn(key, fields)
            self.assertIn("status", fields[key])
            self.assertIn("license_status", fields[key])
        self.assertEqual(self.catalog["license_status"], "not_recorded")
        self.assertIn("reuse_note", self.catalog)

    def test_each_record_keeps_provenance_and_emergency_is_not_realtime(self):
        for record in self.catalog["records"]:
            provenance = record["_provenance"]
            self.assertEqual(provenance["source_class"], "legacy_catalog_import")
            self.assertEqual(provenance["status"], "provisional")
            self.assertIn("fields", provenance)
            emergency_note = provenance["fields"]["emergency"]["note"]
            self.assertIn("不表示实时", emergency_note)


class TransitProvenanceStaysProvisionalTests(TestCase):
    def test_transit_datasets_remain_non_rankable_without_sources(self):
        metadata = json.loads(
            (ROOT / "data" / "transit" / "metadata.json").read_text(encoding="utf-8")
        )
        self.assertTrue(metadata["policy"]["unverified_not_rankable"])
        for dataset in metadata["datasets"].values():
            self.assertEqual(dataset["verification_status"], "PROVISIONAL")
            self.assertIsNone(dataset["source_url"])
            self.assertEqual(dataset["license_status"], "not_recorded")
