import pytest
import app
from evaluation.core_exploration.qualified_symptom_input_audit import CASES


@pytest.mark.parametrize("text,present,unknown,review", CASES)
def test_parent_symptom_is_not_inferred_from_qualified_denial(text, present, unknown, review):
    p = app.predict_disease_name(text, details=True)
    assert p["input_assertions"]["present"] == present
    assert p["input_assertions"]["unknown"] == unknown
    assert p["input_scope_review"]["required"] is review
    if review:
        assert p["abstained"]
        assert p["abstain_reason"] == "qualified_negation_scope_unverified"
        assert not p["predictions"]


@pytest.mark.parametrize("text", ["尿频", "尿频和咳嗽", "我有尿频，但没有尿痛"])
def test_urinary_frequency_does_not_establish_high_urine_volume(text):
    p = app.predict_disease_name(text, details=True)
    assert p["mapping_review"]["required"]
    assert p["abstained"]
    assert p["abstain_reason"] == "unverified_semantic_equivalence"
    assert not p["predictions"]


def test_denied_frequency_does_not_block_independent_cough():
    p = app.predict_disease_name("没有尿频，咳嗽", details=True)
    assert not p["mapping_review"]["required"]
    assert p["input_assertions"]["present"] == ["cough"]
    assert not p["abstained"]


def test_qualified_auxiliary_review_does_not_suppress_a_real_emergency():
    d = app.app.test_client().post("/api/v1/triage", json={"condition": "持续胸痛喘不上气，没有严重头痛"}).get_json()["data"]
    assert d["triage_status"] == "EMERGENCY"
    assert not d["disease_prediction"]["predictions"]
