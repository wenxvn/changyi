"""Unsuccessful exclusion retains concern, not clinical diagnosis certainty."""
from .exclusion_scope_fact_audit import CASES


def run():
    import app
    from backend.app.domain.medical_input import known_disease_mention_state
    rows = []
    client = app.app.test_client()
    for text, known, expected_state, expected_status in CASES[2:]:
        word = "心梗" if "心梗" in text else "糖尿病"
        fact = app.detect_known_disease(text)
        state = known_disease_mention_state(text, word)
        data = client.post("/api/v1/triage", json={"condition": text}).get_json()["data"]
        passed = fact["has_known_disease"] == known and state == expected_state
        if expected_status:
            passed = passed and data["triage_status"] == expected_status
        rows.append({"text": text, "expected_state": expected_state, "state": state,
                     "expected_existing_status": expected_status, "status": data["triage_status"],
                     "clinical_label_verified": False, "pass": bool(passed)})
    return {"scope": "unresolved_exclusion_risk_policy_subset_not_completed_exclusion_or_clinical_validation",
            "total": len(rows), "failed": sum(not r["pass"] for r in rows), "rows": rows}
