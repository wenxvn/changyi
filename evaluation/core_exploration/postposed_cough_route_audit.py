"""Locate later rule fallback after a direct cough assertion gate."""
CASES = (
    ("现在咳嗽是不是", False),
    ("现在咳嗽说不清", False),
    ("现在咳嗽是否有", False),
    ("现在咳嗽不确定", False),
    ("现在有咳嗽", True),
    ("现在没有咳嗽", False),
    ("现在咳嗽是不是，我确诊糖尿病", False),
    ("现在咳嗽是不是，我喘不上气", None),
)


def run():
    import app
    from backend.app.domain.symptom_assertions import has_asserted_cough_route_evidence
    rows = []
    client = app.app.test_client()
    for text, expected in CASES:
        data = client.post("/api/v1/triage", json={"condition": text}).get_json()["data"]
        passed = data["original_condition"] == text
        if expected is None:
            passed = passed and data["triage_status"] == "EMERGENCY"
        else:
            passed = passed and (data["matched_department"] == "呼吸内科") == expected
        analysis = app.build_htriage_analysis(text)
        rows.append({"text": text, "expected_cough_based_respiratory_route": expected,
                     "pure_cough_route_evidence": has_asserted_cough_route_evidence(text),
                     "direct_department_match": app.match_department(text),
                     "department_candidates": analysis.get("department_candidates", []),
                     "disease_candidates": analysis.get("disease_candidates", []),
                     "triage_status": data["triage_status"],
                     "matched_department": data["matched_department"],
                     "clinical_label_verified": False, "pass": bool(passed)})
    return {"scope": "postposed_cough_route_evidence_policy_observation_not_clinical_labels",
            "total": len(rows), "failed": sum(not r["pass"] for r in rows),
            "clinical_accuracy": None, "rows": rows}
