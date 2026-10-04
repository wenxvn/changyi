from evaluation.core_exploration.qualified_chest_auxiliary_audit import run


def test_qualified_chest_denial_is_reviewed_without_inventing_parent_presence():
    result = run()
    assert result["failed"] == 0, [row for row in result["rows"] if not row["pass"]]
