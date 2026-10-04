from evaluation.core_exploration.red_flag_question_priority_audit import run


def test_unanswered_red_flag_question_survives_question_limit():
    result = run()
    assert result["failed"] == 0, [row for row in result["rows"] if not row["pass"]]
