from evaluation.core_exploration.hypothetical_symptom_audit import run


def test_hypothetical_auxiliary_and_published_tag_contract():
    result = run()
    assert result["failed"] == 0, [row for row in result["rows"] if not row["pass"]]
