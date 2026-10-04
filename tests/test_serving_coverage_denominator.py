import pytest
from evaluation.core_exploration.serving_coverage_audit import summarize


def row(accepted, reason=None):
    return {"alias": "synthetic", "legacy_code": "synthetic_code", "text": "synthetic",
            "accepted": accepted, "abstain_reason": reason, "public_model_visible": accepted,
            "high_posterior": False, "safety_gated": False, "pass": True}


def test_abstentions_remain_in_total_and_failed_rows_are_retained():
    rows = [row(True), row(False, "unsupported_model_feature")]
    rows[1]["pass"] = False
    result = summarize(rows)
    assert result["total"] == 2 and result["accepted"] == 1 and result["abstained"] == 1
    assert result["failed"] == 1 and result["unique_texts"] == 1
    assert result["abstention_reasons"] == {"unsupported_model_feature": 1}


@pytest.mark.parametrize("bad", [row(False), row(True, "unsupported_model_feature"), dict(row(True), accepted=1), dict(row(False, "unknown"), high_posterior=True)])
def test_inconsistent_or_implicit_status_is_rejected(bad):
    with pytest.raises(ValueError):
        summarize([bad])


def test_safety_hidden_acceptance_has_separate_denominator():
    hidden = dict(row(True), public_model_visible=False, safety_gated=True)
    result = summarize([hidden, row(False, "unknown")])
    assert result["accepted_hidden_by_safety"] == 1
    assert result["public_model_visible"] == 0 and result["total"] == 2


def test_unexpected_hidden_prediction_is_not_labeled_as_safety():
    hidden = dict(row(True), public_model_visible=False, **{"pass": False})
    result = summarize([hidden])
    assert result["accepted_hidden_by_safety"] == 0
    assert result["accepted_unexpectedly_hidden"] == 1 and result["failed"] == 1
