"""New candidate-evidence consistency protocol, not clinical validation."""
CASES = (
    ("怀疑糖尿病", "exclude_metabolic", None),
    ("如果我有糖尿病应该挂什么科", "exclude_metabolic", None),
    ("糖尿病只是举例，实际没确诊", "exclude_metabolic", None),
    ("已确诊糖尿病，但糖尿病只是举例", "exclude_metabolic", None),
    ("我已确诊乙肝，糖尿病只是一个假设", "keep_hepatitis", None),
    ("怀疑糖尿病但有咳嗽", "keep_respiratory", None),
    ("已确诊糖尿病", "keep_report", None),
    ("怀疑糖尿病", "keep_report", "confirmed"),
    ("目前我呼吸困难，怀疑糖尿病", "emergency", None),
)


def run():
    import app
    rows = []
    for text, expected, answer in CASES:
        body = {"condition": text}
        if answer:
            body["followup_answers"] = [{"question_id": "known_disease_status", "value": answer}]
        data = app.app.test_client().post("/api/v1/triage", json=body).get_json()["data"]
        candidates = data["htriage_analysis"]["disease_candidates"]
        metabolic = any(row["recommended_department"] == "内分泌代谢科" for row in candidates)
        reported = any(row["name"] == "糖尿病" and row["source"] == "user_stated" for row in candidates)
        if expected == "keep_report":
            passed = reported
        elif expected == "emergency":
            passed = not candidates and data["triage_status"] == "EMERGENCY"
        else:
            passed = not metabolic
            if expected == "keep_hepatitis":
                passed = passed and any(row["name"] == "乙肝" and row["source"] == "user_stated" for row in candidates)
            if expected == "keep_respiratory":
                passed = passed and any("呼吸" in row["recommended_department"] for row in candidates)
        rows.append({"text": text, "followup_answer": answer, "expected": expected,
                     "candidates": candidates, "known": data["htriage_analysis"]["known_disease"],
                     "triage_status": data["triage_status"], "pass": passed})
    return {"scope": "synthetic_candidate_evidence_consistency_not_clinical_validation",
            "total": len(rows), "failed": sum(not row["pass"] for row in rows), "rows": rows}
