"""Explicit denials must not regain a specialist through a lexical fallback."""
import app


def test_denied_symptom_does_not_regain_specialist_direction():
    client = app.app.test_client()
    for condition in ("没有胸痛", "不确定有没有胸痛"):
        data = client.post("/api/v1/triage", json={"condition": condition}).get_json()["data"]
        assert data["matched_department"] != "心血管内科"


def test_appended_colloquial_normalization_does_not_create_positive_model_input():
    for condition in ("没有胸口疼", "没有喘不上来"):
        model = app.predict_disease_name(condition, details=True)
        assert model["normalized_symptoms"] == []


def test_coordinated_denial_does_not_assert_later_list_items():
    model = app.predict_disease_name("无发热、咳嗽和胸痛", details=True)
    assert model["normalized_symptoms"] == []


def test_positive_after_contrast_and_known_disease_route_are_preserved():
    assert app.match_department("没有发烧但咳嗽") == "呼吸内科"
    assert app.match_department("已确诊糖尿病，想复诊") == "内分泌代谢科"
    data = app.app.test_client().post("/api/v1/triage", json={"condition": "持续胸痛喘不上气"}).get_json()["data"]
    assert data["triage_status"] == "EMERGENCY"
