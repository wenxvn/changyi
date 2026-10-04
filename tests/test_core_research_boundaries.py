"""Optional research extras; CI has a separate job installing the exact versions."""
import pytest
pytest.importorskip("sklearn")
import numpy as np
from evaluation.core_exploration.study import representation, selective_curves, fit_temperature
from evaluation.core_exploration.router import guarded_prediction


@pytest.mark.parametrize("rep", ["binary", "word", "concat_char", "canonical_char", "segmented_char", "fusion_25", "fusion_50", "fusion_75"])
def test_representation_cannot_read_target_or_source(rep):
    rows = [{"symptoms": ["cough", "fever"], "disease": "A", "source": "s1"}, {"symptoms": ["itching"], "disease": "B", "source": "s2"}]
    vector = representation(rep)
    original = vector.fit_transform(rows)
    changed = vector.transform([{**row, "disease": "arbitrary_target", "source": "arbitrary_source"} for row in rows])
    assert (original != changed).nnz == 0


@pytest.mark.parametrize("status", ["EMERGENCY", "INSUFFICIENT_INFORMATION", None])
def test_safety_exit_short_circuits_before_any_model_access(status):
    result = guarded_prediction({}, {"symptoms": ["cough"]}, safety_status=status, threshold=.5)
    assert result["department"] is None
    assert result["abstained"]


def test_unvalidated_clinical_input_does_not_enter_research_predictor():
    result = guarded_prediction({}, {"symptoms": ["cough"]}, safety_status="ROUTINE", threshold=.5, input_scope="clinical_chinese")
    assert result["reason"] == "input_domain_not_validated"


def test_full_coverage_preserves_composite_accuracy():
    classes = np.array(["A", "B"])
    y = np.array(["A", "A", "B"])
    p = np.array([[.8,.2],[.2,.8],[.1,.9]])
    curve = selective_curves(y, p, p[:2], classes)
    for points in curve.values():
        assert points[0]["coverage"] == 1
        assert points[0]["accuracy"] == pytest.approx(2/3)


def test_temperature_uses_cal_only_and_preserves_order():
    from scipy.special import softmax
    logits = np.array([[2.,0.],[.1,1.],[1.5,0.]])
    t = fit_temperature(logits, np.array(["A","B","A"]), np.array(["A","B"]))
    assert t > 0
    assert np.array_equal(softmax(logits,axis=1).argmax(axis=1), softmax(logits/t,axis=1).argmax(axis=1))
