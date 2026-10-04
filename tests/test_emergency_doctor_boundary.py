from dataclasses import replace
import pytest
import app
from backend.app import composition
from backend.app.application.recommendation import RecommendationContext


def test_emergency_cannot_call_an_unavailable_regular_doctor_ranker():
    calls = []
    def forbidden(*args, **kwargs):
        raise AssertionError("Regular doctor ranking must not run for an emergency")
    def hospitals(*args, **kwargs):
        calls.append("hospitals")
        return [{"hospital": {"id": "synthetic"}}]
    service = replace(composition.RECOMMENDATION_APPLICATION_SERVICE,
                      enhanced_recommend_doctors=forbidden, legacy_recommend_doctors=forbidden,
                      recommend_hospitals=hospitals)
    result = service.build(RecommendationContext("我现在喘不上气", "common", None, "system", None, None),
                           enhanced=True, safety_first=True)
    assert calls == ["hospitals"]
    assert result["recommended_doctors"] == [] and len(result["recommended_hospitals"]) == 1
    assert result["weights_used"] == {}


@pytest.mark.parametrize("text,doctors", [("我现在喘不上气", False), ("我现在是否喘不上气", False),
                                        ("咳嗽", True), ("我确诊糖尿病", True)])
def test_api_regular_doctor_publication_is_status_sensitive(text, doctors):
    data = app.app.test_client().post("/api/v1/recommendations", json={"condition": text}).get_json()["data"]
    assert bool(data["recommended_doctors"]) is doctors
