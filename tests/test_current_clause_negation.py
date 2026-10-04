import pytest

from backend.app.domain.medical_input import contains_positive
from evaluation.core_exploration.current_clause_negation_audit import CASES


@pytest.mark.parametrize("text,expected", CASES)
def test_current_clause_cough_evidence(text, expected):
    assert contains_positive(text, ["咳嗽"]) is expected


@pytest.mark.parametrize("text,expected", [
    ("没有胸痛，现在我没有咳嗽", False),
    ("没有胸痛， 我现在咳嗽", True),
    ("没有胸痛、咳嗽", False),
    ("没有胸痛，咳嗽", False),
    ("没有发烧，目前没有呼吸困难", False),
    ("没有发烧，目前呼吸困难", True),
])
def test_current_clause_preserves_local_and_coordinated_denial(text, expected):
    word = "呼吸困难" if "呼吸困难" in text else "咳嗽"
    assert contains_positive(text, [word]) is expected
