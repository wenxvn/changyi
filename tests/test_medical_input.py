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

    def test_hard_boundary_allows_a_later_positive_occurrence(self):
        text = "既往没有胸痛；现在胸痛"

        self.assertTrue(contains_positive(text, ["胸痛"]))


if __name__ == "__main__":
    import unittest

    unittest.main()
