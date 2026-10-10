import pytest
import app
from backend.app.domain.medical_input import contains_positive, seizure_review_mentions
from evaluation.core_exploration.negative_predicate_scope_audit import CASES


@pytest.mark.parametrize("text,emergency,seizure", CASES)
def test_denied_predicate_does_not_recreate_a_safety_signal(text, emergency, seizure):
    assert bool(seizure_review_mentions(text)) is seizure
    if emergency is not None:
        d = app.app.test_client().post("/api/v1/triage", json={"condition": text}).get_json()["data"]
        assert (d["triage_status"] == "EMERGENCY") is emergency


@pytest.mark.parametrize("text,word", [("我不伴胸痛", "胸痛"), ("我不伴呼吸困难", "呼吸困难"),
                                      ("我未出现呼吸困难", "呼吸困难"), ("我没有出现呼吸困难", "呼吸困难"),
                                      ("我不是没有咳嗽，但没有呼吸困难", "呼吸困难")])
def test_shared_denial_predicate_scope(text, word):
    assert not contains_positive(text, [word])


def test_actual_later_breathing_report_and_double_denial_remain_positive():
    assert contains_positive("我不伴胸痛，但呼吸困难", ["呼吸困难"])
    assert contains_positive("我不是没有呼吸困难", ["呼吸困难"])


def test_auxiliary_or_coordination_is_absent_not_a_present_seizure():
    p = app.predict_disease_name("我没有咳嗽或抽搐，但有头痛", details=True)
    assert "muscle_pain" not in p["input_assertions"]["present"]
    assert not p["mapping_review"]["required"]
