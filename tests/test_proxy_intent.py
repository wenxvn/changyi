import pytest
import app


@pytest.mark.parametrize("verb", ["替", "代替", "帮"])
def test_explicit_proxy_keeps_the_relative_disease(verb):
    text = f"我现在{verb}我妈妈问诊她确诊糖尿病"
    known = app.detect_known_disease(text)
    assert known["has_known_disease"]
    assert known["disease"] == "糖尿病"


@pytest.mark.parametrize("verb", ["替", "代", "帮"])
def test_denied_proxy_does_not_assign_family_disease_to_self(verb):
    text = f"我妈妈确诊糖尿病，我现在不是{verb}她问，是我咳嗽"
    data = app.app.test_client().post("/api/v1/triage", json={"condition": text}).get_json()["data"]
    assert not data["htriage_analysis"]["known_disease"]["has_known_disease"]
    assert data["matched_department"] != "内分泌代谢科"


def test_later_current_self_can_replace_proxy_intent():
    assert not app.detect_known_disease("我现在替妈妈问糖尿病，后来我自己咳嗽")["has_known_disease"]


def test_proxy_intent_does_not_hide_current_emergency():
    data = app.app.test_client().post("/api/v1/triage", json={"condition": "我现在替我妈妈问诊她正在呼吸困难"}).get_json()["data"]
    assert data["triage_status"] == "EMERGENCY"
