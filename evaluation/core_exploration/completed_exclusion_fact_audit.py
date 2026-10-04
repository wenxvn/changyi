"""Reported completed exclusion vs unfinished or unrelated actions, facts only."""
CASES = (
    ("医生已经排除糖尿病", False, ""),
    ("医生明确排除糖尿病", False, ""),
    ("医生未能排除糖尿病", False, "糖尿病"),
    ("医生尚未排除糖尿病", False, "糖尿病"),
    ("医生不能排除糖尿病", False, "糖尿病"),
    ("我已确诊糖尿病，医生排除预约冲突", True, "糖尿病"),
    ("医生已经排除糖尿病，我已确诊乙肝", True, "乙肝"),
)


def run():
    import app
    rows = []
    client = app.app.test_client()
    for text, expected, disease in CASES:
        fact = app.detect_known_disease(text)
        data = client.post("/api/v1/triage", json={"condition": text}).get_json()["data"]
        rows.append({"text": text, "expected_known_fact": expected, "expected_primary": disease,
                     "known_fact": fact, "status": data["triage_status"], "clinical_label_verified": False,
                     "pass": fact["has_known_disease"] == expected and fact["disease"] == disease})
    return {"scope": "reported_completed_exclusion_fact_policy_not_clinical_clearance",
            "total": len(rows), "failed": sum(not r["pass"] for r in rows), "rows": rows}
