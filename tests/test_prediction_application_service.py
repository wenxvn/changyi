from __future__ import annotations

from unittest import TestCase

from backend.app.application.prediction import DiseasePredictionApplicationService


class DiseasePredictionApplicationServiceTests(TestCase):
    def test_details_are_enriched_only_for_available_predictions(self):
        calls: list[str] = []

        def predict(condition, *, details):
            calls.append(f"predict:{condition}:{details}")
            return {"disease": "示例疾病", "available": True}

        def standard_tags(condition):
            calls.append(f"tags:{condition}")
            return [{"tag": "咳嗽"}], {"disease": "示例疾病"}

        service = DiseasePredictionApplicationService(
            predict_disease=predict,
            standard_symptom_tags=standard_tags,
        )

        result = service.predict("咳嗽", details=True)

        self.assertEqual(result.disease, "示例疾病")
        self.assertTrue(result.available)
        self.assertEqual(result.prediction["standard_symptom_tags"], [{"tag": "咳嗽"}])
        self.assertEqual(calls, ["predict:咳嗽:True", "tags:咳嗽"])

    def test_unavailable_and_empty_predictions_keep_route_decision_inputs(self):
        service = DiseasePredictionApplicationService(
            predict_disease=lambda condition, *, details: {"disease": "", "available": False},
            standard_symptom_tags=lambda condition: ([{"tag": "不应调用"}], {}),
        )
        unavailable = service.predict("症状", details=True)
        self.assertFalse(unavailable.available)
        self.assertEqual(unavailable.disease, "")
        self.assertNotIn("standard_symptom_tags", unavailable.prediction)

        empty = DiseasePredictionApplicationService(
            predict_disease=lambda condition, *, details: {"disease": "", "available": True},
            standard_symptom_tags=lambda condition: ([{"tag": "不应调用"}], {}),
        ).predict("信息不足", details=True)
        self.assertTrue(empty.available)
        self.assertEqual(empty.disease, "")
        self.assertNotIn("standard_symptom_tags", empty.prediction)
