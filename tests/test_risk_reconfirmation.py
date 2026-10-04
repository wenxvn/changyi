from evaluation.core_exploration.risk_reconfirmation_audit import run


def test_unknown_risk_answer_is_pending_not_a_completed_question():
    result = run()
    assert result["failed"] == 0, [row for row in result["rows"] if not row["pass"]]
