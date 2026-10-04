"""Declared non-Safety route evidence policy; no clinical department labels."""
CASES = (
    ("现在是否咳嗽", False),
    ("现在不确定是否咳嗽", False),
    ("没有胸痛，现在可能咳嗽", False),
    ("没有胸痛，现在咳嗽", True),
    ("现在不确定为什么咳嗽", True),
    ("我现在有咳嗽", True),
    ("现在没有咳嗽", False),
    ("我确诊糖尿病，现在是否咳嗽", False),
    ("我喘不上气，现在是否咳嗽", None),
)


def run():
    import app
    rows = []
    client = app.app.test_client()
    for text, respiratory in CASES:
        data = client.post("/api/v1/triage", json={"condition": text}).get_json()["data"]
        passed = data["original_condition"] == text
        if respiratory is not None:
            passed = passed and (data["matched_department"] == "呼吸内科") == respiratory
        else:
            passed = passed and data["triage_status"] == "EMERGENCY"
        rows.append({"text": text, "expected_cough_based_respiratory_route": respiratory,
                     "triage_status": data["triage_status"],
                     "matched_department": data["matched_department"],
                     "clinical_label_verified": False, "pass": bool(passed)})
    return {"scope": "bounded_cough_route_evidence_policy_not_clinical_department_accuracy",
            "total": len(rows), "failed": sum(not r["pass"] for r in rows), "rows": rows}
