"""Unified multi-seed model comparison for Round3 (NB vs LR vs SVM vs TF-IDF)."""

from __future__ import annotations

import json
import math
import statistics
import time
from collections import Counter, defaultdict
from typing import Any, Callable, Mapping, Sequence

from data.symptom_disease_model.train import fit, load_dataset

from evaluation.model.evaluate_grouped import ALPHA, MIN_SYMPTOM_DF

from .disease_department import department_for
from .model_baselines import (
    build_binary_features,
    build_tfidf_features,
    decision_scores,
    evaluate_sklearn_like,
    fit_linear_svm,
    fit_logistic_regression,
    predict_proba,
    softmax_from_scores,
)
from .round3_split_audit import load_expanded, load_structured, quota_split
from .uncertainty import (
    distribution_entropy,
    expected_calibration_error,
    fit_temperature,
    predict_distribution,
    top1_confidence,
    top_margin,
)


SEEDS = (42, 123, 2026, 3407, 7777)


def brier_score(probs: Sequence[Sequence[tuple[str, float]]], y_true: Sequence[str]) -> float | None:
    if not probs:
        return None
    total = 0.0
    for ranked, true in zip(probs, y_true):
        p_true = dict(ranked).get(true, 0.0)
        # Multiclass Brier: sum_k (p_k - y_k)^2
        score = 0.0
        for label, p in ranked:
            target = 1.0 if label == true else 0.0
            score += (p - target) ** 2
        total += score
    return round(total / len(probs), 6)


def macro_f1(y_true: Sequence[str], y_pred: Sequence[str | None]) -> float:
    labels = sorted(set(y_true) | {y for y in y_pred if y})
    f1s = []
    for label in labels:
        tp = sum(1 for t, p in zip(y_true, y_pred) if t == label and p == label)
        fp = sum(1 for t, p in zip(y_true, y_pred) if t != label and p == label)
        fn = sum(1 for t, p in zip(y_true, y_pred) if t == label and p != label)
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1s.append(2 * precision * recall / (precision + recall) if precision + recall else 0.0)
    return round(sum(f1s) / len(f1s), 6) if f1s else 0.0


def routing_error_breakdown(
    y_true_disease: Sequence[str],
    y_pred_disease: Sequence[str | None],
    *,
    safety_related_diseases: set[str] | None = None,
) -> dict[str, Any]:
    """Research-only error severity. Reuses department map; no new clinical grades.

    Safety-relevant only if the true disease is in an explicit allowlist derived
    from existing prototype emergency-leaning labels (e.g. Heart attack).
    """

    safety_related = safety_related_diseases or {
        "Heart attack",
        "Paralysis (brain hemorrhage)",
        "Pneumonia",
    }
    same_dept = 0
    cross_dept = 0
    correct = 0
    safety_errors = 0
    for true, pred in zip(y_true_disease, y_pred_disease):
        if pred is None:
            cross_dept += 1
            if true in safety_related:
                safety_errors += 1
            continue
        if true == pred:
            correct += 1
            continue
        if department_for(true) == department_for(pred):
            same_dept += 1
        else:
            cross_dept += 1
            if true in safety_related:
                safety_errors += 1
    n = len(y_true_disease)
    return {
        "n": n,
        "correct": correct,
        "same_department_error": same_dept,
        "cross_department_error": cross_dept,
        "safety_relevant_error": safety_errors,
        "care_routing_accuracy": round((correct + same_dept) / n, 6) if n else 0.0,
        "department_accuracy": round(
            sum(
                1
                for true, pred in zip(y_true_disease, y_pred_disease)
                if pred is not None and department_for(true) == department_for(pred)
            )
            / n,
            6,
        )
        if n
        else 0.0,
        "note": "research-only severity; safety_relevant uses a fixed prototype disease allowlist, not new clinical grading",
    }


def _nb_predict_all(model, rows, temperature: float = 1.0):
    ranked_list = [predict_distribution(model, row["symptoms"], temperature=temperature) for row in rows]
    return ranked_list


def _linear_predict_all(model, feature_dicts, temperature: float = 1.0):
    return [predict_proba(model, features, temperature=temperature) for features in feature_dicts]


def summarize_predictions(
    ranked_list: Sequence[Sequence[tuple[str, float]]],
    y_true: Sequence[str],
    *,
    latency_s: float | None = None,
    model_size_chars: int | None = None,
    temperature: float = 1.0,
) -> dict[str, Any]:
    y_pred = [ranked[0][0] if ranked else None for ranked in ranked_list]
    n = len(y_true)
    confidences = [top1_confidence(ranked) for ranked in ranked_list]
    entropies = [distribution_entropy(ranked) for ranked in ranked_list]
    top2 = sum(1 for true, ranked in zip(y_true, ranked_list) if true in [label for label, _ in ranked[:2]])
    top3 = sum(1 for true, ranked in zip(y_true, ranked_list) if true in [label for label, _ in ranked[:3]])
    correct = sum(1 for true, pred in zip(y_true, y_pred) if true == pred)
    dept_true = [department_for(true) for true in y_true]
    dept_pred = [department_for(pred) if pred else None for pred in y_pred]
    dept_correct = sum(1 for t, p in zip(dept_true, dept_pred) if t == p)
    wrong_conf = sum(1 for true, pred, conf in zip(y_true, y_pred, confidences) if true != pred and conf >= 0.7)
    ece = expected_calibration_error(confidences, [true == pred for true, pred in zip(y_true, y_pred)])
    per_class = Counter(y_true)
    per_class_recall = {}
    for label in sorted(per_class):
        tp = sum(1 for t, p in zip(y_true, y_pred) if t == label and p == label)
        per_class_recall[label] = round(tp / per_class[label], 6)
    confusion = defaultdict(Counter)
    for true, pred in zip(y_true, y_pred):
        confusion[true][pred or "ABSTAIN"] += 1
    routing = routing_error_breakdown(y_true, y_pred)
    return {
        "test_rows": n,
        "accuracy": round(correct / n, 6) if n else 0.0,
        "macro_f1": macro_f1(y_true, y_pred),
        "top2_accuracy": round(top2 / n, 6) if n else 0.0,
        "top3_accuracy": round(top3 / n, 6) if n else 0.0,
        "department_accuracy": round(dept_correct / n, 6) if n else 0.0,
        "department_macro_f1": macro_f1(dept_true, dept_pred),
        "mean_confidence": round(sum(confidences) / n, 6) if n else 0.0,
        "mean_entropy": round(sum(entropies) / n, 6) if n else 0.0,
        "ece": ece["ece"],
        "brier": brier_score(ranked_list, y_true),
        "wrong_but_confident_rate": round(wrong_conf / n, 6) if n else 0.0,
        "per_class_recall": per_class_recall,
        "confusion_matrix": {k: dict(v) for k, v in sorted(confusion.items())},
        "routing_error": routing,
        "inference_latency_s": latency_s,
        "model_size_chars": model_size_chars,
        "temperature": temperature,
    }


def fit_and_eval_models(
    train: Sequence[Mapping[str, Any]],
    cal: Sequence[Mapping[str, Any]],
    test: Sequence[Mapping[str, Any]],
    *,
    seed: int = 42,
) -> dict[str, Any]:
    y_train = [row["disease"] for row in train]
    y_test = [row["disease"] for row in test]

    # NB
    t0 = time.perf_counter()
    nb = fit(train, ALPHA, MIN_SYMPTOM_DF)
    nb_latency = time.perf_counter() - t0
    t0 = time.perf_counter()
    nb_ranked = _nb_predict_all(nb, test)
    nb_pred_latency = time.perf_counter() - t0
    # temperature from cal
    if cal:
        try:
            temperature = float(fit_temperature(nb, cal)["temperature"])
        except Exception:
            temperature = 1.0
    else:
        temperature = 1.0
    nb_ranked_cal = _nb_predict_all(nb, test, temperature=temperature)
    nb_size = len(json.dumps(nb, ensure_ascii=False))
    nb_summary = summarize_predictions(
        nb_ranked, y_test, latency_s=nb_pred_latency, model_size_chars=nb_size
    )
    nb_summary_calibrated = summarize_predictions(
        nb_ranked_cal, y_test, latency_s=nb_pred_latency, model_size_chars=nb_size, temperature=temperature
    )

    # Binary features shared by LR/SVM
    train_bin = build_binary_features(train)
    test_bin = build_binary_features(test)
    cal_bin = build_binary_features(cal) if cal else []

    t0 = time.perf_counter()
    lr = fit_logistic_regression(train_bin, y_train, epochs=60, lr=0.4, seed=seed)
    lr_fit = time.perf_counter() - t0
    t0 = time.perf_counter()
    lr_ranked = _linear_predict_all(lr, test_bin)
    lr_pred = time.perf_counter() - t0
    lr_size = len(json.dumps({k: v for k, v in lr.items() if k != "keys"}, ensure_ascii=False, default=str))
    lr_summary = summarize_predictions(lr_ranked, y_test, latency_s=lr_pred, model_size_chars=lr_size)
    if cal_bin:
        lr_temp = fit_temperature_linear(lr, cal, train)
        lr_ranked_t = _linear_predict_all(lr, test_bin, temperature=lr_temp)
        lr_summary_cal = summarize_predictions(
            lr_ranked_t, y_test, latency_s=lr_pred, model_size_chars=lr_size, temperature=lr_temp
        )
    else:
        lr_summary_cal = lr_summary

    t0 = time.perf_counter()
    svm = fit_linear_svm(train_bin, y_train, epochs=80, lr=0.15, seed=seed)
    svm_fit = time.perf_counter() - t0
    t0 = time.perf_counter()
    # Platt-like: temperature on softmax of decision scores fitted on cal.
    svm_ranked_raw = _linear_predict_all(svm, test_bin, temperature=1.0)
    svm_pred = time.perf_counter() - t0
    svm_size = len(json.dumps({k: v for k, v in svm.items() if k != "keys"}, ensure_ascii=False, default=str))
    svm_summary = summarize_predictions(
        svm_ranked_raw, y_test, latency_s=svm_pred, model_size_chars=svm_size
    )
    # Explicit note: raw decision scores are not probabilities; calibrated variant uses temp on softmax.
    svm_summary["probability_note"] = "decision scores softmax only; not calibrated probabilities"
    if cal_bin:
        svm_temp = fit_temperature_linear(svm, cal, train)
        svm_ranked_t = _linear_predict_all(svm, test_bin, temperature=svm_temp)
        svm_summary_cal = summarize_predictions(
            svm_ranked_t,
            y_test,
            latency_s=svm_pred,
            model_size_chars=svm_size,
            temperature=svm_temp,
        )
        svm_summary_cal["probability_note"] = "temperature-scaled softmax of decision scores on calibration split"
    else:
        svm_summary_cal = svm_summary

    train_tfidf = build_tfidf_features(train, train)
    test_tfidf = build_tfidf_features(train, test)
    t0 = time.perf_counter()
    lr_tfidf = fit_logistic_regression(train_tfidf, y_train, epochs=60, lr=0.4, seed=seed)
    t0p = time.perf_counter()
    lr_tfidf_ranked = _linear_predict_all(lr_tfidf, test_tfidf)
    lr_tfidf_pred = time.perf_counter() - t0p
    lr_tfidf_size = len(json.dumps(lr_tfidf.get("weights", {}), default=str))
    lr_tfidf_summary = summarize_predictions(
        lr_tfidf_ranked, y_test, latency_s=lr_tfidf_pred, model_size_chars=lr_tfidf_size
    )

    return {
        "seed": seed,
        "train_rows": len(train),
        "cal_rows": len(cal),
        "test_rows": len(test),
        "models": {
            "multinomial_nb": nb_summary,
            "multinomial_nb_temperature": nb_summary_calibrated,
            "logistic_regression": lr_summary,
            "logistic_regression_temperature": lr_summary_cal,
            "linear_svm": svm_summary,
            "linear_svm_temperature": svm_summary_cal,
            "tfidf_logistic_regression": lr_tfidf_summary,
        },
        "fit_latency_s": {
            "multinomial_nb": nb_latency,
            "logistic_regression": lr_fit,
            "linear_svm": svm_fit,
        },
    }


def fit_temperature_linear(linear_model, cal_rows, train_rows_for_features, *, grid=None):
    """Grid-search temperature on softmax(decision_scores/T) using calibration rows."""

    if not cal_rows:
        return 1.0
    features = build_binary_features(cal_rows)
    y = [row["disease"] for row in cal_rows]
    temps = grid or [round(0.1 + 0.1 * i, 2) for i in range(1, 50)]
    best_t, best_nll = 1.0, float("inf")
    for temperature in temps:
        nll = 0.0
        for feat, true in zip(features, y):
            ranked = softmax_from_scores(decision_scores(linear_model, feat), temperature=temperature)
            p = dict(ranked).get(true, 1e-12)
            nll -= math.log(max(p, 1e-12))
        mean_nll = nll / len(y)
        if mean_nll < best_nll:
            best_nll = mean_nll
            best_t = temperature
    return best_t


def run_model_matrix(
    bundle_rows: Sequence[Mapping[str, Any]],
    *,
    seeds: Sequence[int] = SEEDS,
    threshold: float = 0.8,
    protocol_name: str = "expanded_quota_0.8",
) -> dict[str, Any]:
    all_runs = []
    for seed in seeds:
        train, cal, test, meta = quota_split(bundle_rows, threshold=threshold, seed=seed)
        if not test:
            continue
        run = fit_and_eval_models(train, cal, test, seed=seed)
        run["protocol"] = protocol_name
        run["split_meta"] = {
            "train_rows": len(train),
            "cal_rows": len(cal),
            "test_rows": len(test),
            "test_diseases": len({r["disease"] for r in test}),
        }
        all_runs.append(run)

    def agg(key_path: Sequence[str]) -> dict[str, Any]:
        values = []
        for run in all_runs:
            node: Any = run
            for key in key_path:
                node = node[key]
            if node is not None:
                values.append(float(node))
        if not values:
            return {"mean": None, "std": None, "values": []}
        mean = sum(values) / len(values)
        std = statistics.pstdev(values) if len(values) > 1 else 0.0
        return {"mean": round(mean, 6), "std": round(std, 6), "values": [round(v, 6) for v in values]}

    model_names = [
        "multinomial_nb",
        "multinomial_nb_temperature",
        "logistic_regression",
        "logistic_regression_temperature",
        "linear_svm",
        "linear_svm_temperature",
        "tfidf_logistic_regression",
    ]
    headline = {}
    for name in model_names:
        headline[name] = {
            "accuracy": agg(("models", name, "accuracy")),
            "macro_f1": agg(("models", name, "macro_f1")),
            "top3_accuracy": agg(("models", name, "top3_accuracy")),
            "department_accuracy": agg(("models", name, "department_accuracy")),
            "ece": agg(("models", name, "ece")),
            "wrong_but_confident_rate": agg(("models", name, "wrong_but_confident_rate")),
            "care_routing_accuracy": agg(("models", name, "routing_error", "care_routing_accuracy")),
            "cross_department_error_rate": {
                "mean": round(
                    (
                        sum(
                            run["models"][name]["routing_error"]["cross_department_error"]
                            / max(run["models"][name]["routing_error"]["n"], 1)
                            for run in all_runs
                        )
                        / len(all_runs)
                    ),
                    6,
                )
                if all_runs
                else None,
                "std": None,
            },
        }

    return {
        "protocol": protocol_name,
        "threshold": threshold,
        "seeds": list(seeds),
        "run_count": len(all_runs),
        "headline": headline,
        "runs": all_runs,
    }
