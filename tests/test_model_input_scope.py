from evaluation.core_exploration.input_scope_audit import run


def test_scope_explains_partial_evidence_without_changing_admission():
    result = run()
    assert result["failed"] == 0, [row for row in result["rows"] if not row["pass"]]
