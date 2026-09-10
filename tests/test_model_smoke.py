from __future__ import annotations

from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

import app as legacy_app


class ModelSmokeTests(TestCase):
    def setUp(self):
        self._runtime = legacy_app._SYMPTOM_DISEASE_RUNTIME
        self._runtime_error = legacy_app._SYMPTOM_DISEASE_RUNTIME_ERROR

    def tearDown(self):
        legacy_app._SYMPTOM_DISEASE_RUNTIME = self._runtime
        legacy_app._SYMPTOM_DISEASE_RUNTIME_ERROR = self._runtime_error

    def _reset_runtime(self):
        legacy_app._SYMPTOM_DISEASE_RUNTIME = None
        legacy_app._SYMPTOM_DISEASE_RUNTIME_ERROR = None

    def test_local_model_loads_and_marks_prediction_as_assistive(self):
        self._reset_runtime()

        result = legacy_app.predict_disease_name("发热 咳嗽", details=True)

        self.assertTrue(result["available"])
        self.assertIn("need_more_info", result)
        self.assertIsInstance(result["predictions"], list)
        self.assertTrue(result["predictions"])

    def test_insufficient_model_input_requests_more_information(self):
        self._reset_runtime()

        result = legacy_app.predict_disease_name("不舒服", details=True)

        self.assertTrue(result["available"])
        self.assertTrue(result["need_more_info"])

    def test_missing_model_degrades_without_disease_claim(self):
        self._reset_runtime()
        missing_path = Path(legacy_app.SYMPTOM_DISEASE_MODEL_PATH).with_name("missing-model.json")

        with patch.object(legacy_app, "SYMPTOM_DISEASE_MODEL_PATH", str(missing_path)):
            result = legacy_app.predict_disease_name("咳嗽", details=True)

        self.assertFalse(result["available"])
        self.assertEqual(result["disease"], "")
        self.assertTrue(result["error"])
