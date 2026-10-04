"""Input-scope publication contract, not out-of-domain recognition accuracy."""
CASES = (("肚脐疼", False), ("咳嗽和肚脐疼", True), ("肚脐疼和咳嗽", True),
         ("咳嗽", True), ("cough", True), ("持续胸痛喘不上气，肚脐疼", False))


def run():
    import app
    rows = []
    for text, accepted in CASES:
        data = app.app.test_client().post("/api/v1/triage", json={"condition": text}).get_json()["data"]
        prediction = data["disease_prediction"]
        coverage = prediction.get("input_coverage", {})
        passed = prediction.get("abstained") is (not accepted)
        passed = passed and coverage.get("scope") == "recognized_lexical_evidence_only" and coverage.get("full_text_understanding_verified") is False
        if accepted:
            passed = passed and prediction.get("normalized_symptoms") == ["cough"] and bool(prediction.get("notice"))
            passed = passed and coverage.get("model_feature_count") == 1
        if "持续胸痛" in text:
            passed = passed and data["triage_status"] == "EMERGENCY" and prediction["abstain_reason"] == "safety_gate_priority"
        rows.append({"text": text, "expected_accepted": accepted, "coverage": coverage,
                     "abstained": prediction.get("abstained"), "notice": prediction.get("notice"),
                     "triage_status": data["triage_status"], "pass": passed})
    return {"scope": "synthetic_input_scope_publication_not_unknown_symptom_detection",
            "total": len(rows), "failed": sum(not row["pass"] for row in rows), "rows": rows}
