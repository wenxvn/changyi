from evaluation.core_exploration.auxiliary_route_counterfactual import run, signature


def test_controlled_auxiliary_helper_cannot_change_route_or_safety():
    result = run()
    assert result["total"] == 24 and result["baseline_inputs"] == 8
    assert result["dependency_restored"] is True
    assert result["failed"] == 0, [row for row in result["rows"] if not row["pass"]]


def test_signature_includes_explicit_routing_deferral():
    data = {"triage_status": "INSUFFICIENT_INFORMATION", "matched_department": None,
            "triage": {"defer_resource_routing": True}}
    assert signature(data)["defer_resource_routing"] is True
