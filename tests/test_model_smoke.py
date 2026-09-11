from __future__ import annotations

from pathlib import Path
from unittest import TestCase
import app as application_entry
from backend.app.infrastructure.models.symptom_disease import SymptomDiseaseModelAdapter


class ModelSmokeTests(TestCase):
    def setUp(self):
        self._adapter = application_entry.SYMPTOM_DISEASE_MODEL_ADAPTER
        self._runtime = self._adapter._runtime
        self._runtime_error = self._adapter._runtime_error
        self._runtime_loader_called = self._adapter._runtime_loader_called

    def tearDown(self):
        self._adapter._runtime = self._runtime
        self._adapter._runtime_error = self._runtime_error
        self._adapter._runtime_loader_called = self._runtime_loader_called

    def _reset_runtime(self):
        self._adapter._runtime = None
        self._adapter._runtime_error = None
        self._adapter._runtime_loader_called = False

    def test_local_model_loads_and_marks_prediction_as_assistive(self):
        self._reset_runtime()

        result = application_entry.predict_disease_name("发热 咳嗽", details=True)

        self.assertTrue(result["available"])
        self.assertIn("need_more_info", result)
        self.assertIsInstance(result["predictions"], list)
        self.assertTrue(result["predictions"])

    def test_insufficient_model_input_requests_more_information(self):
        self._reset_runtime()

        result = application_entry.predict_disease_name("不舒服", details=True)

        self.assertTrue(result["available"])
        self.assertTrue(result["need_more_info"])

    def test_missing_model_degrades_without_disease_claim(self):
        missing_path = Path(application_entry.SYMPTOM_DISEASE_MODEL_PATH).with_name("missing-model.json")
        adapter = SymptomDiseaseModelAdapter(
            model_dir=Path(application_entry.SYMPTOM_DISEASE_MODEL_DIR),
            model_path=missing_path,
            normalize=application_entry.normalize_patient_expression,
        )

        result = adapter.predict("咳嗽", details=True)

        self.assertFalse(result["available"])
        self.assertEqual(result["disease"], "")
        self.assertTrue(result["error"])
