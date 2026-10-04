import pytest
import app


@pytest.mark.parametrize("condition", ["不确定有没有抽搐", "抽搐不确定", "我妈妈说不清是否抽搐"])
def test_denial_of_danger_conditions_does_not_confirm_uncertain_symptom(condition):
    payload = {"condition": condition, "followup_answers": [{"question_id": "red_flag_check", "value": "none"}]}
    client = app.app.test_client()
    data = client.post("/api/v1/triage", json=payload).get_json()["data"]
    assert data["triage_status"] == "INSUFFICIENT_INFORMATION"
    assert data["matched_department"] is None
    ranked = client.post("/api/v1/recommendations", json=payload).get_json()["data"]
    assert not ranked["recommended_hospitals"]
    assert not ranked["recommended_doctors"]


@pytest.mark.parametrize("condition", ["我妈妈持续抽搐", "我爸一直在抽搐", "家人惊厥不止"])
def test_current_ongoing_bystander_report_uses_existing_emergency_rule(condition):
    data = app.app.test_client().post("/api/v1/triage", json={"condition": condition}).get_json()["data"]
    assert data["triage_status"] == "EMERGENCY"


@pytest.mark.parametrize("condition", ["我妈妈以前持续抽搐，现在好了", "家人没有持续抽搐", "科普：持续抽搐是什么", "如果我妈妈持续抽搐会怎样"])
def test_noncurrent_bystander_report_does_not_gain_emergency_override(condition):
    data = app.app.test_client().post("/api/v1/triage", json={"condition": condition}).get_json()["data"]
    assert data["triage_status"] != "EMERGENCY"
