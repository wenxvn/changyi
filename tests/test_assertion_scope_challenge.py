import pytest
import app
from evaluation.core_exploration.assertion_challenge import run


def test_synthetic_assertion_scope_challenge():
    result = run()
    failures = [row for row in result["rows"] if not row["pass"]]
    assert not failures, failures


@pytest.mark.parametrize("text", ["否认有咳嗽", "没有明显的咳嗽", "咳嗽没有了", "咳嗽不确定", "曾经咳嗽", "咳嗽已经好了"])
def test_real_model_adapter_cannot_claim_disease_from_nonpositive_mentions(text):
    result = app.predict_disease_name(text, details=True)
    assert not result["normalized_symptoms"]
    assert not result["disease"]
    assert not result["predictions"]


def test_unresolved_current_symptom_is_not_discarded():
    result = app.predict_disease_name("咳嗽没有减轻", details=True)
    assert "cough" in result["normalized_symptoms"]


def test_explicit_positive_breaks_coordinated_denial():
    result = app.predict_disease_name("没有咳嗽和有头痛", details=True)
    assert result["input_assertions"]["present"] == ["headache"]
    assert result["input_assertions"]["absent"] == ["cough"]
