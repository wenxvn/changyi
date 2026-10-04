"""A binary answer probability uses sample frequency, not token frequency."""
import pytest
from data.symptom_disease_model.train import fit
from evaluation.care_routing.inquiry_protocol import expected_information_gain_states, predict_with_states


def test_binary_answer_probability_and_bayes_consistency():
    rows = [
        {"disease": "A", "symptoms": ["fever", "pain"]},
        {"disease": "A", "symptoms": ["fever", "pain"]},
        {"disease": "B", "symptoms": ["nausea"]},
        {"disease": "B", "symptoms": ["nausea"]},
    ]
    model = fit(rows, alpha=1., min_symptom_df=1)
    posterior = predict_with_states(model, [], [])
    answer = expected_information_gain_states(posterior, model, "fever", [], [])
    assert answer["p_yes"] == pytest.approx(.5)
    assert answer["p_yes"] + answer["p_no"] == pytest.approx(1.)
    yes = dict(predict_with_states(model, ["fever"], []))
    no = dict(predict_with_states(model, [], ["fever"]))
    assert yes["A"] == pytest.approx(.75)
    assert no["A"] == pytest.approx(.25)
    assert answer["information_gain"] >= 0
