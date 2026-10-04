import pytest
import app


@pytest.mark.parametrize("text", ["不确定是否糖尿病", "糖尿病不确定", "怀疑糖尿病", "可能糖尿病", "报告提示糖尿病但未确诊"])
def test_uncertain_disease_is_a_mention_not_known_fact(text):
    data = app.app.test_client().post("/api/v1/triage", json={"condition": text}).get_json()["data"]
    known = data["htriage_analysis"]["known_disease"]
    assert known["has_known_disease"] is False
    assert known["assertion_status"] == "uncertain"
    assert known["disease"] == "糖尿病"
    assert known["confidence"] == 0.0
    assert not any(row["primary_category"] == "用户已知疾病" for row in data["htriage_analysis"]["disease_candidates"])
    assert any(q["id"] == "known_disease_status" for q in data["triage"]["followup"]["questions"])


def test_explicit_other_confirmation_beats_uncertain_longer_name():
    assert app.detect_known_disease("怀疑糖尿病但确诊乙肝")["disease"] == "乙肝"


@pytest.mark.parametrize("value,expected", [("confirmed", True), ("option_1", True), ("report_unconfirmed", False), ("self_suspected", False)])
def test_followup_updates_reported_evidence_without_rewriting_condition(value, expected):
    text = "不确定是否糖尿病"
    data = app.app.test_client().post("/api/v1/triage", json={"condition": text, "followup_answers": [{"question_id": "known_disease_status", "value": value}]}).get_json()["data"]
    assert data["original_condition"] == text
    assert data["htriage_analysis"]["known_disease"]["has_known_disease"] is expected
    assert data["htriage_analysis"]["known_disease"]["evidence_source"] == "structured_followup"


def test_confirmation_cannot_invent_unmentioned_disease_or_downgrade_emergency():
    client = app.app.test_client()
    for text in ("咳嗽", "没有糖尿病但咳嗽"):
        data = client.post("/api/v1/triage", json={"condition": text, "followup_answers": [{"question_id": "known_disease_status", "value": "confirmed"}]}).get_json()["data"]
        assert not data["htriage_analysis"]["known_disease"]["has_known_disease"]
    data = client.post("/api/v1/triage", json={"condition": "持续胸痛喘不上气，怀疑糖尿病", "followup_answers": [{"question_id": "known_disease_status", "value": "self_suspected"}]}).get_json()["data"]
    assert data["triage_status"] == "EMERGENCY"


def test_confirmed_followup_can_refine_only_general_department_fallback():
    data = app.app.test_client().post("/api/v1/triage", json={"condition": "不确定有没有糖尿病", "followup_answers": [{"question_id": "known_disease_status", "value": "confirmed"}]}).get_json()["data"]
    assert data["matched_department"] == "内分泌代谢科"
    assert data["original_condition"] == "不确定有没有糖尿病"
