"""Selective prediction / abstention for Direct Department.

Thresholds are fit on calibration only. Test never tunes coverage.
"""

from __future__ import annotations

import statistics
from typing import Any, Callable, Mapping, Sequence

from .direct_department import macro_f1, weighted_f1
from .uncertainty import expected_calibration_error


SignalFn = Callable[[Sequence[tuple[str, float]]], float]


def _max_prob(ranked: Sequence[tuple[str, float]]) -> float:
    return float(ranked[0][1]) if ranked else 0.0


def _entropy(ranked: Sequence[tuple[str, float]]) -> float:
    from .uncertainty import distribution_entropy

    return distribution_entropy(ranked)


def _margin(ranked: Sequence[tuple[str, float]]) -> float:
    from .uncertainty import top_margin

    return top_margin(ranked)


def _neg_entropy(ranked: Sequence[tuple[str, float]]) -> float:
    return -_entropy(ranked)


SIGNALS: dict[str, SignalFn] = {
    "max_probability": _max_prob,
    "neg_entropy": _neg_entropy,
    "margin": _margin,
}


def threshold_for_coverage(
    scores: Sequence[float],
    target_coverage: float,
    *,
    higher_is_better: bool = True,
) -> float:
    """Pick a score threshold so that approximately ``target_coverage`` of cal rows are retained."""

    if not scores:
        return 0.0
    ordered = sorted(scores, reverse=higher_is_better)
    # Retain the top-k scores where k = ceil(n * coverage).
    n = len(ordered)
    k = max(1, min(n, int(round(n * target_coverage))))
    # Threshold is the k-th best score (inclusive).
    return float(ordered[k - 1])


def selective_metrics(
    ranked_list: Sequence[Sequence[tuple[str, float]]],
    y_true: Sequence[str],
    *,
    signal: str,
    threshold: float,
    higher_is_better: bool = True,
) -> dict[str, Any]:
    fn = SIGNALS[signal]
    scores = [fn(ranked) for ranked in ranked_list]
    retained_ranked = []
    y_true_ret = []
    y_pred_ret = []
    wrong_conf = 0
    for ranked, true, score in zip(ranked_list, y_true, scores):
        retained = (score >= threshold) if higher_is_better else (score <= threshold)
        if not retained:
            continue
        retained_ranked.append(ranked)
        pred = ranked[0][0] if ranked else None
        y_true_ret.append(true)
        y_pred_ret.append(pred)
        if pred != true and _max_prob(ranked) >= 0.7:
            wrong_conf += 1
    n = len(y_true)
    retained_n = len(y_true_ret)
    coverage = retained_n / n if n else 0.0
    if retained_n:
        accuracy = sum(1 for t, p in zip(y_true_ret, y_pred_ret) if t == p) / retained_n
        error_rate = 1.0 - accuracy
        ece = expected_calibration_error(
            [_max_prob(r) for r in retained_ranked],
            [t == p for t, p in zip(y_true_ret, y_pred_ret)],
        )
    else:
        accuracy = None
        error_rate = None
        ece = {"ece": None}
    return {
        "signal": signal,
        "threshold": threshold,
        "coverage": round(coverage, 6),
        "abstention_rate": round(1.0 - coverage, 6),
        "retained_rows": retained_n,
        "retained_accuracy": round(accuracy, 6) if accuracy is not None else None,
        "retained_macro_f1": macro_f1(y_true_ret, y_pred_ret) if retained_n else None,
        "retained_weighted_f1": weighted_f1(y_true_ret, y_pred_ret) if retained_n else None,
        "retained_error_rate": round(error_rate, 6) if error_rate is not None else None,
        "retained_wrong_but_confident_rate": round(wrong_conf / retained_n, 6) if retained_n else None,
        "retained_ece": ece.get("ece"),
    }


def risk_coverage_curve(
    cal_ranked: Sequence[Sequence[tuple[str, float]]],
    test_ranked: Sequence[Sequence[tuple[str, float]]],
    y_cal: Sequence[str],
    y_test: Sequence[str],
    *,
    signal: str,
    coverages: Sequence[float] = (1.0, 0.9, 0.8, 0.7, 0.6, 0.5),
) -> dict[str, Any]:
    """Fit thresholds on calibration coverages, evaluate on test."""

    fn = SIGNALS[signal]
    cal_scores = [fn(ranked) for ranked in cal_ranked]
    points = []
    for coverage in coverages:
        threshold = threshold_for_coverage(cal_scores, coverage, higher_is_better=True)
        metrics = selective_metrics(
            test_ranked, y_test, signal=signal, threshold=threshold, higher_is_better=True
        )
        points.append({"target_coverage": coverage, **metrics})
    return {"signal": signal, "points": points}


def combined_signal(ranked: Sequence[tuple[str, float]]) -> float:
    """Simple combo: average of max_prob and margin, minus entropy penalty."""

    return 0.5 * _max_prob(ranked) + 0.5 * _margin(ranked) - 0.1 * _entropy(ranked)


def run_selective_routing(
    train: Sequence[Mapping[str, Any]],
    cal: Sequence[Mapping[str, Any]],
    test: Sequence[Mapping[str, Any]],
    *,
    seed: int = 42,
    model_name: str = "logistic_regression_binary",
    feature_key: str | None = None,
) -> dict[str, Any]:
    from .direct_department import fit_direct_department_models, prepare_feature_sets

    SIGNALS["combined"] = combined_signal
    fitted = fit_direct_department_models(train, cal, test, seed=seed)
    preds = fitted.get("_predictions", {}).get(model_name)
    if not preds:
        return {"error": f"missing predictions for {model_name}"}

    from .disease_department import department_for

    y_test = preds["y_true"]
    y_cal = [department_for(row["disease"]) for row in cal]
    from .model_baselines import fit_logistic_regression, predict_proba

    # Default feature key from model name.
    if feature_key is None:
        if "char" in model_name and "fusion" in model_name:
            feature_key = "word_char_fusion"
        elif "char" in model_name:
            feature_key = "char_ngram_tfidf"
        elif "tfidf" in model_name or "word" in model_name:
            feature_key = "word_tfidf"
        elif "three_state" in model_name:
            feature_key = "three_state_present"
        else:
            feature_key = "symptom_binary"

    y_train = [department_for(row["disease"]) for row in train]
    features = prepare_feature_sets(train, cal, test)[feature_key]
    if model_name.startswith("linear_svm"):
        from .model_baselines import fit_linear_svm

        model = fit_linear_svm(features["train"], y_train, epochs=80, lr=0.15, seed=seed)
    else:
        model = fit_logistic_regression(features["train"], y_train, epochs=70, lr=0.4, seed=seed)
    temp = float(fitted.get("temperatures", {}).get(model_name, 1.0))
    cal_ranked = [predict_proba(model, feat, temperature=temp) for feat in features["cal"]]
    test_ranked = preds["ranked_calibrated"]

    signals = ("max_probability", "neg_entropy", "margin", "combined")
    curves = {}
    for signal in signals:
        curves[signal] = risk_coverage_curve(
            cal_ranked, test_ranked, y_cal, y_test, signal=signal
        )

    required = {}
    for point in curves["max_probability"]["points"]:
        key = f"{int(point['target_coverage'] * 100)}%"
        required[key] = {
            "retained_accuracy": point["retained_accuracy"],
            "coverage": point["coverage"],
            "abstention_rate": point["abstention_rate"],
            "retained_macro_f1": point["retained_macro_f1"],
            "wrong_but_confident_rate": point["retained_wrong_but_confident_rate"],
            "target_coverage": point["target_coverage"],
        }

    full = selective_metrics(
        test_ranked, y_test, signal="max_probability", threshold=0.0
    )
    return {
        "protocol": "selective_routing",
        "model_name": model_name,
        "feature_key": feature_key,
        "seed": seed,
        "temperature": temp,
        "full_coverage": full,
        "risk_coverage": curves,
        "required_coverages_max_prob": required,
        "note": "thresholds from calibration only; test never tunes coverage",
    }
