"""Ordinary department candidates follow the existing public Safety Gate."""
CASES = (
    ("我现在喘不上气", "EMERGENCY"),
    ("我现在是否喘不上气，我喘不上气", "EMERGENCY"),
    ("我现在是否呼吸困难，但有咳嗽", "INSUFFICIENT_INFORMATION"),
    ("抽搐", "INSUFFICIENT_INFORMATION"),
    ("咳嗽", "ROUTINE"),
    ("我确诊糖尿病", "URGENT"),
)


def run():
    import app
    from backend.app.domain.triage.safety_gate import triage_status_from_legacy
    rows = []
    client = app.app.test_client()
    for text, expected in CASES:
        gated = expected in ("EMERGENCY", "INSUFFICIENT_INFORMATION")
        for endpoint in ("triage", "recommendations"):
            response = client.post("/api/v1/" + endpoint, json={"condition": text})
            data = response.get_json()["data"]
            status = triage_status_from_legacy(data["triage"]).value
            counts = [len(data["triage"].get("department_candidates", [])),
                      len(data["htriage_analysis"].get("department_candidates", []))]
            passed = response.status_code == 200 and status == expected
            passed = passed and (counts == [0, 0] if gated else all(counts))
            rows.append({"text": text, "endpoint": endpoint, "expected_status": expected,
                         "status": status, "matched_department": data["matched_department"],
                         "public_department_candidate_counts": counts,
                         "clinical_label_verified": False, "pass": bool(passed)})
    return {"scope": "gated_public_department_candidate_contract_not_clinical_validation",
            "total": len(rows), "input_count": len(CASES), "failed": sum(not r["pass"] for r in rows), "rows": rows}
