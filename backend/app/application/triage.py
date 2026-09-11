"""Application orchestration for the versioned triage boundary.

This module deliberately does not contain triage rules.  It sequences the
existing rule, Safety Gate, publication, and model helpers so the Flask
adapter can stay focused on request validation and response envelopes.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

from ..domain.triage.safety_gate import SafetyGateDecision, TriageStatus


AnalyzeTriage = Callable[..., Mapping[str, Any]]
EvaluateSafety = Callable[[Mapping[str, Any]], SafetyGateDecision]
PublishTriage = Callable[[Mapping[str, Any], SafetyGateDecision], Mapping[str, Any]]
PredictDisease = Callable[..., Mapping[str, Any]]
PublishPrediction = Callable[[Mapping[str, Any]], Mapping[str, Any]]
BuildPublicHtriage = Callable[[Mapping[str, Any]], Mapping[str, Any]]
PublishHtriage = Callable[[Mapping[str, Any], SafetyGateDecision], Mapping[str, Any]]


@dataclass(frozen=True)
class TriageApplicationService:
    """Compose existing triage dependencies without owning medical policy."""

    analyze_triage: AnalyzeTriage
    evaluate_safety: EvaluateSafety
    publish_triage: PublishTriage
    predict_disease: PredictDisease
    publish_prediction: PublishPrediction
    build_public_htriage: BuildPublicHtriage
    publish_htriage: PublishHtriage
    match_department: Callable[[str], str | None]

    def _analyze(
        self,
        condition: str,
        scenario: str,
        followup_answers: tuple[dict[str, Any], ...] = (),
    ) -> Mapping[str, Any]:
        """Pass structured answers only when present for compatibility adapters."""

        if followup_answers:
            return self.analyze_triage(condition, scenario, followup_answers)
        return self.analyze_triage(condition, scenario)

    def build_legacy_triage_payload(self, condition: str, scenario: str) -> dict[str, Any]:
        """Compose the original triage response without Safety-first projection."""

        triage = self.analyze_triage(condition, scenario)
        return {
            "condition": condition,
            "matched_department": triage.get("matched_department") or self.match_department(condition),
            "disease_prediction": dict(self.predict_disease(condition, details=True)),
            "triage": triage,
            "htriage_analysis": dict(self.build_public_htriage(triage)),
        }

    def build_legacy_followup_payload(self, condition: str, scenario: str) -> dict[str, Any]:
        """Compose the original follow-up response without changing its contract."""

        triage = self.analyze_triage(condition, scenario)
        return {
            "condition": condition,
            "matched_department": triage.get("matched_department") or self.match_department(condition),
            "triage_level": triage.get("level"),
            "triage_label": triage.get("label"),
            "htriage_analysis": dict(self.build_public_htriage(triage)),
            "followup": triage.get("followup", {}),
            "known_disease": triage.get("known_disease", {}),
        }

    def build_legacy_assistant_payload(self, answers: Mapping[str, Any]) -> dict[str, Any]:
        """Compose the original assistant answer projection and triage payload."""

        parts: list[str] = []
        if answers.get("step0"):
            parts.append(answers["step0"])
        if answers.get("step1"):
            parts.append(f"持续{answers['step1']}")
        if answers.get("step2"):
            severity = answers["step2"]
            if "较严重" in severity:
                parts.insert(0, "严重症状")
            elif "严重" in severity:
                parts.insert(0, "中度症状")
        if answers.get("step3") and answers["step3"] != "没有其他症状":
            parts.append(answers["step3"])

        condition = "；".join(parts) if parts else answers.get("step0", "")
        matched_department = self.match_department(answers.get("step0", ""))
        triage = self.analyze_triage(condition, "first_visit")
        return {
            "condition": condition,
            "matched_department": matched_department,
            "disease_prediction": dict(self.predict_disease(condition, details=True)),
            "triage": triage,
            "htriage_analysis": dict(self.build_public_htriage(triage)),
        }

    def build_payload(
        self,
        condition: str,
        scenario: str,
        followup_answers: tuple[dict[str, Any], ...] = (),
    ) -> dict[str, Any]:
        triage = self._analyze(condition, scenario, followup_answers)
        decision = self.evaluate_safety(triage)
        public_triage = dict(self.publish_triage(triage, decision))
        prediction = self.predict_disease(condition, details=True)
        if decision.status in (TriageStatus.EMERGENCY, TriageStatus.INSUFFICIENT_INFORMATION):
            public_prediction: Mapping[str, Any] = self.publish_prediction(prediction)
        else:
            public_prediction = prediction
        return {
            "condition": condition,
            "original_condition": condition,
            "followup_answers": list(followup_answers),
            "matched_department": public_triage.get("matched_department") or self.match_department(condition),
            "triage_status": decision.status.value,
            "disease_prediction": dict(public_prediction),
            "triage": public_triage,
            "htriage_analysis": dict(self.publish_htriage(self.build_public_htriage(public_triage), decision)),
        }

    @staticmethod
    def build_followup_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
        triage = payload.get("triage") or {}
        result = {
            "condition": payload.get("condition", ""),
            "matched_department": payload.get("matched_department"),
            "triage_status": payload.get("triage_status"),
            "triage_label": triage.get("label"),
            "followup": triage.get("followup", {}),
            "known_disease": triage.get("known_disease", {}),
            "htriage_analysis": payload.get("htriage_analysis", {}),
        }
        if "original_condition" in payload:
            result["original_condition"] = payload.get("original_condition")
        if "followup_answers" in payload:
            result["followup_answers"] = payload.get("followup_answers", [])
        return result
