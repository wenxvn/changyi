"""Synthetic type audit: directory/context terms cannot be disease facts."""
import argparse
import json
from pathlib import Path

TOPICS = ("中医", "针灸", "推拿", "产科", "产检", "分娩", "产后")


def run():
    import app
    rows = []
    for topic in TOPICS:
        data = app.app.test_client().post("/api/v1/triage", json={"condition": topic}).get_json()["data"]
        analysis = data["htriage_analysis"]
        known = analysis["known_disease"]
        invented = any(item["name"] == topic for item in analysis["disease_candidates"])
        rows.append({"text": topic, "known": known, "direction": data["matched_department"], "expected_direction": app.DISEASE_DEPT_MAP[topic], "status": data["triage_status"], "invented_candidate": invented, "pass": not known["has_known_disease"] and not invented and data["matched_department"] == app.DISEASE_DEPT_MAP[topic]})
    return {"scope": "synthetic_entity_type_contract_not_clinical_validation", "total": len(rows), "failed": sum(not row["pass"] for row in rows), "rows": rows}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit("Refusing to overwrite evidence")
    result = run()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"total={result['total']} failed={result['failed']}")
