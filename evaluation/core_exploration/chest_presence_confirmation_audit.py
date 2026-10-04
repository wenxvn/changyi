"""Unknown current presence confirmation, not clinical severity assignment."""
CASES = (
    ("没有严重胸痛", None, "INSUFFICIENT_INFORMATION"),
    ("没有严重胸痛", "none", "ROUTINE"),
    ("没有严重胸痛", "present", "EMERGENCY"),
    ("没有严重胸痛", "unknown", "INSUFFICIENT_INFORMATION"),
    ("我没有严重胸痛但有轻微胸痛", None, "URGENT"),
    ("没有严重胸痛但现在喘不上气", None, "EMERGENCY"),
    ("去年没有严重胸痛，现在咳嗽", None, "ROUTINE"),
)


def run():
    import app
    rows = []
    for text, answer, expected in CASES:
        body = {"condition": text}
        if answer:
            body["followup_answers"] = [{"question_id": "red_flag_check", "value": answer}]
        data = app.app.test_client().post("/api/v1/triage", json=body).get_json()["data"]
        passed = data["triage_status"] == expected and data["original_condition"] == text
        if expected == "INSUFFICIENT_INFORMATION":
            passed = passed and data["matched_department"] is None and data["triage"].get("defer_resource_routing") is True
            questions = data["triage"]["followup"]["questions"]
            passed = passed and bool(questions) and questions[0]["id"] == "red_flag_check"
        if expected in ("INSUFFICIENT_INFORMATION", "EMERGENCY"):
            passed = passed and not data["disease_prediction"].get("predictions")
        rows.append({"text": text, "answer": answer, "expected_status": expected,
                     "triage_status": data["triage_status"], "matched_department": data["matched_department"],
                     "defer_resource_routing": data["triage"].get("defer_resource_routing"), "pass": bool(passed)})
    return {"scope": "synthetic_qualified_chest_presence_confirmation_not_clinical_severity_validation",
            "total": len(rows), "failed": sum(not row["pass"] for row in rows), "rows": rows}
