"""Safety Gate contracts for already-evaluated triage results.

This module does not decide medical rules.  It translates the legacy triage
result into a stable public status and an explicit next-action contract so
that API adapters cannot accidentally treat a visit scenario as a triage
level.  Rule changes remain an L3 medical review task.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping


class TriageStatus(str, Enum):
    """Stable public triage statuses; distinct from visit scenarios."""

    EMERGENCY = "EMERGENCY"
    URGENT = "URGENT"
    ROUTINE = "ROUTINE"
    INSUFFICIENT_INFORMATION = "INSUFFICIENT_INFORMATION"


class SafetyAction(str, Enum):
    """Non-diagnostic next-action categories exposed by the Safety Gate."""

    EMERGENCY_ASSESSMENT = "EMERGENCY_ASSESSMENT"
    CLARIFY_AND_REVIEW = "CLARIFY_AND_REVIEW"
    CONTINUE_ASSISTIVE_PATH = "CONTINUE_ASSISTIVE_PATH"


@dataclass(frozen=True)
class SafetyGateDecision:
    """Immutable safety handoff from triage to later application stages."""

    status: TriageStatus
    action: SafetyAction
    requires_human_review: bool
    red_flag_tags: tuple[str, ...] = ()
    reasons: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        """Return JSON-safe data without claiming a diagnosis."""

        return {
            "status": self.status.value,
            "action": self.action.value,
            "requires_human_review": self.requires_human_review,
            "red_flag_tags": list(self.red_flag_tags),
            "reasons": list(self.reasons),
        }


def triage_status_from_legacy(triage: Mapping[str, Any] | None) -> TriageStatus:
    """Map the existing triage shape to the single public status enum."""

    data = triage or {}
    if data.get("severity_bucket") == "信息不足":
        return TriageStatus.INSUFFICIENT_INFORMATION
    return {
        "emergency": TriageStatus.EMERGENCY,
        "urgent": TriageStatus.URGENT,
        "routine": TriageStatus.ROUTINE,
    }.get(data.get("level"), TriageStatus.INSUFFICIENT_INFORMATION)


def evaluate_safety_gate(triage: Mapping[str, Any] | None) -> SafetyGateDecision:
    """Create an explicit handoff decision from legacy triage output.

    The function intentionally consumes, rather than reimplements, red-flag
    rules.  This keeps the extraction behavior-preserving and makes any later
    medical policy change visible as a separate L3 change.
    """

    data = triage or {}
    status = triage_status_from_legacy(data)
    red_flag_tags = tuple(
        tag for tag in (data.get("red_flag_tags") or ()) if isinstance(tag, str) and tag
    )
    reasons = tuple(
        reason for reason in (data.get("reasons") or ()) if isinstance(reason, str) and reason
    )

    if status is TriageStatus.EMERGENCY:
        return SafetyGateDecision(
            status=status,
            action=SafetyAction.EMERGENCY_ASSESSMENT,
            requires_human_review=True,
            red_flag_tags=red_flag_tags,
            reasons=reasons,
        )
    if status is TriageStatus.INSUFFICIENT_INFORMATION:
        return SafetyGateDecision(
            status=status,
            action=SafetyAction.CLARIFY_AND_REVIEW,
            requires_human_review=True,
            red_flag_tags=red_flag_tags,
            reasons=reasons,
        )
    return SafetyGateDecision(
        status=status,
        action=SafetyAction.CONTINUE_ASSISTIVE_PATH,
        requires_human_review=False,
        red_flag_tags=red_flag_tags,
        reasons=reasons,
    )
