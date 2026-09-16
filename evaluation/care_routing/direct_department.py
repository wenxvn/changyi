"""Direct Department classifier matrix for Round4.

Symptoms → Department. No diagnosis claim. Honest quota split only.
"""

from __future__ import annotations

import json
import math
import statistics
import time
from collections import Counter, defaultdict
from typing import Any, Mapping, Sequence

from data.symptom_disease_model.train import fit

from evaluation.model.evaluate_grouped import ALPHA, MIN_SYMPTOM_DF

from .disease_department import department_for
from .model_baselines import (
    build_binary_features,
    build_char_ngram_tfidf_features,
    build_fusion_features,
    build_tfidf_features,
    build_three_state_features,
    decision_scores,
    fit_linear_svm,
    fit_logistic_regression,
    predict_proba,
    softmax_from_scores,
)
from .round3_split_audit import load_expanded, quota_split
from .uncertainty import (
    distribution_entropy,
    expected_calibration_error,
    top1_confidence,
    top_margin,
)

SEEDS = (42, 123, 2026, 3407, 7777)


def weighted_f1(y_true: Sequence[str], y_pred: Sequence[str | None]) -> float:
    support = Counter(y_true)
    labels = sorted(support)
    total = sum(support.values()) or 1
    score = 0.0
    for label in labels:
        tp = sum(1 for t, p in zip(y_true, y_pred) if t == label and p == label)
        fp = sum(1 for t, p in zip(y_true, y_pred) if t != label and p == label)
        fn = sum(1 for t, p in zip(y_true, y_pred) if t == label and p != label)
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        score += support[label] * f1
    return round(score / total, 6)


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


def summarize_dept_predictions(
    ranked_list: Sequence[Sequence[tuple[str, float]]],
    y_true: Sequence[str],
    *,
    latency_s: float | None = None,
    model_size_chars: int | None = None,
    temperature: float = 1.0,
) -> dict[str, Any]:
    y_pred = [ranked[0][0] if ranked else None for ranked in ranked_list]
    n = len(y_true)
    if not n:
        return {"test_rows": 0}
    confidences = [top1_confidence(ranked) for ranked in ranked_list]
    entropies = [distribution_entropy(ranked) for ranked in ranked_list]
    margins = [top_margin(ranked) for ranked in ranked_list]
    correct_flags = [true == pred for true, pred in zip(y_true, y_pred)]
    top2 = sum(
        1 for true, ranked in zip(y_true, ranked_list) if true in [label for label, _ in ranked[:2]]
    )
    top3 = sum(
        1 for true, ranked in zip(y_true, ranked_list) if true in [label for label, _ in ranked[:3]]
    )
    wrong_conf = sum(1 for ok, conf in zip(correct_flags, confidences) if not ok and conf >= 0.7)
    ece = expected_calibration_error(confidences, correct_flags)
    # Multiclass Brier
    brier = 0.0
    for ranked, true in zip(ranked_list, y_true):
        for label, p in ranked:
            target = 1.0 if label == true else 0.0
            brier += (p - target) ** 2
    brier = round(brier / n, 6)

    per_class_total = Counter(y_true)
    per_class_recall = {}
    confusion: dict[str, Counter[str]] = defaultdict(Counter)
    for true, pred in zip(y_true, y_pred):
        confusion[true][pred or "ABSTAIN"] += 1
    for label in sorted(per_class_total):
        tp = confusion[label][label]
        per_class_recall[label] = round(tp / per_class_total[label], 6)

    return {
        "test_rows": n,
        "accuracy": round(sum(correct_flags) / n, 6),
        "macro_f1": macro_f1(y_true, y_pred),
        "weighted_f1": weighted_f1(y_true, y_pred),
        "top2_accuracy": round(top2 / n, 6),
        "top3_accuracy": round(top3 / n, 6),
        "mean_confidence": round(sum(confidences) / n, 6),
        "mean_entropy": round(sum(entropies) / n, 6),
        "mean_margin": round(sum(margins) / n, 6),
        "ece": ece["ece"],
        "brier": brier,
        "wrong_but_confident_rate": round(wrong_conf / n, 6),
        "per_department_recall": per_class_recall,
        "confusion_matrix": {k: dict(v) for k, v in sorted(confusion.items())},
        "inference_latency_s": latency_s,
        "model_size_chars": model_size_chars,
        "temperature": temperature,
    }


def fit_temperature_linear(linear_model, cal_features, cal_labels, *, grid=None) -> float:
    if not cal_labels:
        return 1.0
    temps = grid or [round(0.1 + 0.1 * i, 2) for i in range(1, 50)]
    best_t, best_nll = 1.0, float("inf")
    for temperature in temps:
        nll = 0.0
        for feat, true in zip(cal_features, cal_labels):
            ranked = softmax_from_scores(decision_scores(linear_model, feat), temperature=temperature)
            p = dict(ranked).get(true, 1e-12)
            nll -= math.log(max(p, 1e-12))
        mean = nll / len(cal_labels)
        if mean < best_nll:
            best_nll = mean
            best_t = temperature
    return best_t


def prepare_feature_sets(
    train: Sequence[Mapping[str, Any]],
    cal: Sequence[Mapping[str, Any]],
    test: Sequence[Mapping[str, Any]],
) -> dict[str, dict[str, list[dict[str, float]]]]:
    train_bin = build_binary_features(train)
    cal_bin = build_binary_features(cal)
    test_bin = build_binary_features(test)
    train_word = build_tfidf_features(train, train)
    cal_word = build_tfidf_features(train, cal)
    test_word = build_tfidf_features(train, test)
    train_char = build_char_ngram_tfidf_features(train, train)
    cal_char = build_char_ngram_tfidf_features(train, cal)
    test_char = build_char_ngram_tfidf_features(train, test)
    return {
        "symptom_binary": {"train": train_bin, "cal": cal_bin, "test": test_bin},
        "word_tfidf": {"train": train_word, "cal": cal_word, "test": test_word},
        "char_ngram_tfidf": {"train": train_char, "cal": cal_char, "test": test_char},
        "word_char_fusion": {
            "train": build_fusion_features(train_word, train_char),
            "cal": build_fusion_features(cal_word, cal_char),
            "test": build_fusion_features(test_word, test_char),
        },
        "three_state_present": {
            "train": build_three_state_features(train),
            "cal": build_three_state_features(cal),
            "test": build_three_state_features(test),
        },
    }


def fit_direct_department_models(
    train: Sequence[Mapping[str, Any]],
    cal: Sequence[Mapping[str, Any]],
    test: Sequence[Mapping[str, Any]],
    *,
    seed: int = 42,
) -> dict[str, Any]:
    y_train = [department_for(row["disease"]) for row in train]
    y_cal = [department_for(row["disease"]) for row in cal]
    y_test = [department_for(row["disease"]) for row in test]
    features = prepare_feature_sets(train, cal, test)

    results: dict[str, Any] = {
        "seed": seed,
        "train_rows": len(train),
        "cal_rows": len(cal),
        "test_rows": len(test),
        "department_count_train": len(set(y_train)),
        "department_count_test": len(set(y_test)),
        "models": {},
    }

    # NB on symptom tags as department labels (reuse train.fit).
    t0 = time.perf_counter()
    # NB needs disease labels; for department NB we remap rows.
    dept_rows_train = [
        {"disease": department_for(row["disease"]), "symptoms": row["symptoms"]} for row in train
    ]
    dept_rows_test = [
        {"disease": department_for(row["disease"]), "symptoms": row["symptoms"]} for row in test
    ]
    nb = fit(dept_rows_train, ALPHA, MIN_SYMPTOM_DF)
    from .uncertainty import predict_distribution

    nb_ranked = [predict_distribution(nb, row["symptoms"]) for row in dept_rows_test]
    nb_latency = time.perf_counter() - t0
    results["models"]["multinomial_nb"] = summarize_dept_predictions(
        nb_ranked, y_test, latency_s=nb_latency, model_size_chars=len(json.dumps(nb))
    )

    def run_linear(name: str, feature_key: str, *, svm: bool = False) -> None:
        feats = features[feature_key]
        # Heavier sparse feature spaces need fewer epochs to stay interactive.
        if feature_key in {"char_ngram_tfidf", "word_char_fusion"}:
            epochs = 35 if not svm else 40
            lr = 0.35 if not svm else 0.12
        else:
            epochs = 70 if not svm else 80
            lr = 0.4 if not svm else 0.15
        t0 = time.perf_counter()
        if svm:
            model = fit_linear_svm(feats["train"], y_train, epochs=epochs, lr=lr, seed=seed)
        else:
            model = fit_logistic_regression(feats["train"], y_train, epochs=epochs, lr=lr, seed=seed)
        fit_s = time.perf_counter() - t0
        t0 = time.perf_counter()
        raw = [predict_proba(model, feat, temperature=1.0) for feat in feats["test"]]
        pred_s = time.perf_counter() - t0
        size = len(json.dumps(model.get("weights", {}), default=str))
        raw_summary = summarize_dept_predictions(
            raw, y_test, latency_s=pred_s, model_size_chars=size
        )
        if feats["cal"]:
            temp = fit_temperature_linear(model, feats["cal"], y_cal)
            calibrated = [
                predict_proba(model, feat, temperature=temp) for feat in feats["test"]
            ]
            cal_summary = summarize_dept_predictions(
                calibrated,
                y_test,
                latency_s=pred_s,
                model_size_chars=size,
                temperature=temp,
            )
        else:
            temp = 1.0
            cal_summary = raw_summary
        results["models"][name] = raw_summary
        results["models"][f"{name}_temperature"] = cal_summary
        results.setdefault("fit_latency_s", {})[name] = fit_s
        results.setdefault("temperatures", {})[name] = temp
        # Keep predictions for selective routing / confusion analysis.
        results.setdefault("_predictions", {})[name] = {
            "ranked": raw,
            "ranked_calibrated": calibrated if feats["cal"] else raw,
            "y_true": y_test,
            "y_pred": [r[0][0] if r else None for r in (calibrated if feats["cal"] else raw)],
            "confidence": [
                top1_confidence(r) for r in (calibrated if feats["cal"] else raw)
            ],
            "entropy": [
                distribution_entropy(r) for r in (calibrated if feats["cal"] else raw)
            ],
            "margin": [top_margin(r) for r in (calibrated if feats["cal"] else raw)],
        }

    run_linear("logistic_regression_binary", "symptom_binary")
    run_linear("linear_svm_binary", "symptom_binary", svm=True)
    run_linear("tfidf_logistic_regression", "word_tfidf")
    run_linear("char_ngram_tfidf_lr", "char_ngram_tfidf")
    run_linear("word_char_fusion_lr", "word_char_fusion")
    run_linear("three_state_lr", "three_state_present")

    return results


def aggregate_direct_matrix(runs: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    def agg(model_key: str, metric: str) -> dict[str, Any]:
        values = []
        for run in runs:
            summary = run["models"].get(model_key)
            if summary and summary.get(metric) is not None:
                values.append(float(summary[metric]))
        if not values:
            return {"mean": None, "std": None, "values": []}
        mean = sum(values) / len(values)
        std = statistics.pstdev(values) if len(values) > 1 else 0.0
        return {"mean": round(mean, 6), "std": round(std, 6), "values": [round(v, 6) for v in values]}

    model_keys = sorted(
        {
            key
            for run in runs
            for key in run["models"]
            if not key.endswith("_temperature") and key != "multinomial_nb"
        }
        | {"multinomial_nb"}
    )
    headline = {}
    for key in model_keys:
        headline[key] = {
            metric: agg(key, metric)
            for metric in (
                "accuracy",
                "macro_f1",
                "weighted_f1",
                "top2_accuracy",
                "top3_accuracy",
                "ece",
                "brier",
                "wrong_but_confident_rate",
            )
        }
    # Rank by mean accuracy.
    ranked = sorted(
        (
            (key, headline[key]["accuracy"]["mean"] or 0.0)
            for key in headline
            if not key.endswith("_temperature")
        ),
        key=lambda item: item[1],
        reverse=True,
    )
    return {
        "run_count": len(runs),
        "seeds": [run["seed"] for run in runs],
        "headline": headline,
        "best_model": ranked[0][0] if ranked else None,
        "best_accuracy": ranked[0][1] if ranked else None,
        "ranking": ranked,
    }


def run_direct_department_matrix(
    rows: Sequence[Mapping[str, Any]] | None = None,
    *,
    seeds: Sequence[int] = SEEDS,
    threshold: float = 0.8,
) -> dict[str, Any]:
    bundle_rows = list(rows) if rows is not None else load_expanded().rows
    runs = []
    for seed in seeds:
        train, cal, test, meta = quota_split(bundle_rows, threshold=threshold, seed=seed)
        if not test:
            continue
        run = fit_direct_department_models(train, cal, test, seed=seed)
        run["split_meta"] = {
            "train_rows": len(train),
            "cal_rows": len(cal),
            "test_rows": len(test),
            "test_departments": len({department_for(r["disease"]) for r in test}),
        }
        runs.append(run)
    aggregate = aggregate_direct_matrix(runs)
    # Strip bulky prediction payloads from stored runs by default.
    slim_runs = []
    for run in runs:
        slim = {k: v for k, v in run.items() if not k.startswith("_")}
        slim_runs.append(slim)
    return {
        "protocol": "direct_department_matrix",
        "threshold": threshold,
        "aggregate": aggregate,
        "runs": slim_runs,
        "note": "Symptoms → Department; not a diagnosis model; test never used for tuning",
    }
