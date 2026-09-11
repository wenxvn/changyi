from __future__ import annotations

from unittest import TestCase

from evaluation.safety.evaluate_safety import evaluate_cases, load_cases


class SafetyEvaluationSetTests(TestCase):
    def test_set_covers_required_safety_categories(self):
        cases = load_cases()
        categories = {case["category"] for case in cases}
        self.assertGreaterEqual(
            categories,
            {
                "cardiovascular_emergency",
                "stroke",
                "breathlessness",
                "acute_abdomen",
                "severe_trauma",
                "altered_consciousness",
                "allergy",
                "obstetric",
                "critical_child",
                "eye_emergency",
                "mental_crisis",
                "negation",
                "colloquial",
                "insufficient_information",
            },
        )

    def test_baseline_metrics_keep_known_gaps_visible(self):
        report = evaluate_cases(load_cases())

        self.assertGreaterEqual(report["case_count"], 30)
        self.assertIsNotNone(report["red_flag_recall"])
        self.assertIsNotNone(report["under_triage_rate"])
        self.assertIsNotNone(report["over_triage_rate"])
        self.assertEqual(report["emergency_false_negative"], 0)
        self.assertEqual(report["red_flag_recall"], 1.0)
        self.assertIn("emergency_case_count", report)
        self.assertIn("urgent_case_count", report)
        self.assertIn("routine_case_count", report)
        self.assertIn("insufficient_case_count", report)
        self.assertEqual(report["insufficient_information_matches"], report["insufficient_information_count"])

    def test_safety_regression_keeps_negative_and_vague_inputs_out_of_emergency(self):
        report = evaluate_cases(load_cases())
        rows = {row["id"]: row for row in report["cases"]}

        self.assertEqual(rows["negation-only"]["observed_status"], "ROUTINE")
        self.assertEqual(rows["historical-chest-pain"]["observed_status"], "URGENT")
        self.assertEqual(rows["question-about-chest-pain"]["observed_status"], "URGENT")
        self.assertEqual(rows["vague-discomfort"]["observed_status"], "INSUFFICIENT_INFORMATION")
        self.assertEqual(rows["vague-not-well"]["observed_status"], "INSUFFICIENT_INFORMATION")
