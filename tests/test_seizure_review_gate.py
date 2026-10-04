import pytest
import app


@pytest.mark.parametrize("condition", ["抽搐", "惊厥", "不确定有没有抽搐", "抽搐不确定", "我妈妈正在抽搐"])
def test_unresolved_seizure_report_requires_review_without_ranking(condition):
    client = app.app.test_client()
    data = client.post("/api/v1/triage", json={"condition": condition}).get_json()["data"]
    assert data["triage_status"] == "INSUFFICIENT_INFORMATION"
    assert data["matched_department"] is None
    assert data["triage"]["followup"]["questions"][0]["id"] == "red_flag_check"
    assert "抽搐" in data["triage"]["followup"]["questions"][0]["question"]
    resources = client.post("/api/v1/recommendations", json={"condition": condition}).get_json()["data"]
    assert not resources["recommended_hospitals"]
    assert not resources["recommended_doctors"]


def test_seizure_confirmation_and_existing_emergency_remain_first():
    client = app.app.test_client()
    for payload in (
        {"condition": "持续抽搐"},
        {"condition": "我妈妈正在持续抽搐"},
        {"condition": "持续胸痛喘不上气，不确定有没有抽搐"},
        {"condition": "抽搐", "followup_answers": [{"question_id": "red_flag_check", "value": "present"}]},
    ):
        assert client.post("/api/v1/triage", json=payload).get_json()["data"]["triage_status"] == "EMERGENCY"


def test_negative_danger_answer_does_not_turn_reported_seizure_into_routine():
    data = app.app.test_client().post("/api/v1/triage", json={"condition": "抽搐", "followup_answers": [{"question_id": "red_flag_check", "value": "none"}]}).get_json()["data"]
    assert data["triage_status"] == "URGENT"


@pytest.mark.parametrize("condition", ["没有抽搐但咳嗽", "未出现抽搐", "以前抽搐，现在好了", "科普：抽搐是什么", "如果出现抽搐会怎样"])
def test_denied_resolved_and_educational_mentions_do_not_trigger_new_gate(condition):
    data = app.app.test_client().post("/api/v1/triage", json={"condition": condition}).get_json()["data"]
    assert not data["triage"].get("defer_resource_routing")
    assert data["triage_status"] != "EMERGENCY"


def test_review_does_not_depend_on_learned_model_availability(monkeypatch):
    monkeypatch.setattr(app.SYMPTOM_DISEASE_MODEL_ADAPTER, "predict", lambda *args, **kwargs: {"available": False, "disease": ""})
    data = app.app.test_client().post("/api/v1/triage", json={"condition": "抽搐"}).get_json()["data"]
    assert data["triage_status"] == "INSUFFICIENT_INFORMATION"
