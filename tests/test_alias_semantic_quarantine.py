import pytest
import app


@pytest.mark.parametrize("text", ["抽搐", "抽搐和咳嗽", "尿急和咳嗽", "口渴和咳嗽", "血压高和咳嗽", "发热和咳嗽"])
def test_unverified_or_unsupported_alias_cannot_publish_learned_disease(text):
    result = app.predict_disease_name(text, details=True)
    assert not result["normalized_symptoms"]
    assert not result["disease"]
    assert not result["predictions"]
    assert result["mapping_review"]["required"]
    assert result["mapping_review"]["issues"]


def test_quarantined_alias_is_not_published_as_muscle_pain_tag():
    tags, _ = app._model_standard_symptom_tags("抽搐")
    assert not tags


def test_denied_quarantined_alias_does_not_block_genuine_muscle_pain():
    result = app.predict_disease_name("没有抽搐但肌肉痛", details=True)
    assert result["normalized_symptoms"] == ["muscle_pain"]
    assert not result["mapping_review"]["required"]


def test_specific_fever_and_existing_emergency_remain():
    result = app.predict_disease_name("高烧", details=True)
    assert "high_fever" in result["normalized_symptoms"]
    assert not result["mapping_review"]["required"]
    data = app.app.test_client().post("/api/v1/triage", json={"condition": "持续胸痛喘不上气"}).get_json()["data"]
    assert data["triage_status"] == "EMERGENCY"
