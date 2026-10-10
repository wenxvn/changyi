import pytest
import app
from backend.app.domain.triage.contextual_urgency import contextual_urgent_assessment


POSITIVE = (
    "左小腿肿胀、疼痛两天", "右腿疼痛而且肿胀", "我现在一侧小腿肿胀疼痛",
    "排尿灼痛两天，现在有左侧背部、腰侧疼痛和发热", "我发烧、腰痛和尿痛", "尿痛腰侧痛发热，还有恶心",
)
NEGATIVE = (
    "左小腿肿胀，没有疼痛", "没有左小腿肿胀疼痛", "以前左小腿肿胀疼痛，现在好了",
    "左小腿肿胀好了，现在左小腿疼痛", "如果左小腿肿胀疼痛怎么办", "不确定是否左小腿肿胀疼痛",
    "左小腿肿胀，右小腿疼痛", "左小腿肿胀，头部疼痛", "我左小腿肿胀，我妈左小腿疼痛",
    "没有尿痛，腰痛发热", "尿痛腰痛，没有发热", "以前尿痛，现在腰痛发热",
    "尿痛已经好了，现在腰痛发热", "如果有尿痛腰痛发热怎么办", "不确定是否尿痛腰痛发热",
    "我尿痛，我妈腰痛发热", "尿痛发热", "腰痛发热", "双腿肿胀疼痛",
)


@pytest.mark.parametrize("text", POSITIVE)
def test_current_compound_risk_needs_timely_assessment_and_direction(text):
    assert contextual_urgent_assessment(text)
    d = app.app.test_client().post("/api/v1/triage", json={"condition": text}).get_json()["data"]
    assert d["triage_status"] == "URGENT"
    assert d["matched_department"] == "急诊医学科"
    assert "尽快" in d["triage"]["care_level"]


@pytest.mark.parametrize("text", NEGATIVE)
def test_denied_historical_hypothetical_or_mixed_evidence_does_not_create_a_compound_rule(text):
    assert contextual_urgent_assessment(text) is None


def test_true_emergency_still_precedes_the_new_urgent_rule():
    d = app.app.test_client().post("/api/v1/triage", json={"condition": "左小腿肿胀疼痛，呼吸困难"}).get_json()["data"]
    assert d["triage_status"] == "EMERGENCY"
    assert not d["disease_prediction"]["predictions"]


@pytest.mark.parametrize("preference", ["system", "must_expert", "no_expert"])
def test_acute_assessment_cannot_become_a_chronic_expert_booking(preference):
    d = app.app.test_client().post("/api/v1/recommendations", json={
        "condition": "尿痛腰侧痛发热", "expert_preference": preference}).get_json()["data"]
    assert d["resource_strategy"]["code"] == "urgent_assessment"
    assert not d["resource_strategy"]["expert_enabled"]
    assert d["recommended_doctors"] == []
    assert d["weights_used"] == {}
    assert "不能等待普通预约" in d["ranking_notice"]


def test_unavailable_regular_rankers_do_not_block_urgent_assessment():
    from dataclasses import replace
    from backend.app import composition
    from backend.app.application.recommendation import RecommendationContext
    def forbidden(*args, **kwargs):
        raise AssertionError("Ordinary ranking must not run for acute assessment")
    service = replace(composition.RECOMMENDATION_APPLICATION_SERVICE,
                      enhanced_recommend_doctors=forbidden, legacy_recommend_doctors=forbidden,
                      recommend_hospitals=lambda *args, **kwargs: [{"hospital": {"id": "synthetic"}}])
    d = service.build(RecommendationContext("左小腿肿胀疼痛", "common", None, "must_expert", None, None),
                      enhanced=True, safety_first=True)
    assert d["recommended_doctors"] == []
    assert len(d["recommended_hospitals"]) == 1
