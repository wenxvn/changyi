import pytest
import app
from evaluation.core_exploration.copula_existence_safety_audit import CASES


@pytest.mark.parametrize("text,status", CASES)
def test_copula_question_is_separate_from_a_current_report(text, status):
    data = app.app.test_client().post("/api/v1/triage", json={"condition": text}).get_json()["data"]
    assert data["triage_status"] == status
    assert data["original_condition"] == text


def test_confirmed_danger_still_precedes_the_original_query():
    data = app.app.test_client().post("/api/v1/triage", json={"condition": "我现在是不是喘不上气",
        "followup_answers": [{"question_id": "red_flag_check", "value": "present"}]}).get_json()["data"]
    assert data["triage_status"] == "EMERGENCY"


def test_existing_chest_pain_with_diagnostic_concern_policy_is_preserved():
    data = app.app.test_client().post("/api/v1/triage", json={"condition": "我现在胸痛，是不是心梗"}).get_json()["data"]
    assert data["triage_status"] == "EMERGENCY"
