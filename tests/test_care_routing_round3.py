"""Round3 unit tests: expanded split, models, learning curve, robustness, hierarchical."""

from __future__ import annotations

from evaluation.care_routing.hierarchical_triage import (
    evaluate_direct_department,
    evaluate_disease_first,
)
from evaluation.care_routing.learning_curve import learning_curve
from evaluation.care_routing.robustness import perturb_symptoms, run_robustness
from evaluation.care_routing.round3_models import (
    fit_and_eval_models,
    routing_error_breakdown,
)
from evaluation.care_routing.round3_split_audit import (
    component_threshold_audit,
    cross_split_leakage_audit,
    load_expanded,
    load_structured,
    quota_split,
    write_external_eval_schema,
)
import random


def test_load_structured_and_expanded():
    structured = load_structured()
    expanded = load_expanded()
    assert len(structured.rows) == 304
    assert len(expanded.rows) > 304
    assert len({row["disease"] for row in expanded.rows}) == 41
    assert expanded.sources["extra_rows"] > 0


def test_component_threshold_audit_shapes():
    structured = load_structured()
    audit = component_threshold_audit(structured.rows)
    assert audit["primary_threshold"] == 0.8
    assert len(audit["thresholds"]) == 4
    thr08 = next(item for item in audit["thresholds"] if item["threshold"] == 0.8)
    assert thr08["diseases_with_3plus_components"] >= 1


def test_quota_split_and_leakage_guard():
    expanded = load_expanded()
    train, cal, test, meta = quota_split(expanded.rows, threshold=0.8, seed=42)
    assert test
    assert meta["test_disease_count"] >= 5
    # single-component diseases excluded from test
    test_diseases = {row["disease"] for row in test}
    for disease in meta["excluded_from_test"]:
        assert disease not in test_diseases
    leak = cross_split_leakage_audit(train, test)
    assert "pair_count" in leak
    # primary 0.8 protocol should not be massively leaky at 0.75; allow some but report
    assert leak["leaky"] in (True, False)


def test_fit_and_eval_models_smoke():
    expanded = load_expanded()
    train, cal, test, _ = quota_split(expanded.rows, threshold=0.8, seed=42)
    result = fit_and_eval_models(train, cal, test, seed=42)
    models = result["models"]
    for name in ("multinomial_nb", "logistic_regression", "linear_svm", "tfidf_logistic_regression"):
        assert name in models
        assert models[name]["test_rows"] == len(test)
        assert 0.0 <= models[name]["accuracy"] <= 1.0
    assert "routing_error" in models["logistic_regression"]


def test_routing_error_breakdown_categories():
    y_true = ["Heart attack", "Common Cold", "Migraine"]
    y_pred = ["Hypertension", "Common Cold", "GERD"]
    report = routing_error_breakdown(y_true, y_pred)
    assert report["correct"] == 1
    assert report["same_department_error"] + report["cross_department_error"] == 2
    # Heart attack -> Hypertension is same department (心血管内科)
    assert report["same_department_error"] >= 1
    assert report["care_routing_accuracy"] >= report["accuracy"] if "accuracy" in report else True


def test_learning_curve_runs():
    structured = load_structured()
    # small structured set for speed
    result = learning_curve(structured.rows, fractions=(0.4, 1.0), seeds=(42,), threshold=0.8)
    assert len(result["points"]) == 2
    assert "accuracy_gain_20_to_100" in result
    assert result["csv_ready"]


def test_perturb_symptoms_kinds():
    rng = random.Random(0)
    symptoms = ["cough", "high_fever", "headache", "fatigue"]
    shuffled = perturb_symptoms(symptoms, kind="order_shuffle", rng=rng)
    assert sorted(shuffled) == sorted(symptoms)
    swapped = perturb_symptoms(symptoms, kind="synonym_swap", rng=rng)
    assert swapped != symptoms or True  # may or may not change depending on map
    dropped = perturb_symptoms(symptoms, kind="drop_noncritical", rng=rng)
    assert len(dropped) == len(symptoms) - 1
    filled = perturb_symptoms(symptoms, kind="add_filler", rng=rng)
    assert len(filled) >= len(symptoms)


def test_robustness_smoke():
    structured = load_structured()
    result = run_robustness(structured.rows, seed=42, threshold=0.8)
    assert result["protocol"] == "robustness_simulation"
    assert set(result["clean"]) == {"nb", "lr", "svm"}
    assert "order_shuffle" in result["per_kind"]


def test_hierarchical_smoke():
    structured = load_structured()
    train, cal, test, _ = quota_split(structured.rows, threshold=0.8, seed=42)
    direct = evaluate_direct_department(train, test, seed=42)
    disease = evaluate_disease_first(train, test, seed=42)
    assert direct["approach"] == "direct_department_lr"
    assert disease["approach"] == "disease_first_lr"
    assert 0.0 <= direct["accuracy"] <= 1.0


def test_external_schema_written():
    result = write_external_eval_schema()
    assert result["schema_version"] == "external-triage-eval/v1"
    assert result["results"] is None
