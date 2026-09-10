from __future__ import annotations

from unittest import TestCase

from backend.app.domain.triage.safety_gate import (
    SafetyAction,
    TriageStatus,
    evaluate_safety_gate,
    triage_status_from_legacy,
)


class SafetyGateTests(TestCase):
    def test_legacy_levels_map_to_one_public_status_enum(self):
        self.assertIs(
            triage_status_from_legacy({"level": "emergency"}),
            TriageStatus.EMERGENCY,
        )
        self.assertIs(
            triage_status_from_legacy({"level": "urgent"}),
            TriageStatus.URGENT,
        )
        self.assertIs(
            triage_status_from_legacy({"level": "routine"}),
            TriageStatus.ROUTINE,
        )
        self.assertIs(
            triage_status_from_legacy({"level": "routine", "severity_bucket": "信息不足"}),
            TriageStatus.INSUFFICIENT_INFORMATION,
        )
        self.assertIs(
            triage_status_from_legacy({"level": "unknown"}),
            TriageStatus.INSUFFICIENT_INFORMATION,
        )

    def test_emergency_gate_requires_human_review_and_preserves_reasons(self):
        decision = evaluate_safety_gate({
            "level": "emergency",
            "red_flag_tags": ["呼吸困难"],
            "reasons": ["优先紧急评估"],
        })

        self.assertEqual(decision.status, TriageStatus.EMERGENCY)
        self.assertEqual(decision.action, SafetyAction.EMERGENCY_ASSESSMENT)
        self.assertTrue(decision.requires_human_review)
        self.assertEqual(decision.as_dict()["red_flag_tags"], ["呼吸困难"])

    def test_insufficient_information_gate_does_not_claim_diagnosis(self):
        decision = evaluate_safety_gate({
            "level": "routine",
            "severity_bucket": "信息不足",
        })

        self.assertEqual(decision.status, TriageStatus.INSUFFICIENT_INFORMATION)
        self.assertEqual(decision.action, SafetyAction.CLARIFY_AND_REVIEW)
        self.assertTrue(decision.requires_human_review)
