"""Unit tests for offline care-routing experiments (no Flask, no Safety change)."""

from __future__ import annotations

import math

from data.symptom_disease_model.train import fit, load_dataset

from evaluation.care_routing.disease_department import DISEASE_TO_DEPARTMENT, department_for
from evaluation.care_routing.inquiry import (
    class_conditional_symptom_probs,
    expected_information_gain,
    run_adaptive_inquiry,
    select_information_gain_question,
)
from evaluation.care_routing.metrics import evaluate_uncertainty_split, summarize_inquiry_runs
from evaluation.care_routing.uncertainty import (
    build_uncertainty_payload,
    conformal_threshold,
    distribution_entropy,
    fit_temperature,
    predict_distribution,
    should_clarify,
    softmax_with_temperature,
    top1_confidence,
)


def _toy_model():
    rows = [
        {"disease": "A", "symptoms": ["s1", "s2", "s3"]},
        {"disease": "A", "symptoms": ["s1", "s2", "s4"]},
        {"disease": "B", "symptoms": ["s5", "s6", "s7"]},
        {"disease": "B", "symptoms": ["s5", "s6", "s8"]},
        {"disease": "C", "symptoms": ["s1", "s5", "s9"]},
        {"disease": "C", "symptoms": ["s1", "s5", "s10"]},
    ]
    return fit(rows, alpha=1.0, min_symptom_df=1), rows


def test_department_map_covers_all_model_labels():
    disease_name_map = {
        "(vertigo) Paroymsal Positional Vertigo": "良性阵发性位置性眩晕",
        "Heart attack": "心肌梗死",
        "Pneumonia": "肺炎",
        "Acne": "痤疮",
    }
    assert department_for("Heart attack") == "心血管内科"
    assert department_for("Pneumonia") == "呼吸与危重症医学科"
    assert department_for("Unknown Disease") == "全科医学科"
    assert len(DISEASE_TO_DEPARTMENT) == 41


def test_entropy_and_confidence_basics():
    uniform = [("a", 0.25), ("b", 0.25), ("c", 0.25), ("d", 0.25)]
    assert math.isclose(distribution_entropy(uniform), 2.0, rel_tol=1e-6)
    peaked = [("a", 0.9), ("b", 0.05), ("c", 0.05)]
    assert top1_confidence(peaked) == 0.9
    assert distribution_entropy(peaked) < 1.0


def test_temperature_softens_distribution():
    scores = {"a": 5.0, "b": 1.0, "c": 0.0}
    sharp = softmax_with_temperature(scores, temperature=0.5)
    soft = softmax_with_temperature(scores, temperature=2.0)
    assert sharp[0][1] > soft[0][1]
    assert math.isclose(sum(p for _, p in sharp), 1.0, rel_tol=1e-6)


def test_should_clarify_thresholds():
    assert should_clarify(
        entropy=0.2, confidence=0.9, set_size=1, max_entropy=4.0
    ) is False
    assert should_clarify(
        entropy=3.5, confidence=0.3, set_size=8, max_entropy=4.0
    ) is True


def test_temperature_fit_reduces_or_equals_nll():
    model, rows = _toy_model()
    result = fit_temperature(model, rows)
    assert result["temperature"] > 0
    assert result["nll"] is not None
    assert result["evaluated_rows"] == len(rows)


def test_conformal_threshold_and_payload():
    model, rows = _toy_model()
    conformal = conformal_threshold(model, rows, alpha=0.2, temperature=1.0)
    assert 0.0 <= conformal["threshold"] <= 1.0
    ranked = predict_distribution(model, ["s1", "s2"])
    payload = build_uncertainty_payload(
        ranked,
        disease_name_map={},
        department_for=department_for,
        conformal=conformal,
    )
    assert payload["should_clarify"] in (True, False)
    assert payload["not_medical_confidence"] is True
    assert "disclaimer" in payload
    assert payload["probability_distribution"]


def test_information_gain_prefers_discriminative_symptom():
    model, _ = _toy_model()
    symptom_probs = class_conditional_symptom_probs(model)
    posterior = predict_distribution(model, ["s1"])  # uncertain between A and C
    metrics = expected_information_gain(posterior, symptom_probs, "s2")
    assert metrics["information_gain"] >= 0.0
    choice = select_information_gain_question(model, ["s1"], symptom_probs)
    assert choice is not None
    assert choice["symptom"] not in {"s1"}


def test_adaptive_inquiry_uses_oracle_answers_without_inventing_them():
    model, _ = _toy_model()
    row = {"disease": "A", "symptoms": ["s1", "s2", "s3", "s4"]}
    run = run_adaptive_inquiry(
        model,
        row,
        strategy="information_gain",
        initial_symptom_count=1,
        max_questions=3,
        force_questions=True,
    )
    assert run["skipped"] is False
    assert run["protocol"].startswith("held-out labeled symptom set")
    for question in run["questions"]:
        assert question["answer"] in {"yes", "no"}
        if question["answer"] == "yes":
            assert question["question_symptom"] in row["symptoms"]


def test_summarize_inquiry_runs_handles_empty():
    summary = summarize_inquiry_runs([])
    assert summary["cases"] == 0
    assert summary["average_questions"] is None


def test_evaluate_uncertainty_split_smoke():
    model, rows = _toy_model()
    report = evaluate_uncertainty_split(model, rows, temperature=1.0)
    assert report["test_rows"] == len(rows)
    assert 0.0 <= report["accuracy"] <= 1.0
    assert report["ece"] is not None
    assert report["department_accuracy"] is not None


def test_real_dataset_smoke():
    rows = load_dataset(
        "data/symptom_disease_model/data/disease_symptom_structured_41diseases_long.csv"
    )
    assert len(rows) == 304
    model = fit(rows[:200], alpha=1.0, min_symptom_df=2)
    ranked = predict_distribution(model, rows[200]["symptoms"])
    assert ranked
    assert math.isclose(sum(p for _, p in ranked), 1.0, rel_tol=1e-6)
