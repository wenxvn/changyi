"""Real adapter regressions: negative and unknown mentions are not positive."""
import app


def test_negated_chest_pain_never_reaches_model_positive_codes():
    result = app.predict_disease_name("没有胸痛，但咳嗽", details=True)
    assert "chest_pain" not in result["normalized_symptoms"]
    assert "cough" in result["normalized_symptoms"]


def test_uncertain_chest_pain_abstains_without_disease_claim():
    result = app.predict_disease_name("不确定有没有胸痛", details=True)
    assert "chest_pain" not in result["normalized_symptoms"]
    assert result["disease"] == ""
    assert not result["predictions"]


def test_overlapping_sneeze_alias_cannot_undo_negation():
    result = app.predict_disease_name("没有连续打喷嚏", details=True)
    assert "continuous_sneezing" not in result["normalized_symptoms"]


def test_positive_codes_and_original_safety_status_remain():
    result = app.predict_disease_name("咳嗽、头痛、恶心", details=True)
    assert {"cough", "headache", "nausea"} <= set(result["normalized_symptoms"])
    client = app.app.test_client()
    emergency = client.post("/api/v1/triage", json={"condition": "持续胸痛喘不上气"}).get_json()["data"]
    assert emergency["triage_status"] == "EMERGENCY"


def test_free_text_english_denial_is_not_an_explicit_code_list():
    result = app.predict_disease_name("no cough", details=True)
    assert "cough" not in result["normalized_symptoms"]
