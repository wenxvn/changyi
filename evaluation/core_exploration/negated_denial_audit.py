"""Negated denial risk-cue contract; no clinical diagnosis or new threshold."""
CASES = (
    ("我不否认有胸痛且气短", "EMERGENCY", False),
    ("我不否认呼吸困难", "EMERGENCY", False),
    ("我不否认咳嗽", "ROUTINE", False),
    ("我否认咳嗽", "ROUTINE", False),
    ("我不否认持续抽搐", "EMERGENCY", False),
    ("我否认持续抽搐", "ROUTINE", False),
    ("我不否认有咳嗽但没有胸痛", "ROUTINE", False),
    ("我不否认呼吸困难但不确定是否咳嗽", "EMERGENCY", False),
    ("我不否认糖尿病", "URGENT", False),
)


def run():
    import app
    rows = []
    for text, status, accepted in CASES:
        prediction = app.predict_disease_name(text, details=True)
        data = app.app.test_client().post("/api/v1/triage", json={"condition": text}).get_json()["data"]
        passed = data["triage_status"] == status and prediction["abstained"] is (not accepted)
        assertions = prediction.get("input_assertions", {})
        if "不否认" in text and "咳嗽" in text:
            passed = passed and "cough" in assertions.get("unknown", [])
        if "糖尿病" in text:
            known = data["htriage_analysis"]["known_disease"]
            passed = passed and known["has_known_disease"] is False
        if status == "EMERGENCY":
            passed = passed and not data["disease_prediction"].get("predictions")
        rows.append({"text": text, "expected_status": status, "triage_status": data["triage_status"],
                     "matched_department": data["matched_department"], "assertions": assertions,
                     "known_disease": data["htriage_analysis"]["known_disease"], "pass": passed})
    return {"scope": "synthetic_negated_denial_risk_cue_contract_not_clinical_sensitivity",
            "total": len(rows), "failed": sum(not row["pass"] for row in rows), "rows": rows}
