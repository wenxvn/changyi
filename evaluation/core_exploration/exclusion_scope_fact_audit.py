"""Failure to exclude is distinct from an asserted absence, policy only."""
CASES = (
    ("医生已经排除糖尿病", False, "absent", None),
    ("医生明确排除糖尿病", False, "absent", None),
    ("医生未能排除糖尿病", False, "uncertain", None),
    ("医生尚未排除糖尿病", False, "uncertain", None),
    ("医生未能排除心梗", False, "uncertain", "EMERGENCY"),
    ("医生尚未排除心梗", False, "uncertain", "EMERGENCY"),
    ("医生不能排除心梗", False, "uncertain", "EMERGENCY"),
    ("我没有心梗", False, "absent", "ROUTINE"),
)


def run():
    import app
    from backend.app.domain.medical_input import known_disease_mention_state
    rows = []
    client = app.app.test_client()
    for text, known, expected_state, expected_status in CASES:
        word = "心梗" if "心梗" in text else "糖尿病"
        fact = app.detect_known_disease(text)
        state = known_disease_mention_state(text, word)
        data = client.post("/api/v1/triage", json={"condition": text}).get_json()["data"]
        passed = fact["has_known_disease"] == known and state == expected_state
        if expected_status:
            passed = passed and data["triage_status"] == expected_status
        rows.append({"text": text, "expected_state": expected_state, "observed_state": state,
                     "expected_existing_policy_status": expected_status, "status": data["triage_status"],
                     "known_fact": fact, "clinical_label_verified": False, "pass": bool(passed)})
    return {"scope": "exclusion_verb_scope_policy_not_clinical_validation", "total": len(rows),
            "failed": sum(not r["pass"] for r in rows), "clinical_accuracy": None, "rows": rows}
