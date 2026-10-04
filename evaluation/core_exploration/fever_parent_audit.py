"""Derived parent-feature direction contract, not temperature classification."""
CASES = (
    ("没有高烧但有低烧", ["fever", "mild_fever"], ["high_fever"], [], True),
    ("没有低烧但高烧", ["fever", "high_fever"], ["mild_fever"], [], True),
    ("没有高烧", [], ["high_fever"], [], False),
    ("没有低烧", [], ["mild_fever"], [], False),
    ("高烧不确定", [], [], [], False),
    ("没有发热但高烧", ["fever", "high_fever"], [], ["fever"], False),
    ("没有高烧但有高烧", ["fever", "high_fever"], [], ["high_fever"], False),
    ("高烧", ["fever", "high_fever"], [], [], True),
)


def run():
    import app
    from backend.app.domain.symptom_assertions import parse_asserted_symptoms
    runtime = app.SYMPTOM_DISEASE_MODEL_ADAPTER._load_runtime()
    rows = []
    for text, present, absent, contradiction, accepted in CASES:
        parsed = parse_asserted_symptoms(text, runtime["symptom_alias_map"], runtime["model"]["vocabulary"])
        prediction = app.predict_disease_name(text, details=True)
        data = app.app.test_client().post("/api/v1/triage", json={"condition": text}).get_json()["data"]
        actual = {key: parsed[key] for key in ("present", "absent", "unknown", "contradiction")}
        passed = actual["present"] == present and actual["absent"] == absent and actual["contradiction"] == contradiction
        if text == "高烧不确定":
            passed = passed and actual["unknown"] == ["high_fever"]
        passed = passed and prediction.get("abstained") is (not accepted)
        if accepted:
            passed = passed and prediction["input_coverage"]["model_feature_count"] == 1
        if text == "没有高烧但有低烧":
            passed = passed and data["matched_department"] == "全科医学科"
        rows.append({"text": text, "expected_present": present, "expected_absent": absent,
                     "expected_contradiction": contradiction, "expected_accepted": accepted, "actual": actual,
                     "abstain_reason": prediction.get("abstain_reason"), "normalized_symptoms": prediction.get("normalized_symptoms"),
                     "triage_status": data["triage_status"], "matched_department": data["matched_department"], "pass": passed})
    return {"scope": "synthetic_derived_parent_feature_logic_not_medical_temperature_validation",
            "protocol_version": "fever_parent_direction_and_model_boundary_v2",
            "total": len(rows), "failed": sum(not row["pass"] for row in rows), "rows": rows}
