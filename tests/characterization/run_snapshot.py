"""Generate a stable, privacy-safe snapshot of canonical medical helpers and APIs."""

from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
CASES_PATH = Path(__file__).with_name("cases.json")
OUTPUT_PATH = Path(__file__).with_name("canonical_snapshot.json")
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import app


def _triage_snapshot(condition: str, scenario: str) -> dict:
    normalized, replacements = app.normalize_patient_expression(condition)
    triage = app.analyze_medical_triage(condition, scenario)
    return {
        "normalized_condition": normalized,
        "colloquial_replacements": replacements,
        "department": app.match_department(condition),
        "triage": {
            "level": triage.get("level"),
            "label": triage.get("label"),
            "severity_bucket": triage.get("severity_bucket"),
            "severity_score": triage.get("severity_score"),
            "recommended_scenario": triage.get("recommended_scenario"),
            "matched_department": triage.get("matched_department"),
            "red_flag_tags": triage.get("red_flag_tags", []),
            "has_disclaimer": bool(triage.get("disclaimer")),
            "followup_count": len((triage.get("followup") or {}).get("questions", [])),
        },
    }


def _route_snapshot(client, path: str, payload: dict) -> dict:
    response = client.post(path, json=payload)
    body = response.get_json() or {}
    data = body.get("data") if isinstance(body, dict) else None
    result = {
        "status_code": response.status_code,
        "top_level_keys": sorted(body) if isinstance(body, dict) else [],
    }
    if isinstance(data, dict):
        result["data_keys"] = sorted(data)
        triage = data.get("triage")
        if isinstance(triage, dict):
            result["triage_level"] = triage.get("level")
    if isinstance(body, dict) and isinstance(body.get("error"), dict):
        result["error_code"] = body["error"].get("code")
    return result


def build_snapshot() -> dict:
    cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))["cases"]
    pure = []
    for case in cases:
        pure.append({"id": case["id"], **_triage_snapshot(case["input"]["condition"], case["input"].get("scenario", "common"))})
    client = app.app.test_client()
    routes = {
        "triage": _route_snapshot(client, "/api/v1/triage", {"condition": "突发胸痛伴呼吸困难"}),
        "recommend": _route_snapshot(client, "/api/v1/recommendations", {"condition": "皮肤瘙痒", "district": "天宁区"}),
        "recommend_invalid": _route_snapshot(client, "/api/v1/recommendations", {}),
    }
    return {
        "schema_version": "canonical-characterization/v2",
        "purpose": "稳定字段快照，仅用于重构回归；不代表医学真值或模型准确率。",
        "pure_functions": pure,
        "routes": routes,
    }


def main(output_path: Path = OUTPUT_PATH) -> int:
    output_path.write_text(json.dumps(build_snapshot(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
