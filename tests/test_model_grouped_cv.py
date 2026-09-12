from __future__ import annotations

from unittest import TestCase

from evaluation.model.evaluate_grouped import (
    assign_components_to_folds,
    grouped_cross_validation,
    near_duplicate_components,
)
from data.symptom_disease_model.train import load_dataset
from pathlib import Path


class GroupedCrossValidationTests(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = load_dataset(
            Path("data/symptom_disease_model/data/disease_symptom_structured_41diseases_long.csv")
        )
        cls.components, cls.stats = near_duplicate_components(cls.rows, mode="same_label")

    def test_component_assignment_never_splits_a_component(self):
        folds = assign_components_to_folds(self.rows, self.components, n_folds=5, seed=42)
        for component in self.components:
            assigned = {folds[index] for index in component}
            self.assertEqual(len(assigned), 1, "near-duplicate component crossed folds")

    def test_grouped_cv_keeps_cross_split_near_duplicates_at_zero(self):
        report = grouped_cross_validation(self.rows, self.components, n_folds=5, seed=42)

        self.assertEqual(report["fold_count"], 5)
        self.assertEqual(report["cross_split_near_duplicates_max_pair_count"], 0)
        self.assertEqual(report["class_coverage_across_folds"]["present_class_count"], 41)
        self.assertTrue(report["offline_prototype_only"])
        self.assertFalse(report["clinical_validation"])
        for fold in report["folds"]:
            self.assertGreater(fold["train_rows"], 0)
            self.assertGreater(fold["validation_rows"], 0)
            self.assertEqual(fold["cross_split_near_duplicates"]["pair_count"], 0)
        for key in ("top1_accuracy", "top3_accuracy", "macro_f1", "coverage"):
            self.assertIn(key, report["aggregate"])
            self.assertIn("mean", report["aggregate"][key])
            self.assertIn("std", report["aggregate"][key])
            self.assertIn("weighted", report["aggregate"][key])
