"""Finite modifier scope against the existing unresolved-exclusion policy."""
CASES = (
    ("医生未能明确排除心梗", "EMERGENCY"),
    ("医生尚未明确排除心梗", "EMERGENCY"),
    ("医生未能完全排除心梗", "EMERGENCY"),
    ("医生未能够排除心梗", "EMERGENCY"),
    ("医生未能排除心梗", "EMERGENCY"),
    ("我没有心梗", "ROUTINE"),
    ("去年医生未能明确排除心梗，现在我咳嗽", "NOT_EMERGENCY"),
    ("医生未能明确排除肺炎，我没有心梗", "NOT_EMERGENCY"),
)


def run():
    import app
    from backend.app.domain.medical_input import known_disease_mention_state
    client = app.app.test_client()
    rows = []
    for text, expected in CASES:
        data = client.post("/api/v1/triage", json={"condition": text}).get_json()["data"]
        passed = data["triage_status"] != "EMERGENCY" if expected == "NOT_EMERGENCY" else data["triage_status"] == expected
        rows.append({"text": text, "expected_existing_policy_status": expected, "status": data["triage_status"],
                     "heart_mention_state": known_disease_mention_state(text, "心梗"),
                     "clinical_label_verified": False, "pass": bool(passed)})
    return {"scope": "finite_qualified_exclusion_scope_policy_not_clinical_accuracy",
            "total": len(rows), "failed": sum(not r["pass"] for r in rows), "rows": rows}
