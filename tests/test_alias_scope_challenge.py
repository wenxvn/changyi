import pytest
import app
from evaluation.core_exploration.alias_scope_challenge import run


def test_full_alias_scope_engineering_challenge():
    result = run()
    failures = [row for row in result["rows"] if not row["pass"]]
    assert not failures, failures


@pytest.mark.parametrize("text", ["咳嗽和头痛都没有", "咳嗽和头痛都不确定"])
def test_postposed_scope_cannot_publish_disease(text):
    result = app.predict_disease_name(text, details=True)
    assert not result["normalized_symptoms"]
    assert not result["disease"]
    assert not result["predictions"]


def test_uncertain_first_mention_does_not_erase_explicit_later_positive():
    result = app.predict_disease_name("不确定是否咳嗽但有头痛", details=True)
    assert result["input_assertions"]["present"] == ["headache"]
    assert result["input_assertions"]["unknown"] == ["cough"]
    # The adapter still defers the whole learned claim while an input is unknown.
    assert not result["disease"]


@pytest.mark.parametrize("ending", ["都没有减轻", "都没有好"])
def test_unresolved_coordinated_symptoms_remain_current(ending):
    result = app.predict_disease_name(f"咳嗽和头痛{ending}", details=True)
    assert result["input_assertions"]["present"] == ["cough", "headache"]
    assert not result["input_assertions"]["absent"]
