"""Pure candidate selection and reranking helpers for recommendations.

The legacy application still owns candidate generation and feature assembly.
This module only applies the existing result ordering and light diversity
constraints to already-scored hospital candidates.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

from .scoring import clamp


def rerank_hospital_candidates(
    results: Sequence[dict[str, Any]],
    triage_level: str,
    top_n: int,
    district_fn: Callable[[dict[str, Any]], str],
) -> list[dict[str, Any]]:
    """Preserve legacy hospital ordering while applying diversity constraints.

    The constraints are intentionally limited to routine and urgent paths.
    Emergency candidates bypass both the district and routine tertiary-count
    adjustments so the safety-first ordering remains intact.
    """

    ranked = sorted(results, key=lambda item: item["composite_score"], reverse=True)
    selected = []
    district_count: dict[str, int] = {}
    tertiary_count = 0

    for item in ranked:
        hospital = item["hospital"]
        adjusted = item["composite_score"]
        district = district_fn(hospital)
        if triage_level in ("routine", "urgent") and district_count.get(district, 0) >= 2:
            adjusted -= 1.5
        if triage_level == "routine" and hospital.get("level") == "三级甲等" and tertiary_count >= 2:
            adjusted -= 2.0
        item["rerank_adjustment"] = round(adjusted - item["composite_score"], 1)
        item["composite_score"] = round(clamp(adjusted / 100.0) * 100, 1)
        selected.append(item)
        district_count[district] = district_count.get(district, 0) + 1
        if hospital.get("level") == "三级甲等":
            tertiary_count += 1
        if len(selected) >= top_n:
            break

    selected.sort(key=lambda item: item["composite_score"], reverse=True)
    return selected
