import pytest
from backend.app.domain.medical_input import known_disease_mention_state
from evaluation.core_exploration.postposed_disease_audit import run


def test_fixed_postposed_report_contract():
    result = run()
    assert result["failed"] == 0, [row for row in result["rows"] if not row["pass"]]


@pytest.mark.parametrize("text, expected", [
    ("糖尿病只是一个假设", "uncertain"),
    ("糖尿病是假设的情况", "uncertain"),
    ("糖尿病只是举例", "uncertain"),
    ("糖尿病仅是一种假想情况", "uncertain"),
    ("已确诊糖尿病，假设发热怎么办", "asserted"),
    ("已确诊糖尿病，但糖尿病只是举例", "conflicting"),
    ("糖尿病已经确诊，如果发热怎么办", "asserted"),
    ("糖尿病不是假设，已经确诊", "asserted"),
])
def test_hypothesis_predicate_is_local(text, expected):
    assert known_disease_mention_state(text, "糖尿病") == expected
