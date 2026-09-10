"""Safety-first publication helpers for public triage payloads.

The helpers redact disease-oriented outputs after the Safety Gate. They do
not evaluate red-flag rules or provide clinical advice; those decisions stay
with the existing triage rule layer and the public application adapter.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from .safety_gate import SafetyGateDecision, TriageStatus, evaluate_safety_gate


SAFETY_GATE_NOTICE = "Safety Gate 优先处理当前风险，不展示疾病候选。"


def safety_first_prediction(prediction: Mapping[str, Any] | None) -> dict[str, Any]:
    safe_prediction = dict(prediction or {})
    safe_prediction.update({
        "disease": "",
        "predictions": [],
        "abstained": True,
        "abstain_reason": "safety_gate_priority",
        "notice": SAFETY_GATE_NOTICE,
    })
    return safe_prediction


def safety_first_followup() -> dict[str, Any]:
    return {
        "needed": False,
        "confidence": "deferred_by_safety_gate",
        "missing_slots": [],
        "questions": [],
        "topk_comparison": {"need_compare": False, "focus": [], "distinguish_questions": []},
    }


def safety_first_triage(
    triage: Mapping[str, Any] | None,
    decision: SafetyGateDecision,
) -> dict[str, Any]:
    public_triage = dict(triage or {})
    if decision.status not in (TriageStatus.EMERGENCY, TriageStatus.INSUFFICIENT_INFORMATION):
        return public_triage

    public_triage["disease_candidates"] = []
    public_triage["disease_categories"] = []
    public_triage["model_disease_prediction"] = safety_first_prediction(
        public_triage.get("model_disease_prediction")
    )
    public_triage["disease_prediction_notice"] = SAFETY_GATE_NOTICE
    if decision.status is TriageStatus.EMERGENCY:
        public_triage["followup"] = safety_first_followup()
    return public_triage


def safety_first_htriage_payload(
    htriage_payload: Mapping[str, Any] | None,
    decision: SafetyGateDecision,
) -> dict[str, Any]:
    public_htriage = dict(htriage_payload or {})
    if decision.status not in (TriageStatus.EMERGENCY, TriageStatus.INSUFFICIENT_INFORMATION):
        return public_htriage

    public_htriage["disease_candidates"] = []
    public_htriage["disease_categories"] = []
    public_htriage["model_disease_prediction"] = safety_first_prediction(
        public_htriage.get("model_disease_prediction")
    )
    public_htriage["notice"] = SAFETY_GATE_NOTICE
    if decision.status is TriageStatus.EMERGENCY:
        public_htriage["followup"] = safety_first_followup()
    return public_htriage


def publish_safety_first(
    payload: Mapping[str, Any],
    triage: Mapping[str, Any] | None,
    htriage_payload_builder: Callable[[Mapping[str, Any]], Mapping[str, Any]],
) -> dict[str, Any]:
    """Publish a payload after applying the explicit Safety Gate decision."""

    decision = evaluate_safety_gate(triage)
    if decision.status not in (TriageStatus.EMERGENCY, TriageStatus.INSUFFICIENT_INFORMATION):
        return payload  # type: ignore[return-value]

    public_triage = safety_first_triage(triage, decision)
    public_payload = dict(payload)
    public_payload["triage"] = public_triage
    public_payload["htriage_analysis"] = safety_first_htriage_payload(
        htriage_payload_builder(public_triage),
        decision,
    )
    public_payload["disease_prediction"] = safety_first_prediction(
        public_payload.get("disease_prediction")
    )
    return public_payload
