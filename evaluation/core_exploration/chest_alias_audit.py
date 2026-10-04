"""Unverified chest-tightness equivalence isolation, not clinical diagnosis."""
CASES = (
    ("胸闷", False, True), ("胸闷和咳嗽", False, True),
    ("没有胸闷但咳嗽", True, False), ("没有胸闷但呼吸困难", True, False),
    ("呼吸困难", True, False), ("胸闷和呼吸困难", False, True),
    ("假如胸闷", False, True), ("持续胸痛喘不上气，胸闷", False, True),
)


def run():
    import app
    rows = []
    for text, accepted, quarantined in CASES:
        prediction = app.predict_disease_name(text, details=True)
        data = app.app.test_client().post("/api/v1/triage", json={"condition": text}).get_json()["data"]
        issues = prediction.get("mapping_review", {}).get("issues", [])
        chest_issue = any(item["alias"] == "胸闷" and item["reason"] == "unverified_semantic_equivalence" for item in issues)
        passed = prediction.get("abstained") is (not accepted) and chest_issue == quarantined
        if accepted:
            expected = "breathlessness" if "呼吸困难" in text else "cough"
            passed = passed and expected in prediction.get("normalized_symptoms", [])
        if "呼吸困难" in text or "持续胸痛" in text:
            passed = passed and data["triage_status"] == "EMERGENCY" and not data["disease_prediction"].get("predictions")
        rows.append({"text": text, "expected_accepted": accepted, "expected_quarantine": quarantined,
                     "abstained": prediction.get("abstained"), "abstain_reason": prediction.get("abstain_reason"),
                     "codes": prediction.get("normalized_symptoms"), "mapping_issues": issues,
                     "triage_status": data["triage_status"], "matched_department": data["matched_department"], "pass": passed})
    return {"scope": "synthetic_unverified_alias_isolation_not_medical_equivalence_certification",
            "total": len(rows), "failed": sum(not row["pass"] for row in rows), "rows": rows}
