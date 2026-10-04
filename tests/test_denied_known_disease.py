import pytest
import app


@pytest.mark.parametrize("disease,department", [("糖尿病", "内分泌代谢科"), ("乙肝", "感染性疾病科"), ("类风湿关节炎", "风湿免疫科")])
@pytest.mark.parametrize("denial", ["没有", "否认", "无"])
def test_denied_disease_is_not_published_as_known_or_selected_direction(disease, department, denial):
    text = f"{denial}{disease}但有咳嗽"
    data = app.app.test_client().post("/api/v1/triage", json={"condition": text}).get_json()["data"]
    known = data["htriage_analysis"]["known_disease"]
    assert not known["has_known_disease"]
    assert data["matched_department"] != department
    assert not any(item["name"] == disease and item["source"] == "user_stated" for item in data["htriage_analysis"]["disease_candidates"])


def test_confirmed_other_disease_wins_over_denied_longer_name():
    known = app.detect_known_disease("没有糖尿病但确诊乙肝")
    assert known["has_known_disease"]
    assert known["disease"] == "乙肝"


@pytest.mark.parametrize("text", ["已经确诊糖尿病，来复诊", "有糖尿病病史，来复诊"])
def test_real_positive_history_is_preserved(text):
    known = app.detect_known_disease(text)
    assert known["has_known_disease"]
    assert known["disease"] == "糖尿病"


def test_current_emergency_is_not_downgraded_by_denied_disease():
    data = app.app.test_client().post("/api/v1/triage", json={"condition": "没有糖尿病，但持续胸痛喘不上气"}).get_json()["data"]
    assert data["triage_status"] == "EMERGENCY"


@pytest.mark.parametrize("text", ["我无力，已确诊糖尿病来复诊", "我没力气，已确诊糖尿病", "我没有发热，确诊糖尿病"])
def test_explicit_confirmation_in_its_own_clause_is_not_negated_by_other_symptom(text):
    assert app.detect_known_disease(text)["disease"] == "糖尿病"
