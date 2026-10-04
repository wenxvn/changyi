"""Bounded auxiliary review, no clinical severity judgement or Safety change."""
CASES = (
    ("没有严重胸痛", True, [], ["chest_pain"], False),
    ("我没有严重胸痛但有轻微胸痛", True, ["chest_pain"], [], False),
    ("没有剧烈胸痛但咳嗽", True, ["cough"], ["chest_pain"], False),
    ("没有胸痛", False, [], [], False),
    ("我有轻微胸痛", False, ["chest_pain"], [], True),
    ("是不是严重胸痛", False, [], ["chest_pain"], False),
    ("持续胸痛喘不上气，没有严重胸痛", True, None, [], False),
)


def run():
    import app
    rows = []
    for text, reviewed, present, unknown, accepted in CASES:
        prediction = app.predict_disease_name(text, details=True)
        assertions = prediction["input_assertions"]
        data = app.app.test_client().post("/api/v1/triage", json={"condition": text}).get_json()["data"]
        review = prediction.get("input_scope_review", {})
        passed = bool(review.get("required")) == reviewed and assertions["unknown"] == unknown
        if present is not None:
            passed = passed and assertions["present"] == present
        passed = passed and prediction["abstained"] is (not accepted)
        if reviewed:
            passed = passed and prediction.get("abstain_reason") == "qualified_negation_scope_unverified"
        if "持续胸痛喘不上气" in text:
            passed = passed and data["triage_status"] == "EMERGENCY" and not data["disease_prediction"].get("predictions")
        rows.append({"text": text, "review_expected": reviewed, "expected_present": present, "expected_unknown": unknown,
                     "expected_accepted": accepted, "assertions": assertions, "review": review,
                     "abstain_reason": prediction.get("abstain_reason"), "triage_status": data["triage_status"],
                     "matched_department": data["matched_department"], "pass": passed})
    return {"scope": "synthetic_auxiliary_qualified_chest_review_not_clinical_severity_validation",
            "total": len(rows), "failed": sum(not row["pass"] for row in rows), "rows": rows}
