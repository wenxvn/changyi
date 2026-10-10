import pytest
import app
from backend.app.domain.triage.asthma_review import asthma_rescue_context

CONDITION = "我有哮喘。过去12小时一直喘鸣、胸部发紧。我用了4次急救吸入器，每次只有稍微帮助，症状又回来。仍能说完整句子。"


def payload(value=None, condition=CONDITION):
    d = {"condition": condition}
    if value:
        d["followup_answers"] = [{"question_id": "asthma_rescue_check", "value": value}]
    return d


@pytest.mark.parametrize("value", [None, "unknown", "unsupported"])
def test_uncertain_rescue_response_is_pending_before_ordinary_routing(value):
    c = app.app.test_client()
    d = c.post("/api/v1/triage", json=payload(value)).get_json()["data"]
    assert d["triage_status"] == "INSUFFICIENT_INFORMATION"
    assert d["matched_department"] is None
    assert d["triage"]["followup"]["questions"][0]["id"] == "asthma_rescue_check"
    r = c.post("/api/v1/recommendations", json=payload(value)).get_json()["data"]
    assert r["recommended_doctors"] == [] and r["recommended_hospitals"] == []


def test_general_none_cannot_clear_unknown_specific_response():
    p = payload("unknown")
    p["followup_answers"].append({"question_id": "red_flag_check", "value": "none"})
    d = app.app.test_client().post("/api/v1/triage", json=p).get_json()["data"]
    assert d["triage_status"] == "INSUFFICIENT_INFORMATION"


def test_specific_present_uses_emergency_exit_and_none_still_needs_timely_assessment():
    c = app.app.test_client()
    er = c.post("/api/v1/triage", json=payload("present")).get_json()["data"]
    assert er["triage_status"] == "EMERGENCY" and not er["disease_prediction"]["predictions"]
    urgent = c.post("/api/v1/recommendations", json=payload("none")).get_json()["data"]
    assert urgent["triage"]["level"] == "urgent"
    assert urgent["resource_strategy"]["code"] == "urgent_assessment"
    assert urgent["recommended_doctors"] == []


def test_four_uses_do_not_claim_maximum_but_explicit_plan_failure_is_distinct():
    assert not asthma_rescue_context(CONDITION)["explicit_maximum_failure"]
    text = "我有哮喘，现在一直喘鸣胸部发紧。我按个人方案最大剂量使用急救吸入器，仍没有缓解。"
    assert asthma_rescue_context(text)["explicit_maximum_failure"]
    assert app.app.test_client().post("/api/v1/triage", json=payload(condition=text)).get_json()["data"]["triage_status"] == "EMERGENCY"


@pytest.mark.parametrize("text", ["哮喘复诊开药", "我有哮喘，但没有喘鸣胸闷，曾用急救吸入器",
                                "以前哮喘喘鸣用急救吸入器没好，现在全好了", "如果哮喘一直喘鸣用急救吸入器会怎样",
                                "我妈有哮喘，我现在喘鸣，急救吸入器后一直不缓解"])
def test_noncurrent_denied_hypothetical_or_mixed_subject_does_not_create_a_review(text):
    assert asthma_rescue_context(text) is None


def test_clear_breathing_emergency_precedes_a_negative_specific_answer():
    d = app.app.test_client().post("/api/v1/triage", json=payload("none", CONDITION + "我现在喘不上气")).get_json()["data"]
    assert d["triage_status"] == "EMERGENCY"
