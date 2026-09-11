from __future__ import annotations

from pathlib import Path
from unittest import TestCase

from backend.app.infrastructure.models.symptom_disease import SymptomDiseaseModelAdapter


class SymptomDiseaseModelAdapterTests(TestCase):
    def test_injected_runtime_preserves_normalization_and_top_k_contract(self):
        calls: list[tuple[str, int]] = []

        def predict(model, condition, *, disease_name_map, symptom_alias_map, symptom_name_map, top_k):
            calls.append((condition, top_k))
            return {"disease": "示例疾病", "predictions": ["示例疾病"]}

        adapter = SymptomDiseaseModelAdapter(
            model_dir=Path("/unused"),
            model_path=Path("/unused/model.json"),
            normalize=lambda condition: (condition.replace("喘不上来", "呼吸困难"), {"喘不上来": "呼吸困难"}),
            runtime_loader=lambda: {
                "model": {},
                "disease_name_map": {},
                "symptom_alias_map": {},
                "symptom_name_map": {},
                "predict_with_details": predict,
            },
        )

        details = adapter.predict("喘不上来", details=True)
        short = adapter.predict("咳嗽", details=False)

        self.assertEqual(details["colloquial_replacements"], {"喘不上来": "呼吸困难"})
        self.assertEqual(details["available"], True)
        self.assertEqual(short, {"disease": "示例疾病"})
        self.assertEqual(calls, [("呼吸困难", 5), ("咳嗽", 3)])
