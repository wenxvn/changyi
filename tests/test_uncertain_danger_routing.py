"""Uncertain risk is not a clear negative and must not trigger normal ranking."""
import app


def test_raw_unknown_danger_requires_confirmation_and_has_no_forced_direction():
    client = app.app.test_client()
    for condition in ("不确定有没有胸痛", "我说不清有没有呼吸困难"):
        data = client.post("/api/v1/triage", json={"condition": condition}).get_json()["data"]
        assert data["triage_status"] == "INSUFFICIENT_INFORMATION"
        assert data["matched_department"] is None
        assert data["disease_prediction"]["abstained"]
        assert data["original_condition"] == condition
        assert data["triage"]["followup"]["questions"][0]["id"] == "red_flag_check"


def test_unknown_danger_does_not_get_ranked_resources_or_preference_override():
    data = app.app.test_client().post("/api/v1/recommendations", json={
        "condition": "不确定有没有胸痛", "expert_preference": "wish_expert",
        "routing_preferences": {"distance_preference": "prefer_nearby"},
    }).get_json()["data"]
    assert data["recommended_hospitals"] == []
    assert data["recommended_doctors"] == []
    assert data["matched_department"] is None


def test_clear_emergency_precedes_another_unknown_signal_and_unknown_answer():
    client = app.app.test_client()
    for payload in (
        {"condition": "持续胸痛喘不上气，不确定有没有头痛"},
        {"condition": "持续胸痛喘不上气", "followup_answers": [{"question_id": "red_flag_check", "value": "unknown"}]},
    ):
        data = client.post("/api/v1/triage", json=payload).get_json()["data"]
        assert data["triage_status"] == "EMERGENCY"


def test_explicit_structured_resolution_and_clear_denial_remain_separate():
    client = app.app.test_client()
    for condition in ("没有胸痛", "没有发热但咳嗽"):
        data = client.post("/api/v1/triage", json={"condition": condition}).get_json()["data"]
        assert data["triage_status"] == "ROUTINE"
    data = client.post("/api/v1/triage", json={"condition": "不确定有没有胸痛", "followup_answers": [{"question_id": "red_flag_check", "value": "none"}]}).get_json()["data"]
    assert not data["triage"].get("defer_resource_routing")
