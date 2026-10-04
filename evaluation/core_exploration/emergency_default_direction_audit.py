"""Emergency fallback presentation policy, preserving existing specific routes."""
CASES = (
    ("我现在是否喘不上气，我喘不上气", None, "EMERGENCY", "急诊医学科"),
    ("不确定症状", "present", "EMERGENCY", "急诊医学科"),
    ("我现在喘不上气", None, "EMERGENCY", "呼吸与危重症医学科"),
    ("我现在是否喘不上气", None, "INSUFFICIENT_INFORMATION", None),
    ("没有咳嗽", None, "ROUTINE", "全科医学科"),
    ("我确诊糖尿病", None, "URGENT", "内分泌代谢科"),
)


def run():
    import app
    from backend.app.domain.triage.safety_gate import triage_status_from_legacy
    rows = []
    client = app.app.test_client()
    for text, answer, status, dept in CASES:
        body = {"condition": text}
        if answer:
            body["followup_answers"] = [{"question_id": "red_flag_check", "value": answer}]
        triage = client.post("/api/v1/triage", json=body).get_json()["data"]
        recommendation = client.post("/api/v1/recommendations", json=body).get_json()["data"]
        passed = triage["triage_status"] == triage_status_from_legacy(recommendation["triage"]).value == status
        passed = passed and triage["matched_department"] == recommendation["matched_department"] == dept
        if status == "EMERGENCY":
            passed = passed and not recommendation["recommended_doctors"] and bool(recommendation["recommended_hospitals"])
        rows.append({"text": text, "answer": answer, "expected_status": status, "expected_direction": dept,
                     "status": triage["triage_status"], "triage_department": triage["matched_department"],
                     "recommendation_department": recommendation["matched_department"],
                     "clinical_label_verified": False, "pass": bool(passed)})
    return {"scope": "emergency_default_direction_policy_not_clinical_department_validation",
            "total": len(rows), "failed": sum(not r["pass"] for r in rows), "rows": rows}
