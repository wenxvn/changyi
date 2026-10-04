"""Declared/unconfirmed disease facts, never clinical diagnosis truth."""
CASES = (
    ("医生考虑糖尿病", False, "糖尿病"),
    ("报告考虑糖尿病", False, "糖尿病"),
    ("医生说考虑糖尿病", False, "糖尿病"),
    ("我考虑是不是糖尿病", False, "糖尿病"),
    ("我已确诊糖尿病", True, "糖尿病"),
    ("我没有糖尿病", False, None),
    ("医生考虑糖尿病，但我已确诊乙肝", True, "乙肝"),
    ("我已确诊糖尿病，考虑调整饮食", True, "糖尿病"),
)


def run():
    import app
    rows = []
    client = app.app.test_client()
    for text, known, disease in CASES:
        analysis = app.build_htriage_analysis(text)
        fact = analysis["known_disease"]
        data = client.post("/api/v1/triage", json={"condition": text}).get_json()["data"]
        passed = fact["has_known_disease"] == known
        if disease:
            passed = passed and fact["disease"] == disease
        rows.append({"text": text, "expected_known_fact": known, "expected_primary_mention": disease,
                     "known_fact": fact, "disease_candidates": analysis.get("disease_candidates", []),
                     "triage_status": data["triage_status"], "matched_department": data["matched_department"],
                     "clinical_label_verified": False, "pass": bool(passed)})
    return {"scope": "considered_disease_fact_assertion_policy_not_clinical_labels",
            "total": len(rows), "failed": sum(not row["pass"] for row in rows), "clinical_accuracy": None, "rows": rows}
