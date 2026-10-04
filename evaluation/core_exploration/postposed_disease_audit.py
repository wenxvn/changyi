"""Fixed direct postposed-hypothesis protocol, synthetic engineering evidence."""
CASES = (
    ("糖尿病只是一个假设，实际没确诊", False, "糖尿病"),
    ("糖尿病是假设的情况，我没确诊", False, "糖尿病"),
    ("糖尿病只是举例，实际没确诊", False, "糖尿病"),
    ("糖尿病仅是一种假想情况", False, "糖尿病"),
    ("我已确诊乙肝，糖尿病只是一个假设", True, "乙肝"),
    ("已确诊糖尿病，假设发热怎么办", True, "糖尿病"),
    ("已确诊糖尿病，但糖尿病只是举例", False, "糖尿病"),
    ("目前我呼吸困难，糖尿病只是一个假设", False, "糖尿病"),
)


def run():
    import app
    rows = []
    for text, expected, disease in CASES:
        data = app.app.test_client().post("/api/v1/triage", json={"condition": text}).get_json()["data"]
        known = data["htriage_analysis"]["known_disease"]
        passed = known["has_known_disease"] == expected and known["disease"] == disease
        if "呼吸困难" in text:
            passed = passed and data["triage_status"] == "EMERGENCY"
        rows.append({"text": text, "expected_known": expected, "expected_disease": disease,
                     "actual": known, "triage_status": data["triage_status"], "pass": passed})
    return {"scope": "synthetic_direct_postposed_hypothesis_not_clinical_validation",
            "total": len(rows), "failed": sum(not row["pass"] for row in rows), "rows": rows}
