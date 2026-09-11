from __future__ import annotations

from unittest import TestCase

from backend.app.application.triage import TriageApplicationService
from backend.app.domain.triage.safety_gate import SafetyAction, SafetyGateDecision, TriageStatus


class TriageApplicationServiceTests(TestCase):
    def test_emergency_publication_is_composed_without_reimplementing_rules(self):
        calls: list[str] = []

        def analyze(condition, scenario):
            calls.append(f"analyze:{condition}:{scenario}")
            return {"level": "emergency", "label": "原始标签", "followup": {"needed": True}}

        def evaluate(triage):
            calls.append("evaluate")
            return SafetyGateDecision(
                status=TriageStatus.EMERGENCY,
                action=SafetyAction.EMERGENCY_ASSESSMENT,
                requires_human_review=True,
            )

        def publish_triage(triage, decision):
            calls.append("publish_triage")
            return {"label": "公开标签", "followup": {"needed": False}}

        def predict(condition, *, details):
            calls.append(f"predict:{details}")
            return {"disease": "internal-only"}

        def publish_prediction(prediction):
            calls.append("publish_prediction")
            return {"disease": "", "abstained": True}

        def build_htriage(triage):
            calls.append("build_htriage")
            return {"followup": triage["followup"]}

        def publish_htriage(payload, decision):
            calls.append("publish_htriage")
            return {"followup": {"needed": False}, "notice": "safety"}

        service = TriageApplicationService(
            analyze_triage=analyze,
            evaluate_safety=evaluate,
            publish_triage=publish_triage,
            predict_disease=predict,
            publish_prediction=publish_prediction,
            build_public_htriage=build_htriage,
            publish_htriage=publish_htriage,
            match_department=lambda condition: "急诊医学科",
        )

        payload = service.build_payload("示例描述", "common")

        self.assertEqual(payload["triage_status"], "EMERGENCY")
        self.assertEqual(payload["matched_department"], "急诊医学科")
        self.assertTrue(payload["disease_prediction"]["abstained"])
        self.assertEqual(calls, [
            "analyze:示例描述:common",
            "evaluate",
            "publish_triage",
            "predict:True",
            "publish_prediction",
            "build_htriage",
            "publish_htriage",
        ])

    def test_followup_projection_keeps_only_the_published_contract(self):
        payload = TriageApplicationService.build_followup_payload({
            "condition": "示例描述",
            "matched_department": "内科",
            "triage_status": "ROUTINE",
            "triage": {
                "label": "常规路径",
                "followup": {"needed": False},
                "known_disease": {"internal": True},
                "private_field": "not projected",
            },
            "htriage_analysis": {"notice": "assistive"},
        })

        self.assertEqual(payload, {
            "condition": "示例描述",
            "matched_department": "内科",
            "triage_status": "ROUTINE",
            "triage_label": "常规路径",
            "followup": {"needed": False},
            "known_disease": {"internal": True},
            "htriage_analysis": {"notice": "assistive"},
        })

    def test_legacy_payloads_preserve_unpublished_response_shapes(self):
        service = TriageApplicationService(
            analyze_triage=lambda condition, scenario: {
                "level": "routine",
                "label": "常规",
                "matched_department": None,
                "followup": {"question": "多久"},
                "known_disease": {"name": "未定"},
            },
            evaluate_safety=lambda triage: SafetyGateDecision(
                status=TriageStatus.ROUTINE,
                action=SafetyAction.ROUTINE_RECOMMENDATION,
                requires_human_review=False,
            ),
            publish_triage=lambda triage, decision: triage,
            predict_disease=lambda condition, *, details: {"disease": "内部结果", "details": details},
            publish_prediction=lambda prediction: prediction,
            build_public_htriage=lambda triage: {"source": "legacy"},
            publish_htriage=lambda payload, decision: payload,
            match_department=lambda condition: "内科",
        )

        triage = service.build_legacy_triage_payload("咳嗽", "common")
        followup = service.build_legacy_followup_payload("咳嗽", "common")
        assistant = service.build_legacy_assistant_payload({
            "step0": "咳嗽",
            "step1": "三天",
            "step2": "轻微",
            "step3": "没有其他症状",
        })

        self.assertEqual(triage["disease_prediction"]["disease"], "内部结果")
        self.assertEqual(followup["triage_level"], "routine")
        self.assertEqual(followup["followup"]["question"], "多久")
        self.assertEqual(assistant["condition"], "咳嗽；持续三天")
