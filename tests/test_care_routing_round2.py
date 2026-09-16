"""Round-2 unit tests: negation, three-state features, baselines, schema."""

from __future__ import annotations

from data.symptom_disease_model.train import fit, load_dataset

from evaluation.care_routing.data_schema import (
    synthetic_example_dataset,
    validate_dataset,
)
from evaluation.care_routing.error_analysis import component_inventory
from evaluation.care_routing.inquiry_protocol import (
    predict_with_states,
    run_three_state_inquiry,
    summarize_three_state_runs,
)
from evaluation.care_routing.model_baselines import (
    build_binary_features,
    evaluate_sklearn_like,
    fit_logistic_regression,
)
from evaluation.care_routing.run_experiments import component_triple_split
from evaluation.care_routing.run_round2 import NEGATION_ALIAS_MAP, run_negation_unit_cases
from evaluation.care_routing.stopping import default_policies, policy_as_callable
from evaluation.care_routing.symptom_state import (
    SymptomState,
    features_from_present_absent,
    parse_symptom_states_from_text,
)


def test_negation_parsing_cases():
    report = run_negation_unit_cases()
    assert report["failed"] == 0, report["cases"]


def test_present_beats_absent_when_both_mentioned():
    parsed = parse_symptom_states_from_text("有胸痛，但没有胸痛", NEGATION_ALIAS_MAP)
    # Conservative: presence remains if any positive mention exists.
    assert parsed.get("chest_pain") is SymptomState.PRESENT


def test_features_omit_unknown_and_split_absent():
    features = features_from_present_absent(["fever"], ["cough"])
    assert features["fever__present"] == 1.0
    assert features["cough__absent"] == 1.0
    assert "headache__present" not in features


def test_three_state_predict_uses_absent_likelihood():
    rows = [
        {"disease": "A", "symptoms": ["s1", "s2"]},
        {"disease": "A", "symptoms": ["s1", "s3"]},
        {"disease": "B", "symptoms": ["s4", "s5"]},
        {"disease": "B", "symptoms": ["s4", "s6"]},
    ]
    model = fit(rows, alpha=1.0, min_symptom_df=1)
    with_s4 = predict_with_states(model, ["s4"], [])
    without_s4 = predict_with_states(model, [], ["s4"])
    # Declaring s4 absent should lower B relative to the s4-present case.
    assert dict(with_s4)["B"] > dict(without_s4)["B"]


def test_three_state_inquiry_records_present_and_absent():
    rows = load_dataset(
        "data/symptom_disease_model/data/disease_symptom_structured_41diseases_long.csv"
    )
    train, cal, test = component_triple_split(rows, seed=42)
    model = fit(train, alpha=1.0, min_symptom_df=2)
    run = run_three_state_inquiry(
        model,
        test[0],
        strategy="information_gain",
        initial_symptom_count=1,
        max_questions=3,
        force_questions=True,
        seed=42,
    )
    assert run["protocol"] == "three_state_simulation"
    assert run["is_synthetic_oracle"] is True
    answers = {item["answer"] for item in run["questions"]}
    assert answers <= {"present", "absent"}
    summary = summarize_three_state_runs([run])
    assert summary["cases"] == 1


def test_stopping_policies_force_fixed_n():
    policies = {p.name: p for p in default_policies(max_questions=5)}
    fixed = policies["fixed_n"]
    assert fixed.should_stop(
        entropy=0.1, confidence=0.99, margin=0.9, set_size=1, questions_asked=0
    ) is False
    assert fixed.should_stop(
        entropy=0.1, confidence=0.99, margin=0.9, set_size=1, questions_asked=5
    ) is True
    combined = policies["combined"]
    assert combined.should_stop(
        entropy=0.1, confidence=0.99, margin=0.9, set_size=1, questions_asked=1
    ) is True
    assert callable(policy_as_callable(combined))


def test_logistic_baseline_runs_on_toy_data():
    rows = [
        {"disease": "A", "symptoms": ["s1", "s2"]},
        {"disease": "A", "symptoms": ["s1", "s3"]},
        {"disease": "B", "symptoms": ["s4", "s5"]},
        {"disease": "B", "symptoms": ["s4", "s6"]},
    ]
    features = build_binary_features(rows)
    labels = [row["disease"] for row in rows]
    model = fit_logistic_regression(features, labels, epochs=30, lr=0.5, seed=0)
    report = evaluate_sklearn_like(model, features, labels)
    assert report["test_rows"] == 4
    assert report["accuracy"] >= 0.5


def test_inquiry_schema_validator():
    payload = synthetic_example_dataset()
    result = validate_dataset(payload)
    assert result["valid"] is True, result["errors"]
    bad = dict(payload)
    bad["source"] = "not_allowed"
    bad_result = validate_dataset(bad)
    assert bad_result["valid"] is False


def test_component_inventory_counts_diseases():
    rows = load_dataset(
        "data/symptom_disease_model/data/disease_symptom_structured_41diseases_long.csv"
    )
    inventory = component_inventory(rows)
    assert inventory["single_component_disease_count"] + inventory["multi_component_disease_count"] == 41
