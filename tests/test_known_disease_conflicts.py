import pytest
import app


@pytest.mark.parametrize("text", ["有糖尿病，但现在否认糖尿病", "已确诊糖尿病，但糖尿病不确定"])
def test_conflict_is_preserved_as_unconfirmed_not_known(text):
    data = app.app.test_client().post("/api/v1/triage", json={"condition": text}).get_json()["data"]
    known = data["htriage_analysis"]["known_disease"]
    assert not known["has_known_disease"]
    assert known["assertion_status"] == "conflicting"
    assert known["confidence"] == 0.0
    assert not any(row["primary_category"] == "用户已知疾病" for row in data["htriage_analysis"]["disease_candidates"])
    assert any(q["id"] == "known_disease_status" for q in data["triage"]["followup"]["questions"])


def test_misdiagnosis_then_retraction_is_not_reported_as_confirmed_history():
    assert not app.detect_known_disease("以前被误诊糖尿病，现在确认没有糖尿病")["has_known_disease"]


def test_real_history_and_different_symptom_denial_remain_reported():
    assert app.detect_known_disease("有糖尿病病史，现在没有发热")["has_known_disease"]


def test_new_self_report_can_clarify_conflict_without_rewriting_text():
    text = "已确诊糖尿病，但糖尿病不确定"
    data = app.app.test_client().post("/api/v1/triage", json={"condition": text, "followup_answers": [{"question_id": "known_disease_status", "value": "report_unconfirmed"}]}).get_json()["data"]
    assert data["original_condition"] == text
    assert not data["htriage_analysis"]["known_disease"]["has_known_disease"]
    assert data["htriage_analysis"]["known_disease"]["evidence_source"] == "structured_followup"


def test_conflicted_disease_cannot_downgrade_current_emergency():
    data = app.app.test_client().post("/api/v1/triage", json={"condition": "有糖尿病但否认糖尿病，目前我呼吸困难"}).get_json()["data"]
    assert data["triage_status"] == "EMERGENCY"
