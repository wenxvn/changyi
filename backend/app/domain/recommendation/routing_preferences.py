"""Resource routing preferences.

These preferences only shape post-safety resource routing. They never feed
Safety Gate rules, never lower triage level, and never bypass emergency.
"""

from __future__ import annotations


DISTRICT_PREFERENCE_OPTIONS = ("prefer_home_district", "allow_cross_district", "any_district")
DISTANCE_PREFERENCE_OPTIONS = ("prefer_nearby", "allow_farther_for_fit", "distance_flexible")
CONTINUITY_PREFERENCE_OPTIONS = ("off", "prefer_favorites")


def normalize_routing_preferences(payload: dict | None) -> dict[str, str | bool]:
    """Return a validated preference dict with safe defaults (all off)."""

    data = payload or {}
    district = str(data.get("district_preference") or "any_district")
    distance = str(data.get("distance_preference") or "distance_flexible")
    continuity = data.get("continuity_preference") is True
    if district not in DISTRICT_PREFERENCE_OPTIONS:
        district = "any_district"
    if distance not in DISTANCE_PREFERENCE_OPTIONS:
        distance = "distance_flexible"
    return {
        "district_preference": district,
        "distance_preference": distance,
        "continuity_preference": continuity,
    }


def preferences_affect_emergency(preferences: dict[str, str | bool]) -> bool:
    """Emergency publication ignores routing preferences entirely."""

    return False
