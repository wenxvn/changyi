"""Unresolved risk answer can be clarified, not clinical risk calibration."""
CASES = (("咳嗽", "unknown", True), ("没有严重胸痛", "unknown", True),
         ("咳嗽", "none", False), ("咳嗽", "present", False),
         ("持续胸痛喘不上气", "unknown", False))


def run():
    import app
    rows = []
    for text, answer, needed in CASES:
        body = {"condition": text, "followup_answers": [{"question_id": "red_flag_check", "value": answer}]}
        data = app.app.test_client().post("/api/v1/triage", json=body).get_json()["data"]
        questions = data["triage"]["followup"]["questions"]
        ids = [question["id"] for question in questions]
        passed = data["original_condition"] == text
        passed = passed and ((bool(ids) and ids[0] == "red_flag_check") if needed else "red_flag_check" not in ids)
        if needed:
            passed = passed and data["triage_status"] == "INSUFFICIENT_INFORMATION" and data["matched_department"] is None
        if answer == "present" or "持续胸痛" in text:
            passed = passed and data["triage_status"] == "EMERGENCY"
        rows.append({"text": text, "answer": answer, "expected_reconfirmation": needed,
                     "question_ids": ids, "triage_status": data["triage_status"],
                     "matched_department": data["matched_department"], "pass": bool(passed)})
    return {"scope": "synthetic_unresolved_risk_reconfirmation_not_clinical_validation",
            "total": len(rows), "failed": sum(not row["pass"] for row in rows), "rows": rows}
