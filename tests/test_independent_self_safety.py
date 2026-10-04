import pytest
import app
from evaluation.core_exploration.independent_self_safety_audit import CASES

@pytest.mark.parametrize("text,emergency", CASES)
def test_other_clause_cannot_override_a_direct_self_report(text, emergency):
    data = app.app.test_client().post("/api/v1/triage", json={"condition": text}).get_json()["data"]
    assert (data["triage_status"] == "EMERGENCY") is emergency
    assert data["original_condition"] == text
