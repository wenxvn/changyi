from evaluation.core_exploration.candidate_evidence_audit import run


def test_candidate_evidence_matches_assertion_state():
    result = run()
    assert result["failed"] == 0, [row for row in result["rows"] if not row["pass"]]
