"""Provisional report language remains distinct from reported confirmed facts."""
CASES = (
    ("医生考虑诊断为糖尿病", False, "糖尿病"),
    ("报告倾向糖尿病", False, "糖尿病"),
    ("报告提示可能糖尿病", False, "糖尿病"),
    ("医生说不能排除糖尿病", False, "糖尿病"),
    ("医生建议排查糖尿病", False, "糖尿病"),
    ("我已确诊乙肝，报告倾向糖尿病", True, "乙肝"),
    ("我已确诊糖尿病", True, "糖尿病"),
    ("我已确诊糖尿病，考虑选择内分泌医生", True, "糖尿病"),
)


def run():
    import app
    rows = []
    client = app.app.test_client()
    for text, expected, primary in CASES:
        analysis = app.build_htriage_analysis(text)
        fact = analysis["known_disease"]
        data = client.post("/api/v1/triage", json={"condition": text}).get_json()["data"]
        rows.append({"text": text, "expected_known_fact": expected, "expected_primary_mention": primary,
                     "known_fact": fact, "disease_candidates": analysis["disease_candidates"],
                     "status": data["triage_status"], "matched_department": data["matched_department"],
                     "clinical_label_verified": False,
                     "pass": fact["has_known_disease"] == expected and fact["disease"] == primary})
    return {"scope": "provisional_report_fact_policy_observation_not_clinical_labels",
            "total": len(rows), "failed": sum(not r["pass"] for r in rows), "clinical_accuracy": None, "rows": rows}
