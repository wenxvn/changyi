import pytest
import app
from evaluation.core_exploration.emergency_default_direction_audit import CASES


@pytest.mark.parametrize("text,answer,status,dept", CASES)
def test_emergency_defaults_are_separate_from_routine_defaults(text, answer, status, dept):
    body = {"condition": text}
    if answer:
        body["followup_answers"] = [{"question_id": "red_flag_check", "value": answer}]
    data = app.app.test_client().post("/api/v1/triage", json=body).get_json()["data"]
    assert data["triage_status"] == status
    assert data["matched_department"] == dept
    assert data["original_condition"] == text
