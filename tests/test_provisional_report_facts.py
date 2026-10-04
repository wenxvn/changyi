import pytest
import app
from evaluation.core_exploration.provisional_report_fact_audit import CASES


@pytest.mark.parametrize("text,known,primary", CASES)
def test_provisional_language_does_not_create_a_confirmed_fact(text, known, primary):
    fact = app.detect_known_disease(text)
    assert fact["has_known_disease"] is known
    assert fact["disease"] == primary


def test_non_disease_tasks_do_not_erase_a_reported_condition():
    assert app.detect_known_disease("我已确诊糖尿病，倾向选择内分泌医生并排查预约时间")["has_known_disease"] is True


def test_cannot_exclude_danger_is_not_a_negative_safety_signal():
    data = app.app.test_client().post("/api/v1/triage", json={"condition": "医生说不能排除心梗"}).get_json()["data"]
    assert data["triage_status"] == "EMERGENCY"


def test_structured_confirmation_remains_user_reported_evidence():
    data = app.app.test_client().post("/api/v1/triage", json={"condition": "报告倾向糖尿病",
        "followup_answers": [{"question_id": "red_flag_check", "value": "none"},
                             {"question_id": "known_disease_status", "value": "confirmed"}]}).get_json()["data"]
    fact = data["htriage_analysis"]["known_disease"]
    assert fact["has_known_disease"] is True and fact["evidence_source"] == "structured_followup"
