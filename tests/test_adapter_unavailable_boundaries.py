from evaluation.core_exploration.adapter_unavailable_audit import run


def test_shared_adapter_failure_does_not_change_safety_or_route():
    result = run()
    assert result["baseline_inputs"] == 8 and result["total"] == 16
    assert result["adapter_state_restored"] is True
    assert result["failed"] == 0, [row for row in result["rows"] if not row["pass"]]
