"""Direct department classifier vs disease-first routing."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from data.symptom_disease_model.train import fit

from evaluation.model.evaluate_grouped import ALPHA, MIN_SYMPTOM_DF

from .disease_department import department_for
from .model_baselines import (
    build_binary_features,
    fit_logistic_regression,
    predict_proba,
)
from .round3_models import macro_f1, routing_error_breakdown, summarize_predictions
from .round3_split_audit import quota_split
from .uncertainty import expected_calibration_error, predict_distribution, top1_confidence


def evaluate_direct_department(
    train: Sequence[Mapping[str, Any]],
    test: Sequence[Mapping[str, Any]],
    *,
    seed: int = 42,
) -> dict[str, Any]:
    y_train = [department_for(row["disease"]) for row in train]
    y_test = [department_for(row["disease"]) for row in test]
    train_bin = build_binary_features(train)
    test_bin = build_binary_features(test)
    model = fit_logistic_regression(train_bin, y_train, epochs=60, lr=0.4, seed=seed)
    ranked_list = [predict_proba(model, feat) for feat in test_bin]
    y_pred = [ranked[0][0] if ranked else None for ranked in ranked_list]
    confidences = [top1_confidence(ranked) for ranked in ranked_list]
    ece = expected_calibration_error(
        confidences, [true == pred for true, pred in zip(y_test, y_pred)]
    )
    correct = sum(1 for t, p in zip(y_test, y_pred) if t == p)
    n = len(y_test)
    # Direct department errors are by definition cross-department (or abstain).
    return {
        "approach": "direct_department_lr",
        "accuracy": round(correct / n, 6) if n else 0.0,
        "macro_f1": macro_f1(y_test, y_pred),
        "ece": ece["ece"],
        "mean_confidence": round(sum(confidences) / n, 6) if n else 0.0,
        "department_labels": sorted(set(y_train)),
        "test_rows": n,
        "note": "product-facing care routing baseline; not a diagnosis model",
    }


def evaluate_disease_first(
    train: Sequence[Mapping[str, Any]],
    test: Sequence[Mapping[str, Any]],
    *,
    seed: int = 42,
) -> dict[str, Any]:
    y_train = [row["disease"] for row in train]
    y_test = [row["disease"] for row in test]
    train_bin = build_binary_features(train)
    test_bin = build_binary_features(test)
    model = fit_logistic_regression(train_bin, y_train, epochs=60, lr=0.4, seed=seed)
    ranked_list = [predict_proba(model, feat) for feat in test_bin]
    disease_summary = summarize_predictions(ranked_list, y_test)
    y_pred_disease = [ranked[0][0] if ranked else None for ranked in ranked_list]
    dept_true = [department_for(d) for d in y_test]
    dept_pred = [department_for(d) if d else None for d in y_pred_disease]
    dept_correct = sum(1 for t, p in zip(dept_true, dept_pred) if t == p)
    n = len(y_test)
    routing = routing_error_breakdown(y_test, y_pred_disease)
    # NB disease-first reference
    nb = fit(train, ALPHA, MIN_SYMPTOM_DF)
    nb_ranked = [predict_distribution(nb, row["symptoms"]) for row in test]
    nb_summary = summarize_predictions(nb_ranked, y_test)
    return {
        "approach": "disease_first_lr",
        "disease_accuracy": disease_summary["accuracy"],
        "department_accuracy": round(dept_correct / n, 6) if n else 0.0,
        "department_macro_f1": macro_f1(dept_true, dept_pred),
        "ece_disease": disease_summary["ece"],
        "routing_error": routing,
        "test_rows": n,
        "nb_disease_first": {
            "disease_accuracy": nb_summary["accuracy"],
            "department_accuracy": nb_summary["department_accuracy"],
            "ece": nb_summary["ece"],
        },
        "note": "disease label is research-only intermediate; UI must not present it as diagnosis",
    }


def run_hierarchical_comparison(
    rows: Sequence[Mapping[str, Any]],
    *,
    seeds: Sequence[int] = (42, 123, 2026),
    threshold: float = 0.8,
) -> dict[str, Any]:
    import statistics

    direct_runs = []
    disease_runs = []
    for seed in seeds:
        train, cal, test, meta = quota_split(rows, threshold=threshold, seed=seed)
        if not test:
            continue
        direct_runs.append(evaluate_direct_department(train, test, seed=seed))
        disease_runs.append(evaluate_disease_first(train, test, seed=seed))

    def agg(runs: Sequence[Mapping[str, Any]], key: str) -> dict[str, Any]:
        values = [float(run[key]) for run in runs if run.get(key) is not None]
        if not values:
            return {"mean": None, "std": None}
        mean = sum(values) / len(values)
        std = statistics.pstdev(values) if len(values) > 1 else 0.0
        return {"mean": round(mean, 6), "std": round(std, 6)}

    direct_dept = agg(direct_runs, "accuracy")
    disease_dept = agg(disease_runs, "department_accuracy")
    disease_acc = agg(disease_runs, "disease_accuracy")
    return {
        "protocol": "hierarchical_vs_direct",
        "threshold": threshold,
        "seeds": list(seeds),
        "direct_department_accuracy": direct_dept,
        "disease_first_department_accuracy": disease_dept,
        "disease_first_disease_accuracy": disease_acc,
        "direct_runs": direct_runs,
        "disease_first_runs": disease_runs,
        "recommendation": (
            "若 direct department accuracy ≥ disease-first department accuracy 且更稳定，"
            "则产品叙事优先 Direct Department（更贴合 Care Routing，标签更粗、样本更聚合）。"
        ),
    }
