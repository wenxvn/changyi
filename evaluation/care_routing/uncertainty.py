"""Uncertainty-aware triage utilities for the prototype NB disease model.

Model probabilities are treated as uncalibrated assistive scores. These
helpers never claim medical confidence and never override Safety Gate.
"""

from __future__ import annotations

import math
from typing import Any, Iterable, Mapping, Sequence

from data.symptom_disease_model.train import log_scores, predict


def softmax_with_temperature(log_probs_or_scores: Mapping[str, float], temperature: float = 1.0) -> list[tuple[str, float]]:
    """Softmax over class log-scores with temperature. Returns sorted (label, p)."""

    if not log_probs_or_scores:
        return []
    t = max(float(temperature), 1e-6)
    scaled = {label: float(score) / t for label, score in log_probs_or_scores.items()}
    max_score = max(scaled.values())
    exp_scores = {label: math.exp(score - max_score) for label, score in scaled.items()}
    total = sum(exp_scores.values()) or 1.0
    ranked = sorted(
        ((label, value / total) for label, value in exp_scores.items()),
        key=lambda item: item[1],
        reverse=True,
    )
    return ranked


def predict_distribution(
    model: Mapping[str, Any],
    symptoms: Sequence[str],
    temperature: float = 1.0,
    top_k: int | None = None,
) -> list[tuple[str, float]]:
    """Full class distribution (optionally temperature-scaled)."""

    scores = log_scores(model, list(symptoms))
    ranked = softmax_with_temperature(scores, temperature=temperature)
    if top_k is not None and top_k > 0:
        return ranked[:top_k]
    return ranked


def entropy_bits(probs: Sequence[float]) -> float:
    total = 0.0
    for p in probs:
        if p > 0.0:
            total -= p * math.log2(p)
    return total


def distribution_entropy(ranked: Sequence[tuple[str, float]]) -> float:
    return entropy_bits([p for _, p in ranked])


def top1_confidence(ranked: Sequence[tuple[str, float]]) -> float:
    return float(ranked[0][1]) if ranked else 0.0


def top_margin(ranked: Sequence[tuple[str, float]]) -> float:
    if len(ranked) < 2:
        return top1_confidence(ranked)
    return float(ranked[0][1] - ranked[1][1])


def negative_log_likelihood(ranked: Sequence[tuple[str, float]], true_label: str, eps: float = 1e-12) -> float:
    probs = dict(ranked)
    p = float(probs.get(true_label, 0.0))
    return -math.log(max(p, eps))


def fit_temperature(
    model: Mapping[str, Any],
    rows: Sequence[Mapping[str, Any]],
    temperatures: Sequence[float] | None = None,
) -> dict[str, Any]:
    """Grid-search temperature minimizing NLL on a calibration split."""

    if not rows:
        return {"temperature": 1.0, "nll": None, "evaluated_rows": 0, "grid": []}
    grid = list(temperatures or [round(0.1 + 0.1 * i, 2) for i in range(1, 50)])
    best_t = 1.0
    best_nll = float("inf")
    trail: list[dict[str, float]] = []
    for temperature in grid:
        nll_sum = 0.0
        for row in rows:
            ranked = predict_distribution(model, row["symptoms"], temperature=temperature)
            nll_sum += negative_log_likelihood(ranked, row["disease"])
        mean_nll = nll_sum / len(rows)
        trail.append({"temperature": temperature, "nll": round(mean_nll, 6)})
        if mean_nll < best_nll:
            best_nll = mean_nll
            best_t = temperature
    return {
        "temperature": best_t,
        "nll": round(best_nll, 6),
        "evaluated_rows": len(rows),
        "grid": trail,
    }


def expected_calibration_error(
    confidences: Sequence[float],
    correct: Sequence[bool],
    n_bins: int = 10,
) -> dict[str, Any]:
    """Standard ECE over equal-width confidence bins."""

    if len(confidences) != len(correct) or not confidences:
        return {"ece": None, "bins": [], "n": 0}
    bins = [
        {
            "bin_index": i,
            "lower": i / n_bins,
            "upper": (i + 1) / n_bins,
            "count": 0,
            "avg_confidence": 0.0,
            "avg_accuracy": 0.0,
            "gap": 0.0,
        }
        for i in range(n_bins)
    ]
    for confidence, is_correct in zip(confidences, correct):
        index = min(int(confidence * n_bins), n_bins - 1)
        buckets = bins[index]
        buckets["count"] += 1
        buckets["avg_confidence"] += float(confidence)
        buckets["avg_accuracy"] += 1.0 if is_correct else 0.0
    total = len(confidences)
    ece = 0.0
    for bucket in bins:
        count = bucket["count"]
        if count:
            bucket["avg_confidence"] = round(bucket["avg_confidence"] / count, 6)
            bucket["avg_accuracy"] = round(bucket["avg_accuracy"] / count, 6)
            bucket["gap"] = round(abs(bucket["avg_confidence"] - bucket["avg_accuracy"]), 6)
            ece += (count / total) * bucket["gap"]
    return {"ece": round(ece, 6), "bins": bins, "n": total}


def conformal_threshold(
    model: Mapping[str, Any],
    calibration_rows: Sequence[Mapping[str, Any]],
    alpha: float = 0.1,
    temperature: float = 1.0,
) -> dict[str, Any]:
    """Split-conformal LAC threshold: include y if 1 - p_y <= q_hat."""

    if not calibration_rows:
        return {"alpha": alpha, "threshold": 1.0, "scores": [], "temperature": temperature}
    scores: list[float] = []
    for row in calibration_rows:
        ranked = predict_distribution(model, row["symptoms"], temperature=temperature)
        probs = dict(ranked)
        scores.append(1.0 - float(probs.get(row["disease"], 0.0)))
    scores_sorted = sorted(scores)
    n = len(scores_sorted)
    # Finite-sample corrected quantile index.
    level = min(math.ceil((n + 1) * (1.0 - alpha)) - 1, n - 1)
    level = max(level, 0)
    threshold = scores_sorted[level]
    return {
        "alpha": alpha,
        "threshold": threshold,
        "calibration_rows": n,
        "temperature": temperature,
        "score_quantiles": {
            "p50": scores_sorted[n // 2],
            "p90": scores_sorted[min(int(0.9 * (n - 1)), n - 1)],
            "max": scores_sorted[-1],
        },
    }


def prediction_set(
    ranked: Sequence[tuple[str, float]],
    conformal: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """LAC conformal prediction set from a calibrated threshold."""

    threshold = float(conformal.get("threshold", 1.0))
    items = [
        {"disease": label, "probability": round(float(prob), 6), "in_set": (1.0 - float(prob)) <= threshold}
        for label, prob in ranked
    ]
    return items


def uncertainty_level(entropy: float, confidence: float, max_entropy: float | None = None) -> str:
    """Coarse operational levels for assistive routing (not medical risk scores)."""

    if max_entropy is None or max_entropy <= 0:
        return "high" if confidence < 0.45 else ("medium" if confidence < 0.70 else "low")
    ratio = entropy / max_entropy
    if confidence >= 0.75 and ratio <= 0.35:
        return "low"
    if confidence >= 0.50 and ratio <= 0.65:
        return "medium"
    return "high"


def should_clarify(
    *,
    entropy: float,
    confidence: float,
    set_size: int,
    max_entropy: float,
    confidence_threshold: float = 0.55,
    entropy_ratio_threshold: float = 0.55,
    max_set_size: int = 3,
) -> bool:
    if set_size > max_set_size:
        return True
    if confidence < confidence_threshold:
        return True
    if max_entropy > 0 and (entropy / max_entropy) > entropy_ratio_threshold:
        return True
    return False


def build_uncertainty_payload(
    ranked: Sequence[tuple[str, float]],
    disease_name_map: Mapping[str, str],
    department_for,
    conformal: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Unified offline payload shape requested by the exploration task."""

    if not ranked:
        return {
            "predicted_department": None,
            "probability_distribution": [],
            "confidence": 0.0,
            "entropy": 0.0,
            "max_entropy": 0.0,
            "margin": 0.0,
            "uncertainty_level": "high",
            "prediction_set": [],
            "prediction_set_size": 0,
            "should_clarify": True,
            "assistive_only": True,
            "not_medical_confidence": True,
        }

    entropy = distribution_entropy(ranked)
    confidence = top1_confidence(ranked)
    margin = top_margin(ranked)
    class_count = max(len(ranked), 2)
    max_entropy = math.log2(class_count) if class_count > 1 else 0.0
    set_items = prediction_set(ranked, conformal) if conformal else [
        {"disease": label, "probability": round(float(prob), 6), "in_set": True}
        for label, prob in ranked[:3]
    ]
    set_size = sum(1 for item in set_items if item.get("in_set"))
    level = uncertainty_level(entropy, confidence, max_entropy)
    clarify = should_clarify(
        entropy=entropy,
        confidence=confidence,
        set_size=set_size,
        max_entropy=max_entropy,
    )
    top_label = ranked[0][0]
    return {
        "predicted_disease": disease_name_map.get(top_label, top_label),
        "predicted_department": department_for(top_label),
        "probability_distribution": [
            {
                "disease": disease_name_map.get(label, label),
                "raw_label": label,
                "probability": round(float(prob), 6),
            }
            for label, prob in ranked[:10]
        ],
        "confidence": round(confidence, 6),
        "entropy": round(entropy, 6),
        "max_entropy": round(max_entropy, 6),
        "margin": round(margin, 6),
        "uncertainty_level": level,
        "prediction_set": [
            {
                "disease": disease_name_map.get(item["disease"], item["disease"]),
                "raw_label": item["disease"],
                "probability": item["probability"],
                "in_set": item["in_set"],
            }
            for item in set_items
        ],
        "prediction_set_size": set_size,
        "should_clarify": clarify,
        "assistive_only": True,
        "not_medical_confidence": True,
        "disclaimer": "置信度与不确定性仅来自离线症状分类模型概率，未经临床校准，不得解释为医学置信度；急症仍以 Safety Gate 为准。",
    }
