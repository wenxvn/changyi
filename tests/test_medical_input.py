from __future__ import annotations

from unittest import TestCase

import app as application_entry
from backend.app.domain.medical_input import contains_positive, normalize_patient_expression


class MedicalInputBoundaryTests(TestCase):
    def test_legacy_exports_use_the_domain_normalizer(self):
        self.assertIs(application_entry.normalize_patient_expression, normalize_patient_expression)
        self.assertIs(application_entry._contains_positive, contains_positive)

    def test_colloquial_red_flag_alias_is_preserved(self):
        normalized, replacements = normalize_patient_expression("喘不上来")

        self.assertIn("呼吸困难", normalized)
        self.assertEqual(replacements, [{"raw": "喘不上来", "standard": "呼吸困难"}])

    def test_negation_window_and_turning_point_are_preserved(self):
        text = "没有胸痛，但出现呼吸困难"

        self.assertFalse(contains_positive(text, ["胸痛"]))
        self.assertTrue(contains_positive(text, ["呼吸困难"]))
        self.assertFalse(contains_positive("否认呼吸困难", ["呼吸困难"]))

    def test_double_negation_is_not_treated_as_clear_denial(self):
        self.assertTrue(contains_positive("不是没有呼吸困难", ["呼吸困难"]))
        self.assertTrue(contains_positive("并非没有胸痛", ["胸痛"]))
        self.assertTrue(contains_positive("不能说没有胸闷", ["胸闷"]))
        self.assertFalse(contains_positive("没有呼吸困难", ["呼吸困难"]))

    def test_hard_boundary_allows_a_later_positive_occurrence(self):
        text = "既往没有胸痛；现在胸痛"

        self.assertTrue(contains_positive(text, ["胸痛"]))


class TriageWhitespaceSafetyTests(TestCase):
    def test_collapsed_whitespace_still_hits_red_flag_keywords(self):
        from backend.app.composition import analyze_medical_triage
        from backend.app.domain.triage.safety_gate import triage_status_from_legacy

        noisy = analyze_medical_triage("喘 不 上 气")
        spaced_pair = analyze_medical_triage("胸 痛 并 呼 吸 困 难")

        self.assertEqual(triage_status_from_legacy(noisy).value, "EMERGENCY")
        self.assertEqual(triage_status_from_legacy(spaced_pair).value, "EMERGENCY")


if __name__ == "__main__":
    import unittest

    unittest.main()
