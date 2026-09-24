"""Capture three golden E2E demo cases through the official v1 API.

Writes behavior boundaries (status / abstain / strategy), not brittle scores.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import app as application_entry

OUT = Path(__file__).resolve().parent


def capture() -> dict:
    client = application_entry.app.test_client()

    def triage(payload: dict) -> dict:
        return client.post("/api/v1/triage", json=payload).get_json()["data"]

    def rec(payload: dict) -> dict:
        return client.post("/api/v1/recommendations", json=payload).get_json()["data"]

    ordinary = triage({"condition": "咳嗽三天，有点低烧，没有胸痛"})
    ordinary_rec = rec({"condition": "咳嗽三天，有点低烧，没有胸痛", "location_source": "unknown"})

    vague = triage({"condition": "不舒服"})
    followups = client.post("/api/v1/triage/followups", json={"condition": "不舒服"}).get_json()["data"]
    answered = triage({
        "condition": "不舒服",
        "followup_answers": [
            {"question_id": "duration", "value": "lt_1_week"},
            {"question_id": "red_flag_check", "value": "none"},
        ],
    })

    emergency = triage({"condition": "持续胸痛，喘不上气，出冷汗"})
    emergency_rec = rec({"condition": "持续胸痛，喘不上气", "location_source": "unknown"})
    map_items = client.get("/api/v1/map").get_json()["data"].get("items") or []

    return {
        "schema_version": "golden-e2e/v1",
        "claim_scope": "behavior boundaries, not brittle scores",
        "cases": {
            "ordinary_clear_path": {
                "observed": {
                    "triage_status": ordinary["triage_status"],
                    "matched_department": ordinary["matched_department"],
                    "hospitals": len(ordinary_rec.get("recommended_hospitals") or []),
                    "doctors": len(ordinary_rec.get("recommended_doctors") or []),
                    "resource_strategy": (ordinary_rec.get("resource_strategy") or {}).get("code"),
                },
                "pass": ordinary["triage_status"] in ("ROUTINE", "URGENT")
                and bool(ordinary_rec.get("recommended_hospitals"))
                and bool(ordinary_rec.get("recommended_doctors")),
            },
            "vague_insufficient_followup_reroute": {
                "observed": {
                    "triage_status": vague["triage_status"],
                    "disease_abstained": vague["disease_prediction"].get("abstained"),
                    "followup_questions": len(((followups.get("followup") or {}).get("questions") or [])),
                    "condition_unchanged_after_answers": answered["condition"] == "不舒服",
                    "original_condition": answered.get("original_condition"),
                },
                "pass": vague["triage_status"] == "INSUFFICIENT_INFORMATION"
                and bool(vague["disease_prediction"].get("abstained"))
                and answered["condition"] == "不舒服",
            },
            "emergency_short_circuit_safety_exit": {
                "observed": {
                    "triage_status": emergency["triage_status"],
                    "disease_abstained": emergency["disease_prediction"].get("abstained"),
                    "resource_strategy": (emergency_rec.get("resource_strategy") or {}).get("code"),
                    "map_emergency_items": sum(1 for item in map_items if item.get("emergency")),
                },
                "pass": emergency["triage_status"] == "EMERGENCY"
                and bool(emergency["disease_prediction"].get("abstained"))
                and (emergency_rec.get("resource_strategy") or {}).get("code") == "emergency_fast_track",
            },
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    payload = capture()
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if args.write:
        (OUT / "golden_e2e.json").write_text(text, encoding="utf-8")
        print(f"wrote {OUT / 'golden_e2e.json'}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
