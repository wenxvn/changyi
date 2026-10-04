import pytest
from evaluation.core_exploration.saved_selective_bridge_audit import choose_cal_threshold


def test_no_cal_solution_refuses_all_instead_of_relaxing_target():
    policy = choose_cal_threshold([.9]*15, [True]*10+[False]*5, range(15))
    assert policy["threshold"] is None and policy["status"] == "NO_ADMISSIBLE_CAL_THRESHOLD"


def test_group_minimum_prevents_template_duplicates_from_faking_sample_size():
    policy = choose_cal_threshold([.9]*30, [True]*30, [0]*30)
    assert policy["threshold"] is None


def test_maximum_cal_coverage_is_selected_without_test_inputs():
    policy = choose_cal_threshold([.8]*10+[.2]*10, [True]*10+[False]*10, range(20))
    assert policy["threshold"] == pytest.approx(.25)
