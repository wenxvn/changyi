import pytest
from evaluation.core_exploration.saved_bridge_calibration_audit import pooled_metrics


def test_empty_stratum_is_unavailable_not_perfect():
    assert pooled_metrics([], [])["accuracy"] is None
    assert pooled_metrics([], [])["pooled_ece"] is None


def test_unseen_wrong_predictions_keep_the_denominator_and_confidence():
    result = pooled_metrics([False, False], [.8, .9])
    assert result["n"] == 2 and result["accuracy"] == 0
    assert result["pooled_ece"] == pytest.approx(.85)
    assert result["wrong_confident_07_count"] == 2


def test_mismatched_denominators_are_rejected():
    with pytest.raises(ValueError):
        pooled_metrics([True], [])
