from evaluation.core_exploration.chest_alias_audit import run


def test_unverified_chest_alias_does_not_create_model_breathlessness():
    result = run()
    assert result["failed"] == 0, [row for row in result["rows"] if not row["pass"]]
