from evaluation.core_exploration.hypothetical_risk_audit import run


def test_explicit_hypothetical_cue_requires_confirmation_not_a_current_report():
    result = run()
    assert result["failed"] == 0, [row for row in result["rows"] if not row["pass"]]
