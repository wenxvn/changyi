"""Synthetic auxiliary input and published symptom-evidence contract."""
CASES = (
    ("如果咳嗽", [], ["cough"], [], ["咳嗽"]),
    ("假如咳嗽", [], ["cough"], [], ["咳嗽"]),
    ("假设有咳嗽", [], ["cough"], [], ["咳嗽"]),
    ("倘若咳嗽", [], ["cough"], [], ["咳嗽"]),
    ("咳嗽只是举例", [], ["cough"], [], ["咳嗽"]),
    ("如果咳嗽但现在恶心", ["nausea"], ["cough"], ["恶心"], ["咳嗽"]),
    ("我现在咳嗽但假设恶心怎么办", ["cough"], ["nausea"], ["咳嗽"], ["恶心"]),
    ("我现在咳嗽", ["cough"], [], ["咳嗽"], []),
    ("目前我呼吸困难，假如咳嗽", None, ["cough"], ["呼吸困难"], ["咳嗽"]),
)


def run():
    import app
    rows = []
    for text, present, unknown, included, excluded in CASES:
        prediction = app.predict_disease_name(text, details=True)
        data = app.app.test_client().post("/api/v1/triage", json={"condition": text}).get_json()["data"]
        assertions = prediction.get("input_assertions", {})
        terms = {term for tag in data["htriage_analysis"]["symptom_tags"] for term in tag.get("matched_terms", [])}
        passed = set(unknown) <= set(assertions.get("unknown", []))
        if present is not None:
            passed = passed and set(assertions.get("present", [])) == set(present)
        passed = passed and set(included) <= terms and not (set(excluded) & terms)
        if unknown:
            passed = passed and prediction.get("abstained") is True and not prediction.get("predictions")
        else:
            passed = passed and prediction.get("abstained") is False
        if "呼吸困难" in text:
            passed = passed and data["triage_status"] == "EMERGENCY"
        rows.append({"text": text, "expected_present": present, "expected_unknown": unknown,
                     "expected_included_terms": included, "expected_excluded_terms": excluded,
                     "assertions": assertions, "abstained": prediction.get("abstained"),
                     "abstain_reason": prediction.get("abstain_reason"), "published_terms": sorted(terms),
                     "triage_status": data["triage_status"], "pass": passed})
    return {"scope": "synthetic_hypothetical_auxiliary_and_tag_contract_not_clinical_validation",
            "total": len(rows), "failed": sum(not row["pass"] for row in rows), "rows": rows}
