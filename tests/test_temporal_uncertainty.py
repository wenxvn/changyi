from evaluation.core_exploration.temporal_uncertainty_audit import run


def test_current_word_cannot_erase_uncertainty_about_that_symptom():
    result = run()
    assert result["failed"] == 0, [row for row in result["rows"] if not row["pass"]]
