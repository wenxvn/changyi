"""Repeated-mention uncertainty retention, not clinical assertion accuracy."""
CASES = (
    ("有咳嗽但不确定是否咳嗽", ["cough"], False, "symptom_assertion_uncertain"),
    ("不确定是否咳嗽但我咳嗽", ["cough"], False, "symptom_assertion_uncertain"),
    ("没有咳嗽但不确定是否咳嗽", ["cough"], False, "symptom_assertion_uncertain"),
    ("咳嗽和咳嗽不确定", ["cough"], False, "symptom_assertion_uncertain"),
    ("不确定是否咳嗽但有头痛", [], False, "symptom_assertion_uncertain"),
    ("有咳嗽而且咳嗽", [], True, None),
    ("有咳嗽但以前也咳嗽", ["cough"], False, "noncurrent_symptom_context"),
    ("持续胸痛喘不上气，有咳嗽但不确定是否咳嗽", ["cough"], False, "symptom_assertion_uncertain"),
)


def run():
    import app
    rows = []
    for text, overlap, accepted, reason in CASES:
        prediction = app.predict_disease_name(text, details=True)
        assertions = prediction["input_assertions"]
        data = app.app.test_client().post("/api/v1/triage", json={"condition": text}).get_json()["data"]
        passed = assertions.get("uncertainty_conflicts", []) == overlap and prediction["abstained"] is (not accepted)
        passed = passed and prediction.get("abstain_reason") == reason
        if "持续胸痛" in text:
            passed = passed and data["triage_status"] == "EMERGENCY" and not data["disease_prediction"].get("predictions")
        rows.append({"text": text, "expected_overlap": overlap, "expected_accepted": accepted,
                     "assertions": assertions, "abstained": prediction["abstained"], "abstain_reason": prediction.get("abstain_reason"),
                     "triage_status": data["triage_status"], "matched_department": data["matched_department"], "pass": passed})
    return {"scope": "synthetic_uncertainty_overlap_contract_not_clinical_validation",
            "total": len(rows), "failed": sum(not row["pass"] for row in rows), "rows": rows}
