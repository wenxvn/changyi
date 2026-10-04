"""Observe explicit current clause existence language; no clinical labels."""
CASES = (
    ("没有胸痛，现在是否咳嗽", "unknown"),
    ("没有胸痛，现在不确定是否咳嗽", "unknown"),
    ("没有胸痛，现在可能咳嗽", "unknown"),
    ("没有胸痛，如果现在咳嗽", "unknown"),
    ("没有胸痛，现在有咳嗽", "present"),
    ("没有胸痛，现在没有咳嗽", "absent"),
    ("没有胸痛，现在不确定为什么咳嗽", "present"),
    ("不确定是否胸痛，但现在有咳嗽", "present"),
)


def run():
    import app
    from backend.app.domain.medical_input import contains_positive
    rows = []
    client = app.app.test_client()
    for text, expected in CASES:
        prediction = app.predict_disease_name(text, details=True)
        assertions = prediction.get("input_assertions", {})
        response = client.post("/api/v1/triage", json={"condition": text})
        data = response.get_json()["data"]
        states = [state for state in ("present", "absent", "unknown")
                  if "cough" in assertions.get(state, [])]
        lexical = contains_positive(text, ["咳嗽"])
        rows.append({"text": text, "expected_existence_state": expected,
                     "auxiliary_states": states, "lexical_positive": lexical,
                     "auxiliary_contract_pass": states == [expected],
                     "lexical_existence_agrees": lexical == (expected == "present"),
                     "execution_valid": response.status_code == 200 and data["original_condition"] == text,
                     "triage_status": data["triage_status"],
                     "matched_department": data["matched_department"],
                     "abstained": prediction["abstained"],
                     "abstain_reason": prediction.get("abstain_reason"),
                     "clinical_label_verified": False})
    return {"scope": "current_clause_uncertainty_language_observation_no_clinical_oracle",
            "total": len(rows),
            "failed": sum(not row["auxiliary_contract_pass"] for row in rows),
            "lexical_existence_mismatches": sum(not row["lexical_existence_agrees"] for row in rows),
            "execution_failures": sum(not row["execution_valid"] for row in rows),
            "clinical_accuracy": None, "rows": rows}
