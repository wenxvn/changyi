"""Evaluate frozen anonymous vignette labels at the serving API, without fitting.

Dataset provenance is supplied by the curator, not certified by this evaluator.
Neither engineering fixtures nor published expert vignettes prove clinical safety.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path

STATUSES = {"ROUTINE", "URGENT", "EMERGENCY", "INSUFFICIENT_INFORMATION"}


def validate_dataset(dataset):
    if not isinstance(dataset, dict) or set(dataset) != {"schema_version", "provenance", "cases"}:
        raise ValueError("Expected schema_version, provenance and cases only")
    if dataset["schema_version"] != "independent-core-validation/v1":
        raise ValueError("Unsupported validation schema")
    p = dataset["provenance"]
    keys = {"source_url", "license", "origin", "label_origin", "privacy_review", "patient_records", "development_exposure"}
    if not isinstance(p, dict) or set(p) != keys:
        raise ValueError("Incomplete or unexpected provenance fields")
    if p["origin"] not in {"synthetic_engineering", "published_expert_vignettes", "public_general_questions"}:
        raise ValueError("Patient records are outside the project data boundary")
    if p["patient_records"] is not False or p["privacy_review"] != "reviewed_no_identity_or_patient_records":
        raise ValueError("Privacy review is required before evaluating text")
    if not all(isinstance(p[key], str) and p[key].strip() for key in keys - {"patient_records"}):
        raise ValueError("Provenance fields must be nonempty text")
    if p["development_exposure"] not in {"never_used", "used_for_development", "unknown"}:
        raise ValueError("Invalid development exposure")
    cases = dataset["cases"]
    if not isinstance(cases, list) or not cases:
        raise ValueError("An empty set is not validation evidence")
    ids, texts = set(), set()
    for case in cases:
        if not isinstance(case, dict) or set(case) != {"case_id", "condition", "acceptable_departments", "risk_status"}:
            raise ValueError("Unexpected case fields; do not include records or answers")
        if not all(isinstance(case[key], str) and case[key].strip() for key in ("case_id", "condition")):
            raise ValueError("Cases require anonymous id and nonempty input")
        if case["case_id"] in ids or case["condition"].strip() in texts:
            raise ValueError("Duplicate ids or identical inputs inflate the denominator")
        ids.add(case["case_id"]); texts.add(case["condition"].strip())
        depts = case["acceptable_departments"]
        if not isinstance(depts, list) or any(not isinstance(d, str) or not d.strip() for d in depts):
            raise ValueError("Departments must use reviewer-approved serving names")
        if len(depts) != len(set(depts)) or (not depts and case["risk_status"] is None):
            raise ValueError("Every case needs a label; duplicate departments are invalid")
        if case["risk_status"] is not None and (not isinstance(case["risk_status"], str) or case["risk_status"] not in STATUSES):
            raise ValueError("Unknown risk label")
    return dataset


def evaluate(dataset, predict):
    validate_dataset(dataset)
    counts = defaultdict(int)
    per_department = defaultdict(lambda: {"cases": 0, "correct": 0})
    rows = []
    for case in dataset["cases"]:
        counts["total_cases"] += 1
        result = predict(case["condition"])
        valid = (isinstance(result, dict) and isinstance(result.get("triage_status"), str)
                 and result["triage_status"] in STATUSES)
        if not valid:
            counts["api_errors"] += 1
            result = {}
        actual = result.get("triage_status")
        direction = result.get("matched_department")
        routed = valid and actual in {"ROUTINE", "URGENT"} and bool(direction)
        risk = case["risk_status"]
        risk_correct = valid and actual == risk if risk is not None else None
        depts = case["acceptable_departments"]
        dept_correct = routed and direction in depts if depts else None
        if risk is not None:
            counts["risk_labeled_cases"] += 1
            counts["risk_correct"] += bool(risk_correct)
            if risk == "EMERGENCY":
                counts["emergency_labeled_cases"] += 1
                counts["emergency_missed"] += actual != "EMERGENCY"
        if depts:
            counts["department_labeled_cases"] += 1
            counts["department_routed"] += bool(routed)
            counts["department_correct"] += bool(dept_correct)
            for dept in depts:
                per_department[dept]["cases"] += 1
                per_department[dept]["correct"] += bool(routed and direction == dept)
        counts["all_available_labels_correct"] += (risk_correct is not False and dept_correct is not False)
        rows.append({"case_id": case["case_id"], "api_valid": valid,
                     "triage_status": actual, "matched_department": direction,
                     "risk_correct": risk_correct, "department_correct": dept_correct})
    ratio = lambda numerator, denominator: counts[numerator] / counts[denominator] if counts[denominator] else None
    p = dataset["provenance"]
    return {"schema_version": "independent-core-validation-result/v1", "provenance_declarations": p,
            "independence_declared": p["development_exposure"] == "never_used",
            "clinical_validation": False, "scope": p["origin"], "counts": dict(counts),
            "risk_accuracy": ratio("risk_correct", "risk_labeled_cases"),
            "department_accuracy_full_denominator": ratio("department_correct", "department_labeled_cases"),
            "department_coverage": ratio("department_routed", "department_labeled_cases"),
            "department_retained_accuracy": ratio("department_correct", "department_routed"),
            "joint_available_label_accuracy": ratio("all_available_labels_correct", "total_cases"),
            "per_acceptable_department": dict(per_department), "rows": rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    args = parser.parse_args()
    raw = args.dataset.read_bytes()
    dataset = validate_dataset(json.loads(raw))
    # Do not import the serving app or make requests before provenance validation.
    import app
    client = app.app.test_client()
    def predict(text):
        response = client.post("/api/v1/triage", json={"condition": text})
        payload = response.get_json(silent=True)
        return payload.get("data") if response.status_code == 200 and isinstance(payload, dict) else None
    result = evaluate(dataset, predict)
    result["dataset_sha256"] = hashlib.sha256(raw).hexdigest()
    result["serving_versions"] = {key: app.app.config[key] for key in ("TRIAGE_RULES_VERSION", "MODEL_VERSION")}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result["counts"].get("api_errors") else 0


if __name__ == "__main__":
    raise SystemExit(main())
