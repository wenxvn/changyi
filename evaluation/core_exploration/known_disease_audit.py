"""Synthetic known-disease input audit; not a clinical routing label set."""
import argparse
import json
from pathlib import Path

CASES = [
    ("denied", "没有糖尿病，只是咳嗽", False, ""),
    ("denied", "否认乙肝，有皮疹", False, ""),
    ("denied", "没有类风湿关节炎但有咳嗽", False, ""),
    ("contrast", "没有糖尿病但确诊乙肝", True, "乙肝"),
    ("positive", "已经确诊糖尿病，来复诊", True, "糖尿病"),
    ("history", "有糖尿病病史，来复诊", True, "糖尿病"),
    ("uncertain", "不确定是否糖尿病", False, ""),
    ("uncertain", "糖尿病不确定", False, ""),
]


def run():
    import app
    rows = []
    for family, text, expected, disease in CASES:
        data = app.app.test_client().post("/api/v1/triage", json={"condition": text}).get_json()["data"]
        known = data["htriage_analysis"]["known_disease"]
        rows.append({"family": family, "text": text, "expected_known": expected, "expected_disease": disease, "actual_known": known, "direction": data["matched_department"], "status": data["triage_status"], "pass": known["has_known_disease"] == expected and (not expected or known["disease"] == disease)})
    return {"scope": "synthetic_known_disease_contract_audit_not_clinical_accuracy", "total": len(rows), "failed": sum(not row["pass"] for row in rows), "rows": rows}


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
