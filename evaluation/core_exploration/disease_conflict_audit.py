"""Synthetic conflicting-report audit, never a clinical diagnosis decision."""
import argparse
import json
from pathlib import Path

CASES = [
    ("conflict", "有糖尿病，但现在否认糖尿病", False),
    ("conflict", "已确诊糖尿病，但糖尿病不确定", False),
    ("retracted", "以前被误诊糖尿病，现在确认没有糖尿病", False),
    ("history", "有糖尿病病史，现在没有发热", True),
    ("reported", "已确诊糖尿病，来复诊", True),
    ("different", "否认乙肝但确诊糖尿病", True),
    ("subject_open", "我妈妈确诊糖尿病，现在我咳嗽", False),
]


def run():
    import app
    rows = []
    for family, text, expected in CASES:
        known = app.detect_known_disease(text)
        rows.append({"family": family, "text": text, "expected_known": expected, "actual": known, "pass": known["has_known_disease"] == expected})
    return {"scope": "synthetic_report_conflict_not_clinical_validation", "total": len(rows), "failed": sum(not row["pass"] for row in rows), "rows": rows}


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
