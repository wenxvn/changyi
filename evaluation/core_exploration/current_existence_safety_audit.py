"""Explicit existence queries vs independent danger reports, policy only."""
CASES = (
    ("我现在是否喘不上气", "INSUFFICIENT_INFORMATION"),
    ("我现在不确定是否呼吸困难", "INSUFFICIENT_INFORMATION"),
    ("我现在有没有意识不清", "INSUFFICIENT_INFORMATION"),
    ("我现在是否胸痛", "INSUFFICIENT_INFORMATION"),
    ("我现在喘不上气", "EMERGENCY"),
    ("我现在是否呼吸困难，我喘不上气", "EMERGENCY"),
    ("我现在是否喘不上气，我喘不上气", "EMERGENCY"),
    ("我现在不确定为什么喘不上气", "EMERGENCY"),
)


def run():
    import app
    rows = []
    client = app.app.test_client()
    for text, expected in CASES:
        data = client.post("/api/v1/triage", json={"condition": text}).get_json()["data"]
        questions = data["triage"].get("followup", {}).get("questions", [])
        passed = data["triage_status"] == expected and data["original_condition"] == text
        if expected == "INSUFFICIENT_INFORMATION":
            passed = passed and data["matched_department"] is None
            passed = passed and any(q["id"] == "red_flag_check" for q in questions)
        rows.append({"text": text, "expected_existing_policy_status": expected,
                     "triage_status": data["triage_status"], "matched_department": data["matched_department"],
                     "public_abstain_reason": data["disease_prediction"].get("abstain_reason"),
                     "risk_confirmation_present": any(q["id"] == "red_flag_check" for q in questions),
                     "clinical_label_verified": False, "pass": bool(passed)})
    return {"scope": "current_existence_question_safety_policy_not_clinical_accuracy",
            "total": len(rows), "failed": sum(not r["pass"] for r in rows),
            "clinical_accuracy": None, "rows": rows}
