import pytest
import app


@pytest.mark.parametrize("text,reason", [
    ("发热和咳嗽", "unsupported_model_feature"),
    ("抽搐和咳嗽", "unverified_semantic_equivalence"),
    ("皮疹不确定", "symptom_assertion_uncertain"),
    ("以前咳嗽", "noncurrent_symptom_context"),
    ("没有咳嗽但有咳嗽", "contradictory_symptom_assertions"),
])
def test_empty_auxiliary_prediction_explains_why(text, reason):
    result = app.predict_disease_name(text, details=True)
    assert result["abstained"] is True
    assert result["abstain_reason"] == reason
    assert result["notice"]
    assert not result["disease"]
    assert not result["predictions"]


def test_supported_prediction_is_not_labeled_abstained():
    result = app.predict_disease_name("咳嗽", details=True)
    assert result["abstained"] is False
    assert result["predictions"]


def test_api_keeps_auxiliary_reason_and_safety_priority_separate():
    client = app.app.test_client()
    ordinary = client.post("/api/v1/triage", json={"condition": "发热和咳嗽"}).get_json()["data"]
    assert ordinary["disease_prediction"]["abstain_reason"] == "unsupported_model_feature"
    emergency = client.post("/api/v1/triage", json={"condition": "持续胸痛喘不上气"}).get_json()["data"]
    assert emergency["disease_prediction"]["abstain_reason"] == "safety_gate_priority"
    pending = client.post("/api/v1/triage", json={"condition": "抽搐"}).get_json()["data"]
    assert pending["disease_prediction"]["abstain_reason"] == "safety_gate_priority"
    assert pending["disease_prediction"]["auxiliary_abstain_reason"] == "unverified_semantic_equivalence"
