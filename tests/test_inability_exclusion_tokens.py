import pytest
import app
from backend.app.domain.medical_input import known_disease_mention_state, contains_positive
from evaluation.core_exploration.inability_exclusion_token_audit import CASES


@pytest.mark.parametrize("text,expected", CASES)
def test_exclusion_action_negation_preserves_existing_safety_policy(text, expected):
    data = app.app.test_client().post("/api/v1/triage", json={"condition": text}).get_json()["data"]
    if expected == "NOT_EMERGENCY":
        assert data["triage_status"] != "EMERGENCY"
    else:
        assert data["triage_status"] == expected


@pytest.mark.parametrize("prefix", ["无法", "无法完全", "没能", "没有", "没能够明确"])
def test_uncompleted_exclusion_is_uncertain_not_absent_or_known(prefix):
    text = "医生" + prefix + "排除糖尿病"
    assert known_disease_mention_state(text, "糖尿病") == "uncertain"
    assert not app.detect_known_disease(text)["has_known_disease"]


@pytest.mark.parametrize("text", ["医生无法排除肺炎，我没有心梗", "医生没能排除肺炎，我无心梗",
                                "没有心梗", "无心梗", "医生没有排除肺炎，但没有心梗"])
def test_actual_disease_denial_still_excludes_the_signal(text):
    assert not contains_positive(text, ["心梗"])
