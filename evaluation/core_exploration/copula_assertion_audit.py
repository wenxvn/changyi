"""Copula polarity and question engineering contract, not medical diagnosis."""
CASES = (
    ("是不是咳嗽", [], [], ["cough"], [], False),
    ("不是咳嗽", [], ["cough"], [], [], False),
    ("我不是咳嗽而是恶心", ["nausea"], ["cough"], [], [], True),
    ("不是没有咳嗽", [], [], ["cough"], [], False),
    ("不是咳嗽而是咳嗽", ["cough"], [], [], ["cough"], False),
    ("是不是现在咳嗽", [], [], ["cough"], [], False),
    ("可能现在没有咳嗽但恶心", ["nausea"], [], ["cough"], [], False),
    ("咳嗽是不是存在", [], [], ["cough"], [], False),
    ("不是咳嗽而是正在呼吸困难", None, ["cough"], [], [], True),
)


def run():
    import app
    rows = []
    for text, present, absent, unknown, conflict, accepted in CASES:
        prediction = app.predict_disease_name(text, details=True)
        assertions = prediction["input_assertions"]
        data = app.app.test_client().post("/api/v1/triage", json={"condition": text}).get_json()["data"]
        passed = assertions["absent"] == absent and assertions["unknown"] == unknown and assertions["contradiction"] == conflict
        if present is not None:
            passed = passed and assertions["present"] == present
        passed = passed and prediction["abstained"] is (not accepted)
        if text == "不是咳嗽":
            terms = {term for tag in data["htriage_analysis"]["symptom_tags"] for term in tag.get("matched_terms", [])}
            passed = passed and "咳嗽" not in terms
        if "正在呼吸困难" in text:
            passed = passed and data["triage_status"] == "EMERGENCY" and not data["disease_prediction"].get("predictions")
        rows.append({"text": text, "expected_present": present, "expected_absent": absent, "expected_unknown": unknown,
                     "expected_contradiction": conflict, "expected_accepted": accepted, "assertions": assertions,
                     "abstained": prediction["abstained"], "triage_status": data["triage_status"],
                     "matched_department": data["matched_department"], "pass": passed})
    return {"scope": "synthetic_copula_question_negation_scope_not_clinical_validation",
            "total": len(rows), "failed": sum(not row["pass"] for row in rows), "rows": rows}
