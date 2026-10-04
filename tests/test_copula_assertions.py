import app
from evaluation.core_exploration.copula_assertion_audit import run


def test_copula_polarity_and_questions_keep_distinct_states():
    result = run()
    assert result["failed"] == 0, [row for row in result["rows"] if not row["pass"]]


def test_question_is_not_a_clear_denial_and_contrast_keeps_danger_signal():
    assert app._contains_positive("是不是胸痛", ["胸痛"]) is True
    assert app._contains_positive("不是胸痛", ["胸痛"]) is False
    assert app._contains_positive("不是咳嗽而是呼吸困难", ["呼吸困难"]) is True
    assert app._contains_positive("不是咳嗽导致胸痛", ["胸痛"]) is True
