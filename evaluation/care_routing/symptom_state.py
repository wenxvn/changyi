"""Three-state symptom representation: present / absent / unknown.

Offline-only. Never wired into production Safety Gate. Negative parsing is
conservative: only explicit Chinese denial patterns mark a symptom absent.
Unknown is represented by omitting the symptom from features entirely.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable, Mapping, Sequence


class SymptomState(str, Enum):
    PRESENT = "present"
    ABSENT = "absent"
    UNKNOWN = "unknown"


# Conservative denial patterns. Ordered so longer/more specific patterns are
# tried first. These never feed production red-flag Safety rules.
DENIAL_PATTERNS: tuple[str, ...] = (
    "没有明显",
    "没有明显有",
    "不存在",
    "未出现",
    "未见",
    "不伴有",
    "不伴",
    "没有",
    "无明显",
    "无",
    "否认",
    "不觉得有",
    "不是",
)

# Words that make a nearby symptom phrase uncertain rather than present/absent.
UNCERTAIN_PATTERNS: tuple[str, ...] = (
    "不知道",
    "不确定",
    "说不清",
    "可能有",
    "也许有",
    "好像有",
    "是否",
    "有没有",
)


@dataclass(frozen=True)
class SymptomObservation:
    code: str
    state: SymptomState
    evidence: str = ""


@dataclass
class SymptomStateMap:
    """Explicit tri-state map. Unknown symptoms are simply absent from the dict."""

    states: dict[str, SymptomObservation] = field(default_factory=dict)

    def set(self, code: str, state: SymptomState, evidence: str = "") -> None:
        if state is SymptomState.UNKNOWN:
            self.states.pop(code, None)
            return
        self.states[code] = SymptomObservation(code=code, state=state, evidence=evidence)

    def get(self, code: str) -> SymptomState:
        observation = self.states.get(code)
        return observation.state if observation else SymptomState.UNKNOWN

    def present_codes(self) -> list[str]:
        return sorted(code for code, obs in self.states.items() if obs.state is SymptomState.PRESENT)

    def absent_codes(self) -> list[str]:
        return sorted(code for code, obs in self.states.items() if obs.state is SymptomState.ABSENT)

    def as_features(self) -> dict[str, float]:
        """Binary bag features: ``code__present`` / ``code__absent``. Unknown omitted."""

        features: dict[str, float] = {}
        for code, obs in self.states.items():
            if obs.state is SymptomState.PRESENT:
                features[f"{code}__present"] = 1.0
            elif obs.state is SymptomState.ABSENT:
                features[f"{code}__absent"] = 1.0
        return features

    def as_present_set(self) -> set[str]:
        return set(self.present_codes())

    def as_absent_set(self) -> set[str]:
        return set(self.absent_codes())

    def merge(self, other: "SymptomStateMap") -> None:
        for code, obs in other.states.items():
            self.set(code, obs.state, obs.evidence)


def _find_denial_span(text: str, symptom_label: str) -> tuple[bool, str]:
    """Return (is_absent, matched_pattern) if a denial applies to this label."""

    index = text.find(symptom_label)
    if index < 0:
        return False, ""
    # Look at a small left context window (up to 8 chars) for denial cues.
    left = text[max(0, index - 8) : index]
    for pattern in DENIAL_PATTERNS:
        if left.endswith(pattern) or pattern in left:
            # Require the denial to be adjacent-ish (last 4 chars) to stay conservative.
            if pattern in left[-4:] or left.endswith(pattern):
                return True, pattern
    return False, ""


def _is_uncertain_context(text: str, symptom_label: str) -> bool:
    index = text.find(symptom_label)
    if index < 0:
        return False
    left = text[max(0, index - 6) : index]
    right = text[index + len(symptom_label) : index + len(symptom_label) + 6]
    window = left + symptom_label + right
    return any(pattern in window for pattern in UNCERTAIN_PATTERNS)


def parse_symptom_states_from_text(
    text: str,
    alias_map: Mapping[str, str],
    *,
    known_labels: Mapping[str, str] | None = None,
) -> SymptomStateMap:
    """Parse Chinese free text into tri-state symptom observations.

    ``alias_map`` maps colloquial alias -> standard code (e.g. 胸痛 -> chest_pain).
    ``known_labels`` optionally maps code -> Chinese display label for denial lookup.
    Conservative rules:
      - explicit denial adjacent to a symptom marks it absent
      - uncertainty phrases mark unknown (no feature)
      - otherwise a matched alias marks present
      - a code that appears both denied and present keeps PRESENT (safer for triage)
    """

    raw = "".join((text or "").split())
    result = SymptomStateMap()
    if not raw:
        return result

    # Track per-code evidence so present wins over a single denial mention.
    present_hits: dict[str, str] = {}
    absent_hits: dict[str, str] = {}
    uncertain_hits: dict[str, str] = {}

    # Prefer longer aliases first so "没有明显胸痛" matches "胸痛" after denial check.
    aliases = sorted(alias_map.items(), key=lambda item: len(item[0]), reverse=True)
    for alias, code in aliases:
        if not alias or alias not in raw:
            continue
        if _is_uncertain_context(raw, alias):
            uncertain_hits.setdefault(code, alias)
            continue
        denied, pattern = _find_denial_span(raw, alias)
        if denied:
            absent_hits.setdefault(code, f"{pattern}{alias}")
        else:
            present_hits.setdefault(code, alias)

    for code, evidence in present_hits.items():
        result.set(code, SymptomState.PRESENT, evidence)
    for code, evidence in absent_hits.items():
        # Present wins: if any positive mention exists, do not mark absent.
        if code not in present_hits:
            result.set(code, SymptomState.ABSENT, evidence)
    for code in uncertain_hits:
        if code not in present_hits and code not in absent_hits:
            result.set(code, SymptomState.UNKNOWN, uncertain_hits[code])
    return result


def features_from_present_absent(
    present: Iterable[str],
    absent: Iterable[str],
) -> dict[str, float]:
    features: dict[str, float] = {}
    for code in present:
        features[f"{code}__present"] = 1.0
    for code in absent:
        # Never encode a code as both present and absent.
        if f"{code}__present" not in features:
            features[f"{code}__absent"] = 1.0
    return features


def binary_symptom_likelihood(
    *,
    present_codes: Sequence[str],
    absent_codes: Sequence[str],
    disease: str,
    symptom_counts: Mapping[str, Mapping[str, int]],
    total_symptom_counts: Mapping[str, int],
    vocabulary: Sequence[str],
    alpha: float = 1.0,
) -> float:
    """P(features | disease) under NB with explicit absent handling.

    Present: standard Laplace count.
    Absent: complement likelihood (1 - P(symptom|disease)), so "no fever"
    down-weights diseases that almost always have fever.
    Unknown: omitted (no contribution).
    """

    vocab_size = max(len(vocabulary), 1)
    denom = float(total_symptom_counts.get(disease, 0)) + alpha * vocab_size
    counts = symptom_counts.get(disease, {})
    log_likelihood = 0.0
    for code in present_codes:
        count = float(counts.get(code, 0))
        log_likelihood += _log((count + alpha) / denom)
    for code in absent_codes:
        count = float(counts.get(code, 0))
        p_present = (count + alpha) / denom
        # Guard: probability must stay in (0, 1).
        p_present = min(max(p_present, 1e-12), 1.0 - 1e-12)
        log_likelihood += _log(1.0 - p_present)
    return log_likelihood


def _log(value: float) -> float:
    import math

    return math.log(max(value, 1e-12))
