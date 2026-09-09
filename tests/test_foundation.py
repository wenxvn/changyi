from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from backend.app.infrastructure.data.loaders import DataLoadError, JsonDataLoader
from backend.app.infrastructure.regions.registry import RegionRegistry
from backend.app.infrastructure.repositories.doctor_repository import DoctorRepository
from backend.app.infrastructure.repositories.transit_repository import TransitRepository
from backend.app.api.v1.response import failure, success
from backend.app.api.v1.schemas.recommendation import RecommendationRequest, RequestValidationError
from data_validation.validate_datasets import validate_data_root


ROOT = Path(__file__).resolve().parents[1]


class LoaderTests(unittest.TestCase):
    def test_loader_rejects_path_escape(self):
        loader = JsonDataLoader(ROOT)
        with self.assertRaises(DataLoadError):
            loader.load("../outside.json")

    def test_loader_reports_malformed_json(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "broken.json").write_text("{", encoding="utf-8")
            with self.assertRaises(DataLoadError):
                JsonDataLoader(root).load("broken.json")


class RegionRegistryTests(unittest.TestCase):
    def test_changzhou_pack_is_the_only_active_region(self):
        registry = RegionRegistry.from_root(ROOT / "data" / "regions")
        self.assertEqual([context.code for context in registry.active()], ["320400"])
        self.assertEqual(registry.get("320400").get_district("天宁区")["code"], "320402")

    def test_manifest_relative_sources_are_loadable(self):
        registry = RegionRegistry.from_root(ROOT / "data" / "regions")
        region = registry.get("320400")
        loader = JsonDataLoader(ROOT)
        self.assertEqual(DoctorRepository(region, loader).count(), 2100)
        self.assertEqual(len(TransitRepository(region, loader).list("bus_routes")), 50)


class DataAuditTests(unittest.TestCase):
    def test_report_is_deterministic_for_same_input(self):
        first = validate_data_root(ROOT / "data")
        second = validate_data_root(ROOT / "data")
        self.assertEqual(first, second)
        self.assertGreater(first["dataset_count"], 0)

    def test_manifest_paths_resolve_inside_data_root(self):
        report = validate_data_root(ROOT / "data")
        missing = [item for item in report["issues"] if item["code"] == "DECLARED_FILE_MISSING"]
        self.assertEqual(missing, [])


class CharacterizationCaseTests(unittest.TestCase):
    def test_cases_are_machine_readable(self):
        cases = json.loads((ROOT / "tests" / "characterization" / "cases.json").read_text(encoding="utf-8"))
        self.assertEqual(cases["schema_version"], "characterization-cases/v1")
        self.assertEqual(len(cases["cases"]), 5)
        self.assertTrue(all(item["input"].get("condition") for item in cases["cases"]))


class ContractTests(unittest.TestCase):
    def test_recommendation_request_rejects_non_active_region(self):
        with self.assertRaises(RequestValidationError) as context:
            RecommendationRequest.parse({"condition": "咳嗽", "region_code": "320100"})
        self.assertEqual(context.exception.code, "REGION_NOT_ACTIVE")

    def test_response_envelope_has_stable_error_shape(self):
        self.assertEqual(success({}, region_code="320400", model_version="test")["error"], None)
        body = failure("INVALID", "bad", region_code="320400", model_version="test")
        self.assertEqual(body["data"], None)
        self.assertEqual(body["error"]["code"], "INVALID")


if __name__ == "__main__":
    unittest.main()
