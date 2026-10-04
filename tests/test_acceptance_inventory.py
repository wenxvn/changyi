import pytest
from evaluation.core_exploration.acceptance_inventory import aggregate


def source(name, expected=True, passed=True, total=1, failed=None):
    return {"name": name, "layer": "known_report_contract", "total": total, "failed": int(not passed) if failed is None else failed, "rows": [{"text": "synthetic case", "expected_known": expected, "pass": passed}]}


def test_repeated_snapshot_does_not_increase_unique_coverage():
    result = aggregate([source("first"), source("second")])
    assert result["raw_rows"] == 2
    assert result["unique_layer_texts"] == 1
    assert result["duplicate_layer_text_rows"] == 1


def test_contradictory_constraint_is_not_silently_selected():
    with pytest.raises(ValueError, match="Conflicting constraints"):
        aggregate([source("first"), source("second", expected=False)])


@pytest.mark.parametrize("bad", [source("bad-total", total=2), source("bad-pass", passed=False, failed=0)])
def test_invalid_source_counts_cannot_be_reported(bad):
    with pytest.raises(ValueError, match="mismatch"):
        aggregate([bad])


def test_negative_snapshot_survives_duplicate_merge():
    result = aggregate([source("pass"), source("fail", passed=False)])
    assert result["layers"]["known_report_contract"]["snapshot_failures"] == 1


def test_explicit_passed_count_cannot_disagree_with_rows():
    bad = dict(source("bad-passed"), passed=2)
    with pytest.raises(ValueError, match="passed count mismatch"):
        aggregate([bad])
