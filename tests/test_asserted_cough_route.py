import pytest
import app

@pytest.mark.parametrize("text", ["现在是否咳嗽", "现在可能咳嗽", "现在不确定是否咳嗽"])
def test_unknown_cough_does_not_establish_respiratory_route(text):
    assert app.match_department(text) != "呼吸内科"

@pytest.mark.parametrize("text", ["现在有咳嗽", "现在不确定为什么咳嗽", "没有胸痛，现在咳嗽"])
def test_reported_cough_keeps_route(text):
    assert app.match_department(text) == "呼吸内科"

def test_route_assertion_is_independent_of_model_availability(monkeypatch):
    from backend.app import composition
    monkeypatch.setattr(composition, "predict_disease_name", lambda *args, **kwargs: {})
    assert app.match_department("现在是否咳嗽") != "呼吸内科"
    assert app.match_department("现在有咳嗽") == "呼吸内科"
