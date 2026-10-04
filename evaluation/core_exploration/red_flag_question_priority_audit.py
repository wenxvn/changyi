"""Unanswered risk-question retention, not medical severity validation."""
CASES = (("没有严重胸痛", None, True), ("咳嗽", None, True),
         ("已确诊糖尿病", None, True), ("咳嗽", "none", False),
         ("持续胸痛喘不上气", None, False))


def run():
    import app
    rows = []
    for text, answer, expected in CASES:
        body = {"condition": text}
        if answer:
            body["followup_answers"] = [{"question_id": "red_flag_check", "value": answer}]
        data = app.app.test_client().post("/api/v1/triage", json=body).get_json()["data"]
        questions = data["triage"]["followup"]["questions"]
        ids = [question["id"] for question in questions]
        passed = len(questions) <= 8 and ((bool(ids) and ids[0] == "red_flag_check") if expected else "red_flag_check" not in ids)
        rows.append({"text": text, "answer": answer, "expected_priority": expected, "question_ids": ids,
                     "triage_status": data["triage_status"], "matched_department": data["matched_department"], "pass": bool(passed)})
    return {"scope": "synthetic_risk_question_priority_contract_not_clinical_validation",
            "total": len(rows), "failed": sum(not row["pass"] for row in rows), "rows": rows}
