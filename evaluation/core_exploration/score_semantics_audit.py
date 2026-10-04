"""Synthetic score interpretation contract; no calibration performance claim."""
CASES = ("咳嗽", "恶心", "已确诊糖尿病", "假如咳嗽", "持续胸痛喘不上气", "抽搐")


def run():
    import app
    rows = []
    for text in CASES:
        data = app.app.test_client().post("/api/v1/triage", json={"condition": text}).get_json()["data"]
        htriage = data["htriage_analysis"]
        semantics = htriage.get("candidate_score_semantics", {})
        prediction_semantics = data["disease_prediction"].get("probability_semantics", {})
        candidates = htriage["disease_candidates"]
        passed = semantics.get("kind") == "relative_support_score" and semantics.get("calibrated") is False and semantics.get("clinical_probability") is False
        passed = passed and all(row.get("relative_support_score") == row["probability"] and row.get("score_kind") == "relative_support_score" for row in candidates)
        passed = passed and prediction_semantics.get("kind") == "uncalibrated_model_posterior" and prediction_semantics.get("clinical_probability") is False
        if data["triage_status"] in ("EMERGENCY", "INSUFFICIENT_INFORMATION"):
            passed = passed and not candidates and not data["disease_prediction"].get("predictions")
        rows.append({"text": text, "triage_status": data["triage_status"], "candidate_semantics": semantics,
                     "prediction_semantics": prediction_semantics, "candidates": candidates, "pass": passed})
    return {"scope": "synthetic_score_publication_contract_not_probability_calibration",
            "total": len(rows), "failed": sum(not row["pass"] for row in rows), "rows": rows}
