import pytest
import app
from evaluation.core_exploration.current_existence_safety_audit import CASES

@pytest.mark.parametrize("text,expected", CASES)
def test_existence_query_and_independent_reports_keep_separate_priority(text, expected):
    data = app.app.test_client().post("/api/v1/triage", json={"condition": text}).get_json()["data"]
    assert data["triage_status"] == expected
    assert data["original_condition"] == text
    if expected == "INSUFFICIENT_INFORMATION":
        assert data["matched_department"] is None
        assert data["triage"]["defer_resource_routing"] is True

def test_structured_danger_confirmation_still_precedes_uncertain_original_text():
    text = "我现在是否喘不上气"
    data = app.app.test_client().post("/api/v1/triage", json={"condition": text,
        "followup_answers": [{"question_id": "red_flag_check", "value": "present"}]}).get_json()["data"]
    assert data["triage_status"] == "EMERGENCY"
    assert data["original_condition"] == text

def test_space_before_a_queried_cue_retains_the_confirmation_channel():
    data = app.app.test_client().post("/api/v1/triage", json={"condition": "我现在是否 喘不上气"}).get_json()["data"]
    assert data["triage_status"] == "INSUFFICIENT_INFORMATION"
    assert any(q["id"] == "red_flag_check" for q in data["triage"]["followup"]["questions"])
