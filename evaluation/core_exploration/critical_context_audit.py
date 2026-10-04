"""Synthetic caller audit of existing critical cues; not medical ground truth."""
import argparse
import json
from pathlib import Path


def run():
    import app
    client = app.app.test_client()
    rows = []
    families = (
        ("self_current", "我现在{word}", ["EMERGENCY"]),
        ("bystander_current", "我妈妈正在{word}", ["EMERGENCY"]),
        ("denied", "没有{word}，只有咳嗽", ["ROUTINE", "URGENT", "INSUFFICIENT_INFORMATION"]),
        ("history_other_current", "以前{word}，现在我咳嗽", ["ROUTINE", "URGENT", "INSUFFICIENT_INFORMATION"]),
        ("uncertain", "不确定有没有{word}", ["INSUFFICIENT_INFORMATION", "EMERGENCY"]),
    )
    for word in app.TRIAGE_CRITICAL_SINGLE_KEYWORDS:
        for family, template, expected in families:
            text = template.format(word=word)
            response = client.post("/api/v1/triage", json={"condition": text})
            data = response.get_json()["data"]
            rows.append({"cue": word, "family": family, "text": text, "expected_statuses": expected, "actual": data["triage_status"], "matched_rule": data["triage"].get("matched_rule"), "direction": data["matched_department"], "pass": data["triage_status"] in expected})
    summaries = {family: {"total": sum(row["family"] == family for row in rows), "failed": sum(row["family"] == family and not row["pass"] for row in rows)} for family, *_ in families}
    return {"scope": "synthetic_existing_rule_context_audit_not_clinical_accuracy", "total": len(rows), "failed": sum(not row["pass"] for row in rows), "families": summaries, "rows": rows}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit("Refusing to overwrite evidence")
    result = run()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({key: value for key, value in result.items() if key != "rows"}, ensure_ascii=False))
