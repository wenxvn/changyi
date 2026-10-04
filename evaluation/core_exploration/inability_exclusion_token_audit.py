"""Different negative tokens scoped to the exclusion action, policy only."""
CASES = (
    ("医生无法排除心梗", "EMERGENCY"),
    ("医生无法完全排除心梗", "EMERGENCY"),
    ("医生没能排除心梗", "EMERGENCY"),
    ("医生没有排除心梗", "EMERGENCY"),
    ("我无心梗", "ROUTINE"),
    ("我没有心梗", "ROUTINE"),
    ("去年医生无法排除心梗，现在我咳嗽", "NOT_EMERGENCY"),
    ("医生无法排除肺炎，我没有心梗", "NOT_EMERGENCY"),
)


def run():
    import app
    from backend.app.domain.medical_input import known_disease_mention_state
    rows = []
    client = app.app.test_client()
    for text, expected in CASES:
        data = client.post("/api/v1/triage", json={"condition": text}).get_json()["data"]
        passed = data["triage_status"] != "EMERGENCY" if expected == "NOT_EMERGENCY" else data["triage_status"] == expected
        rows.append({"text": text, "expected_existing_policy_status": expected, "status": data["triage_status"],
                     "heart_mention_state": known_disease_mention_state(text, "心梗"),
                     "clinical_label_verified": False, "pass": bool(passed)})
    return {"scope": "inability_exclusion_negative_token_policy_not_clinical_validation",
            "total": len(rows), "failed": sum(not r["pass"] for r in rows), "rows": rows}
