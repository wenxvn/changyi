"""Pure helpers shared by hospital and doctor recommendation scoring.

The helpers intentionally do not know about Flask, Region repositories,
models, or the current data store.  They preserve the legacy calculations
while making the first candidate/feature/score boundary independently testable.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def as_text(value: Any) -> str:
    if not value:
        return ""
    if isinstance(value, (list, tuple, set)):
        return " ".join(str(item) for item in value if item)
    return str(value)


def rebalance_weights(weights: Mapping[str, float], unavailable: set[str]) -> dict[str, float]:
    """Remove unavailable features and normalize the remaining weights."""

    available = {key: float(value) for key, value in weights.items() if key not in unavailable}
    total = sum(available.values())
    if total <= 0:
        return {key: 0.0 for key in weights}
    return {
        key: round((available.get(key, 0.0) / total) if key in available else 0.0, 6)
        for key in weights
    }


def doctor_title_score(doc: dict[str, Any]) -> float:
    title = doc.get("title", "") or ""
    if "主任医师" in title and "副主任" not in title:
        return 1.0
    if "副主任医师" in title:
        return 0.72
    if "主治医师" in title:
        return 0.42
    return 0.25


def doctor_resource_tier(
    doc: dict[str, Any],
    hospital: dict[str, Any] | None,
    specialty_score: float,
    academic_score: float,
    surgery_score: float,
) -> str:
    """Return an internal resource tier, not a public doctor grade.

    Academic output (SCI, funding, patents) stays available as profile
    metadata, but must not define clinical expert tiers: research volume is
    not a proxy for patient-care fit.
    """

    hospital_text = (hospital or {}).get("level", "")
    title_score = doctor_title_score(doc)
    strong_platform = "三级甲等" in hospital_text or "三甲" in hospital_text
    high_clinical = surgery_score >= 0.62 or (doc.get("surgery_count") or 0) >= 800
    strong_specialty = specialty_score >= 0.85
    if strong_platform and specialty_score >= 0.78 and title_score >= 0.72 and (high_clinical or strong_specialty):
        return "top_expert"
    if specialty_score >= 0.72 and (title_score >= 0.72 or high_clinical or strong_specialty):
        return "expert"
    if specialty_score >= 0.58 or title_score >= 0.42:
        return "specialist"
    return "general"


def departments_related(target_dept: str | None, doc_dept: str | None) -> bool:
    if not target_dept or not doc_dept:
        return False
    if target_dept == doc_dept or target_dept in doc_dept or doc_dept in target_dept:
        return True
    families = [
        ("肿瘤",),
        ("消化", "脾胃", "胃肠"),
        ("呼吸", "肺"),
        ("心血管", "心脏"),
        ("神经", "脑"),
        ("骨", "脊柱", "关节"),
        ("妇", "产", "生殖"),
        ("儿", "儿童", "新生儿"),
        ("肾", "泌尿"),
        ("中医", "针灸", "推拿", "康复"),
    ]
    for family in families:
        if any(token in target_dept for token in family) and any(token in doc_dept for token in family):
            return True
    return False


def score_hospital_candidate(
    *,
    clinical: float,
    availability: float,
    accessibility: float,
    continuity: float,
    quality: float,
    fairness: float,
    emergency: float,
    risk_penalty: float,
    weights: Mapping[str, float],
    traffic_access: Mapping[str, Any],
) -> tuple[float, dict[str, Any]]:
    """Combine prepared hospital features using the existing legacy formula."""

    raw_score = (
        weights["clinical"] * clinical
        + weights["availability"] * availability
        + weights["accessibility"] * accessibility
        + weights["continuity"] * continuity
        + weights["quality"] * quality
        + weights["fairness"] * fairness
        + weights["emergency"] * emergency
        - risk_penalty
    )
    composite = round(clamp(raw_score) * 100, 1)
    feature_scores = {
        "clinical": round(clinical, 4),
        "availability": round(availability, 4),
        "accessibility": round(accessibility, 4),
        "continuity": round(continuity, 4),
        "quality": round(quality, 4),
        "fairness": round(fairness, 4),
        "emergency": round(emergency, 4),
        "risk_penalty": round(risk_penalty, 4),
        "traffic_access": traffic_access,
    }
    return composite, feature_scores


def score_doctor_candidate(
    *,
    surgery_score: float,
    specialty_score: float,
    academic_score: float,
    title_score: float,
    hospital_score: float,
    access_score: float,
    availability_score: float,
    continuity_score: float,
    fairness_score: float,
    risk_penalty: float,
    weights: Mapping[str, float],
    extra_weights: Mapping[str, float],
) -> float:
    """Combine prepared doctor features using the existing legacy formula."""

    base_score = (
        weights["surgery"] * surgery_score
        + weights["specialty"] * specialty_score
        + weights["academic"] * academic_score
        + weights["title"] * title_score
        + weights["hospital"] * hospital_score
        + weights.get("access", 0.0) * access_score
    )
    total_score = (
        base_score * (1 - sum(extra_weights.values()))
        + extra_weights.get("availability", 0.0) * availability_score
        + extra_weights.get("continuity", 0.0) * continuity_score
        + extra_weights.get("fairness", 0.0) * fairness_score
        - risk_penalty
    )
    if specialty_score > 0.5:
        total_score *= 1.08
    return clamp(total_score)
