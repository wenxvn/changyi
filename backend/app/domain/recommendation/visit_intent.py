"""Visit-intent contract for resource routing only.

Visit intent never feeds Safety Gate rules, never lowers triage level, and
never bypasses emergency publication. It only selects ranking weight profiles
after triage has already been decided.
"""

from __future__ import annotations


VISIT_INTENT_OPTIONS = (
    "first_visit",
    "follow_up",
    "review_results",
    "procedure_consult",
    "unsure",
)

VISIT_INTENT_LABELS = {
    "first_visit": "首次就诊",
    "follow_up": "已有诊断，需要复诊",
    "review_results": "已有检查，希望进一步就医",
    "procedure_consult": "手术 / 专科治疗咨询",
    "unsure": "不确定",
}

# Ranking scenario used for resource routing only.
# procedure_consult is a distinct elective/specialty-planning profile and must
# not inherit emergency surgery semantics (urgent access, emergency fallback).
VISIT_INTENT_TO_RANKING_SCENARIO = {
    "first_visit": "first_visit",
    "follow_up": "complex",
    "review_results": "complex",
    "procedure_consult": "procedure_consult",
    "unsure": "common",
}


def ranking_scenario_for_visit_intent(visit_intent: str | None, default_scenario: str) -> str:
    """Map a user visit intent to a ranking scenario without touching triage."""

    if not visit_intent:
        return default_scenario
    return VISIT_INTENT_TO_RANKING_SCENARIO.get(visit_intent, default_scenario)
