"""Local cause-question interpretation contract, not clinical diagnosis."""
CASES = (
    ("不确定为什么咳嗽", ["cough"], [], [], True),
    ("说不清为何咳嗽", ["cough"], [], [], True),
    ("不确定为什么咳嗽但确实咳嗽", ["cough"], [], [], True),
    ("不确定为什么没有咳嗽", [], ["cough"], [], False),
    ("不确定是否咳嗽", [], [], ["cough"], False),
    ("假如不确定为什么咳嗽", [], [], ["cough"], False),
    ("以前不确定为什么咳嗽", [], [], ["cough"], False),
    ("持续胸痛喘不上气，不确定为什么咳嗽", None, [], [], True),
)


def run():
    import app
    rows = []
    for text, present, absent, unknown, accepted in CASES:
        prediction = app.predict_disease_name(text, details=True)
        assertions = prediction["input_assertions"]
        data = app.app.test_client().post("/api/v1/triage", json={"condition": text}).get_json()["data"]
        passed = assertions["absent"] == absent and assertions["unknown"] == unknown and not assertions["uncertainty_conflicts"]
        if present is not None:
            passed = passed and assertions["present"] == present
        passed = passed and prediction["abstained"] is (not accepted)
        if "持续胸痛" in text:
            passed = passed and data["triage_status"] == "EMERGENCY" and not data["disease_prediction"].get("predictions")
        rows.append({"text": text, "expected_present": present, "expected_absent": absent, "expected_unknown": unknown,
                     "expected_accepted": accepted, "assertions": assertions, "abstain_reason": prediction.get("abstain_reason"),
                     "triage_status": data["triage_status"], "matched_department": data["matched_department"], "pass": passed})
    return {"scope": "synthetic_local_cause_vs_presence_uncertainty_not_clinical_validation",
            "total": len(rows), "failed": sum(not row["pass"] for row in rows), "rows": rows}
