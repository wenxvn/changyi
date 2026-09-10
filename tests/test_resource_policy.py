from __future__ import annotations

from unittest import TestCase

from backend.app.domain.recommendation.resource_policy import (
    apply_resource_fit,
    doctor_resource_mismatch_penalty,
    resource_strategy,
)


class ResourcePolicyTests(TestCase):
    def test_emergency_strategy_overrides_expert_preference(self):
        strategy = resource_strategy({"level": "emergency"}, "must_expert")
        self.assertEqual(strategy["code"], "emergency_fast_track")
        self.assertFalse(strategy["expert_enabled"])
        self.assertTrue(strategy["top_expert_allowed"])

    def test_urgent_strategy_distinguishes_specialty_followup(self):
        followup = resource_strategy(
            {"level": "urgent", "severity_bucket": "专科病情/需评估"},
            "system",
        )
        priority = resource_strategy({"level": "urgent"}, "no_expert")
        self.assertEqual(followup["code"], "specialty_followup")
        self.assertEqual(priority["code"], "specialty_priority")
        self.assertFalse(priority["expert_enabled"])

    def test_resource_fit_keeps_routine_caps_and_emergency_notice(self):
        routine, notes, cap = apply_resource_fit(
            0.9,
            "top_expert",
            "routine",
            "system",
            {"top_expert_allowed": False},
            0.8,
        )
        self.assertEqual(routine, 0.68)
        self.assertEqual(cap, 0.68)
        self.assertIn("普通病症降低顶级专家资源占用", notes)

        emergency, emergency_notes, emergency_cap = apply_resource_fit(
            0.9,
            "top_expert",
            "emergency",
            "must_expert",
            {"top_expert_allowed": True},
            0.2,
        )
        self.assertEqual(emergency, 0.9)
        self.assertEqual(emergency_cap, 1.0)
        self.assertIn("急症按急诊能力与距离优先", emergency_notes)

    def test_mismatch_penalty_reports_safety_relevant_reasons(self):
        penalty, details = doctor_resource_mismatch_penalty(
            {},
            {"emergency": False},
            "specialist",
            "emergency",
            "no_expert",
            specialty_score=0.4,
            hospital_score=0.4,
            access_score=0.3,
            target_dept="心血管内科",
        )
        self.assertEqual(penalty, 0.3)
        self.assertEqual({item["code"] for item in details}, {"emergency", "access", "specialty", "preference"})

    def test_routine_mismatch_penalty_preserves_top_expert_overuse_rule(self):
        penalty, details = doctor_resource_mismatch_penalty(
            {},
            {"emergency": True},
            "top_expert",
            "routine",
            "system",
            specialty_score=0.8,
            hospital_score=0.8,
            access_score=0.4,
            target_dept="心血管内科",
        )
        self.assertEqual(penalty, 0.14)
        self.assertEqual([item["code"] for item in details], ["overuse", "access"])
