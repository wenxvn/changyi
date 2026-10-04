import pytest
import app


@pytest.mark.parametrize("text", ["我妈妈确诊糖尿病现在我咳嗽", "我爸爸确诊糖尿病目前我咳嗽"])
def test_same_sentence_relative_disease_does_not_belong_to_current_self(text):
    data = app.app.test_client().post("/api/v1/triage", json={"condition": text}).get_json()["data"]
    assert not data["htriage_analysis"]["known_disease"]["has_known_disease"]
    assert "糖尿病" in data["htriage_analysis"]["known_disease"]["background_mentions"]
    assert data["matched_department"] != "内分泌代谢科"


def test_own_disease_keeps_its_evidence_in_same_sentence():
    known = app.detect_known_disease("我确诊乙肝我妈妈确诊糖尿病现在我自己来复诊")
    assert known["disease"] == "乙肝"


def test_other_symptoms_word_is_not_a_relative_pronoun():
    assert app.match_department("我自己其他症状是咳嗽") == app.match_department("咳嗽")


def test_proxy_and_bystander_emergency_controls():
    assert app.detect_known_disease("我现在帮我妈妈咨询她确诊糖尿病")["has_known_disease"]
    data = app.app.test_client().post("/api/v1/triage", json={"condition": "我妈妈正在呼吸困难现在我咳嗽"}).get_json()["data"]
    assert data["triage_status"] == "EMERGENCY"
