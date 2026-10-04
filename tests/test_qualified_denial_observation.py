import pytest
from evaluation.core_exploration.qualified_denial_observation import summarize


def row():
    return {"rule_positive": False, "aux_code_present": True, "layer_disagreement": True,
            "execution_valid": True, "clinical_label_verified": False, "group": "synthetic"}


def test_disagreement_is_not_clinical_accuracy_or_execution_failure():
    result = summarize([row(), dict(row(), execution_valid=False)])
    assert result["total"] == 2 and result["failed"] == 1
    assert result["layer_disagreements"] == 2 and result["clinical_accuracy"] is None
    assert result["clinical_verified_rows"] == 0


@pytest.mark.parametrize("value", [dict(row(), rule_positive=0), dict(row(), layer_disagreement=False)])
def test_untyped_or_misreported_comparison_is_rejected(value):
    with pytest.raises(ValueError):
        summarize([value])
