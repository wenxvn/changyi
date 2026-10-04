import pytest
import app
from backend.app.domain.medical_input import known_disease_mention_state, contains_positive
from evaluation.core_exploration.exclusion_scope_fact_audit import CASES


@pytest.mark.parametrize("text,known,state,status", CASES[2:])
def test_failure_to_exclude_is_not_a_negative_disease_report(text, known, state, status):
    word = "心梗" if "心梗" in text else "糖尿病"
    assert known_disease_mention_state(text, word) == state
    assert app.detect_known_disease(text)["has_known_disease"] is known
    if status:
        data = app.app.test_client().post("/api/v1/triage", json={"condition": text}).get_json()["data"]
        assert data["triage_status"] == status


def test_real_later_denial_is_not_erased_by_an_earlier_exclusion_phrase():
    assert not contains_positive("医生未能排除肺炎，我没有心梗", ["心梗"])


def test_past_exclusion_concern_is_not_made_a_current_emergency():
    data = app.app.test_client().post("/api/v1/triage", json={"condition": "去年未能排除心梗，现在我咳嗽"}).get_json()["data"]
    assert data["triage_status"] != "EMERGENCY"
