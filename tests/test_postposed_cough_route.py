import pytest
import app

@pytest.mark.parametrize("text", ["现在咳嗽是不是", "现在咳嗽说不清", "现在咳嗽是否有"])
def test_rule_fallback_cannot_recreate_uncertain_cough_evidence(text):
    analysis = app.build_htriage_analysis(text)
    assert not any(item["department"] == "呼吸内科" and item["source"] == "rule_engine"
                   for item in analysis["department_candidates"])
    assert app.match_department(text) != "呼吸内科"

def test_other_reported_symptom_keeps_its_independent_direction():
    assert app.match_department("现在咳嗽是不是，我有发烧") == app.match_department("我有发烧")

def test_known_disease_and_emergency_remain_independent():
    client = app.app.test_client()
    known = client.post("/api/v1/triage", json={"condition": "现在咳嗽是不是，我确诊糖尿病"}).get_json()["data"]
    assert known["matched_department"] == "内分泌代谢科"
    danger = client.post("/api/v1/triage", json={"condition": "现在咳嗽是不是，我喘不上气"}).get_json()["data"]
    assert danger["triage_status"] == "EMERGENCY"

def test_uncertain_rule_evidence_is_not_restored_by_model_outage(monkeypatch):
    from backend.app import composition
    monkeypatch.setattr(composition, "predict_disease_name", lambda *args, **kwargs: {})
    assert app.match_department("现在咳嗽是不是") != "呼吸内科"
