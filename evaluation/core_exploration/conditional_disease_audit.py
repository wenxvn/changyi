"""New fixed conditional-report protocol; synthetic, not clinical accuracy."""
CASES = (
    ("如果我有糖尿病应该挂什么科", False, "糖尿病"),
    ("假如患有糖尿病", False, "糖尿病"),
    ("如果我妈妈有糖尿病会怎样", False, "糖尿病"),
    ("倘若我有糖尿病", False, "糖尿病"),
    ("已确诊糖尿病，如果发热怎么办", True, "糖尿病"),
    ("我已确诊乙肝但如果糖尿病怎么办", True, "乙肝"),
)


def run():
    import app
    rows = []
    for text, expected, disease in CASES:
        data = app.app.test_client().post("/api/v1/triage", json={"condition": text}).get_json()["data"]
        known = data["htriage_analysis"]["known_disease"]
        rows.append({"text": text, "expected_known": expected, "expected_disease": disease, "actual": known, "pass": known["has_known_disease"] == expected and known["disease"] == disease})
    return {"scope": "synthetic_conditional_report_contract_not_clinical_validation", "total": len(rows), "failed": sum(not row["pass"] for row in rows), "rows": rows}
