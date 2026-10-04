"""Current-time word scope contract, not clinical temporality inference."""
CASES = (
    ("不确定是否现在咳嗽", [], ["cough"], False),
    ("假如现在咳嗽", [], ["cough"], False),
    ("不确定是否 现在 咳嗽", [], ["cough"], False),
    ("不确定是否现在有胸痛", [], ["chest_pain"], False),
    ("不确定是否咳嗽但现在头痛", ["headache"], ["cough"], False),
    ("不确定是否有咳嗽现在有头痛", ["headache"], ["cough"], False),
    ("不确定为什么现在咳嗽", ["cough"], [], True),
    ("持续胸痛喘不上气，不确定是否现在咳嗽", None, ["cough"], False),
)


def run():
    import app
    rows = []
    for text, present, unknown, accepted in CASES:
        prediction = app.predict_disease_name(text, details=True)
        assertions = prediction["input_assertions"]
        data = app.app.test_client().post("/api/v1/triage", json={"condition": text}).get_json()["data"]
        passed = assertions["unknown"] == unknown and prediction["abstained"] is (not accepted)
        if present is not None:
            passed = passed and assertions["present"] == present
        if "持续胸痛" in text:
            passed = passed and data["triage_status"] == "EMERGENCY" and not data["disease_prediction"].get("predictions")
        rows.append({"text": text, "expected_present": present, "expected_unknown": unknown, "expected_accepted": accepted,
                     "assertions": assertions, "abstain_reason": prediction.get("abstain_reason"),
                     "triage_status": data["triage_status"], "matched_department": data["matched_department"], "pass": passed})
    return {"scope": "synthetic_current_word_uncertainty_scope_not_clinical_time_reasoning",
            "total": len(rows), "failed": sum(not row["pass"] for row in rows), "rows": rows}
