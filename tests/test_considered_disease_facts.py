import pytest
import app


@pytest.mark.parametrize("prefix", ["医生考虑", "报告考虑", "医生说考虑", "医生考虑为", "医生考虑是"])
def test_considered_disease_is_an_unconfirmed_mention(prefix):
    fact = app.detect_known_disease(prefix + "糖尿病")
    assert fact["has_known_disease"] is False
    assert fact["disease"] == "糖尿病"
    assert fact["source"] == "unconfirmed_mention"


@pytest.mark.parametrize("text", ["我已确诊糖尿病", "我已确诊糖尿病，考虑调整饮食", "我考虑了确诊糖尿病后的饮食"])
def test_non_disease_consideration_does_not_erase_the_reported_diagnosis(text):
    assert app.detect_known_disease(text)["has_known_disease"] is True


def test_another_confirmed_disease_precedes_the_considered_mention():
    analysis = app.build_htriage_analysis("医生考虑糖尿病，但我已确诊乙肝")
    assert analysis["known_disease"]["disease"] == "乙肝"
    assert not any(candidate["name"] == "糖尿病" and candidate["source"] == "user_stated"
                   for candidate in analysis["disease_candidates"])


def test_existing_emergency_priority_is_not_decided_by_known_disease_certainty():
    data = app.app.test_client().post("/api/v1/triage", json={"condition": "医生考虑心梗"}).get_json()["data"]
    assert data["triage_status"] == "EMERGENCY"
