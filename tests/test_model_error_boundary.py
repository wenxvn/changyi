from evaluation.core_exploration.model_error_boundary_audit import run


def test_public_model_error_keeps_diagnostic_internal():
    result = run()
    assert result["adapter_state_restored"] is True
    assert result["failed"] == 0, result["rows"]
