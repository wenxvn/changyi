"""Pure candidate filtering helpers for recommendation pipelines."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .scoring import as_text, departments_related


def build_doctor_query_terms(
    condition: str,
    disease_department_map: Mapping[str, str],
    htriage: Mapping[str, Any] | None,
) -> set[str]:
    """Build the legacy doctor query-term set from explicit inputs."""

    query_words: set[str] = set()
    for word in condition.replace("，", ",").replace("、", ",").split(","):
        query_words.add(word.strip())
    for symptom in disease_department_map:
        if symptom in condition:
            query_words.add(symptom)
    for item in (htriage or {}).get("symptom_tags", []):
        query_words.add(item.get("tag", ""))
        for term in item.get("matched_terms", []):
            query_words.add(term)
    for item in (htriage or {}).get("disease_candidates", []):
        query_words.add(item.get("name", ""))
        query_words.add(item.get("primary_category", ""))
        query_words.add(item.get("secondary_category", ""))
    return query_words


def doctor_matches_candidate(
    doctor: Mapping[str, Any],
    target_dept: str | None,
    query_words: set[str],
) -> bool:
    """Return whether one doctor passes the existing candidate filter."""

    if target_dept:
        return departments_related(target_dept, doctor["department"])
    keyword_text = as_text(doctor.get("keywords", [])) + " " + doctor["department"]
    return any(word in keyword_text for word in query_words)


def resolve_hospital_candidate_match(
    hospital: Mapping[str, Any],
    target_dept: str | None,
) -> tuple[float, str | None]:
    """Resolve the legacy hospital department match and strength fallback."""

    if target_dept and target_dept in hospital.get("strength_scores", {}):
        return hospital["strength_scores"][target_dept], target_dept
    if target_dept and target_dept in hospital.get("departments", []):
        return 75, target_dept

    strength_score = 50
    matched_dept = target_dept
    for department in hospital.get("departments", []):
        if target_dept and departments_related(target_dept, department):
            return 70, department
    return strength_score, matched_dept


def hospital_supports_emergency_fallback(
    hospital: Mapping[str, Any] | None,
) -> bool:
    """Return whether a hospital enters the legacy emergency fallback pool."""

    return bool(hospital and hospital.get("emergency"))
