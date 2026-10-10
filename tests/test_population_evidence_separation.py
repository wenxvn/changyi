import pytest
import app


@pytest.mark.parametrize("text", ["儿童咳嗽", "宝宝皮肤瘙痒", "小孩皮肤科挂号", "宝宝接种疫苗", "我替宝宝咨询咳嗽"])
def test_population_word_is_not_symptom_or_disease(text):
    result = app.build_htriage_analysis(text)
    assert "儿童症状" not in {item["tag"] for item in result["symptom_tags"]}
    assert "儿童常见病/儿童急症风险" not in {item["name"] for item in result["disease_candidates"]}


@pytest.mark.parametrize("text", ["宝宝不舒服", "小孩不舒服"])
def test_population_fallback_keeps_pediatric_entry_without_fabricated_disease(text):
    result = app.build_htriage_analysis(text)
    assert app.match_department(text) == "儿科"
    candidate = next(item for item in result["department_candidates"] if item["department"] == "儿科")
    assert candidate["source"] == "population_context"
    assert candidate["score"] == 0


def test_real_cough_evidence_survives_population_separation():
    result = app.build_htriage_analysis("儿童咳嗽")
    assert any("咳嗽" in item["matched_terms"] for item in result["symptom_tags"])
    assert result["department_candidates"][0]["source"] != "population_context"


def test_emergency_and_demographic_only_controls():
    client = app.app.test_client()
    assert client.post("/api/v1/triage", json={"condition": "宝宝现在呼吸困难"}).get_json()["data"]["triage_status"] == "EMERGENCY"
    result = client.post("/api/v1/triage", json={"condition": "宝宝2个月大"}).get_json()["data"]
    assert result["triage_status"] == "INSUFFICIENT_INFORMATION"
    assert result["triage"]["department_candidates"] == []
