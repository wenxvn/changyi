import pytest
import app
from backend.app.domain.triage.publication import safety_first_triage, safety_first_htriage_payload
from backend.app.domain.triage.safety_gate import evaluate_safety_gate
from evaluation.core_exploration.gated_department_publication_audit import CASES


@pytest.mark.parametrize("text,status", CASES)
def test_candidate_direction_publication_follows_safety_status(text, status):
    data = app.app.test_client().post("/api/v1/triage", json={"condition": text}).get_json()["data"]
    assert data["triage_status"] == status
    counts = [len(data["triage"]["department_candidates"]), len(data["htriage_analysis"]["department_candidates"])]
    if status in ("EMERGENCY", "INSUFFICIENT_INFORMATION"):
        assert counts == [0, 0]
    else:
        assert all(counts)


def test_public_projection_does_not_mutate_internal_candidate_evidence():
    original = {"level": "emergency", "department_candidates": [{"department": "合成科室"}]}
    decision = evaluate_safety_gate(original)
    assert safety_first_triage(original, decision)["department_candidates"] == []
    assert safety_first_htriage_payload(original, decision)["department_candidates"] == []
    assert original["department_candidates"] == [{"department": "合成科室"}]
