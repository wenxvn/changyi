"""Existing strong cue priority under unrelated question context."""
CASES = (
    ("现在咳嗽是不是，我喘不上气", True),
    ("我喘不上气，咳嗽是不是", True),
    ("没有胸痛，我喘不上气", True),
    ("咳嗽是不是，我现在喘不上气", True),
    ("咳嗽是不是，如果我喘不上气", False),
    ("咳嗽是不是，我是否喘不上气", False),
    ("咳嗽是不是，我以前喘不上气", False),
    ("咳嗽是不是，我没有喘不上气", False),
    ("咳嗽是不是，我喘不上气是不是", False),
    ("咳嗽是不是，我喘不上气已经好了", False),
)


def run():
    import app
    rows = []
    client = app.app.test_client()
    for text, emergency in CASES:
        data = client.post("/api/v1/triage", json={"condition": text}).get_json()["data"]
        rows.append({"text": text, "expected_existing_emergency_priority": emergency,
                     "triage_status": data["triage_status"], "matched_department": data["matched_department"],
                     "clinical_label_verified": False,
                     "pass": (data["triage_status"] == "EMERGENCY") == emergency and data["original_condition"] == text})
    return {"scope": "bounded_self_report_safety_policy_not_clinical_validation",
            "total": len(rows), "failed": sum(not r["pass"] for r in rows), "rows": rows}
