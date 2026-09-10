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

        self.assertEqual(report["case_count"], 16)
        self.assertIsNotNone(report["red_flag_recall"])
        self.assertIsNotNone(report["under_triage_rate"])
        self.assertIsNotNone(report["over_triage_rate"])
        self.assertIn("colloquial-breathlessness", report["review_required"])
        self.assertIn("vague-discomfort", report["review_required"])
        self.assertGreaterEqual(report["emergency_false_negative"], 1)
