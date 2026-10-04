from evaluation.core_exploration.uncertainty_overlap_audit import run


def test_repeated_uncertainty_cannot_be_erased_by_another_assertion():
    result = run()
    assert result["failed"] == 0, [row for row in result["rows"] if not row["pass"]]
