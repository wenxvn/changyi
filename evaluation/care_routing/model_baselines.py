"""Small pure-Python baselines to test whether NB capacity limits near-dup generalization.

No sklearn/numpy dependency. Multiclass logistic regression and linear SVM
(one-vs-rest hinge) over binary bag-of-symptom features, plus optional TF-IDF.
"""

from __future__ import annotations

import math
import random
from typing import Any, Mapping, Sequence


def _sigmoid(value: float) -> float:
    if value >= 0:
        z = math.exp(-value)
        return 1.0 / (1.0 + z)
    z = math.exp(value)
    return z / (1.0 + z)


def build_binary_features(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, float]]:
    return [{f"{symptom}__present": 1.0 for symptom in row["symptoms"]} for row in rows]


def build_tfidf_features(
    train_rows: Sequence[Mapping[str, Any]],
    rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, float]]:
    # Document frequency from train only.
    df: dict[str, int] = {}
    for row in train_rows:
        for symptom in set(row["symptoms"]):
            df[symptom] = df.get(symptom, 0) + 1
    n_docs = max(len(train_rows), 1)
    idf = {
        symptom: math.log((1.0 + n_docs) / (1.0 + count)) + 1.0
        for symptom, count in df.items()
    }
    features = []
    for row in rows:
        counts: dict[str, int] = {}
        for symptom in row["symptoms"]:
            counts[symptom] = counts.get(symptom, 0) + 1
        total = sum(counts.values()) or 1
        features.append(
            {
                f"{symptom}__present": (count / total) * idf.get(symptom, 0.0)
                for symptom, count in counts.items()
                if symptom in idf
            }
        )
    return features


def _all_keys(feature_dicts: Sequence[Mapping[str, float]]) -> list[str]:
    keys: set[str] = set()
    for item in feature_dicts:
        keys.update(item.keys())
    return sorted(keys)


def _dot(weights: Mapping[str, float], features: Mapping[str, float]) -> float:
    total = 0.0
    for key, value in features.items():
        weight = weights.get(key, 0.0)
        if weight:
            total += weight * value
    return total


def fit_logistic_regression(
    train_features: Sequence[Mapping[str, float]],
    train_labels: Sequence[str],
    *,
    epochs: int = 80,
    lr: float = 0.5,
    l2: float = 1e-3,
    seed: int = 42,
) -> dict[str, Any]:
    """One-vs-rest logistic regression with SGD. Features are sparse dicts."""

    rng = random.Random(seed)
    labels = sorted(set(train_labels))
    keys = _all_keys(train_features)
    weights: dict[str, dict[str, float]] = {label: {} for label in labels}
    biases: dict[str, float] = {label: 0.0 for label in labels}
    indices = list(range(len(train_features)))
    for _epoch in range(epochs):
        rng.shuffle(indices)
        for index in indices:
            features = train_features[index]
            true_label = train_labels[index]
            for label in labels:
                target = 1.0 if label == true_label else 0.0
                score = biases[label] + _dot(weights[label], features)
                error = _sigmoid(score) - target
                # Bias update
                biases[label] -= lr * error
                # Sparse weight update
                row_w = weights[label]
                for key, value in features.items():
                    grad = error * value + l2 * row_w.get(key, 0.0)
                    row_w[key] = row_w.get(key, 0.0) - lr * grad
    return {
        "model_type": "logistic_regression_ovr",
        "labels": labels,
        "keys": keys,
        "weights": weights,
        "biases": biases,
    }


def fit_linear_svm(
    train_features: Sequence[Mapping[str, float]],
    train_labels: Sequence[str],
    *,
    epochs: int = 100,
    lr: float = 0.2,
    c: float = 1.0,
    seed: int = 42,
) -> dict[str, Any]:
    """One-vs-rest linear SVM with hinge loss + L2, plain SGD."""

    rng = random.Random(seed)
    labels = sorted(set(train_labels))
    weights: dict[str, dict[str, float]] = {label: {} for label in labels}
    biases: dict[str, float] = {label: 0.0 for label in labels}
    indices = list(range(len(train_features)))
    for epoch in range(epochs):
        rng.shuffle(indices)
        step = lr / (1.0 + 0.01 * epoch)
        for index in indices:
            features = train_features[index]
            true_label = train_labels[index]
            for label in labels:
                target = 1.0 if label == true_label else -1.0
                score = biases[label] + _dot(weights[label], features)
                if target * score < 1.0:
                    biases[label] += step * target
                    row_w = weights[label]
                    for key, value in features.items():
                        row_w[key] = row_w.get(key, 0.0) + step * target * value
    return {
        "model_type": "linear_svm_ovr",
        "labels": labels,
        "weights": weights,
        "biases": biases,
    }


def decision_scores(model: Mapping[str, Any], features: Mapping[str, float]) -> list[tuple[str, float]]:
    labels = model["labels"]
    scores = [
        (label, model["biases"][label] + _dot(model["weights"][label], features))
        for label in labels
    ]
    scores.sort(key=lambda item: item[1], reverse=True)
    return scores


def softmax_from_scores(scores: Sequence[tuple[str, float]], temperature: float = 1.0) -> list[tuple[str, float]]:
    if not scores:
        return []
    t = max(float(temperature), 1e-6)
    scaled = [(label, value / t) for label, value in scores]
    max_score = max(value for _, value in scaled)
    exp_scores = [(label, math.exp(value - max_score)) for label, value in scaled]
    total = sum(value for _, value in exp_scores) or 1.0
    return sorted(
        ((label, value / total) for label, value in exp_scores),
        key=lambda item: item[1],
        reverse=True,
    )


def predict_proba(model: Mapping[str, Any], features: Mapping[str, float], temperature: float = 1.0) -> list[tuple[str, float]]:
    return softmax_from_scores(decision_scores(model, features), temperature=temperature)


def evaluate_sklearn_like(
    model: Mapping[str, Any],
    test_features: Sequence[Mapping[str, float]],
    test_labels: Sequence[str],
    *,
    top_k_list: Sequence[int] = (1, 2, 3),
) -> dict[str, Any]:
    n = len(test_labels)
    if not n:
        return {"test_rows": 0, "accuracy": None}
    correct = 0
    topk = {k: 0 for k in top_k_list}
    y_pred = []
    confidences = []
    for features, true in zip(test_features, test_labels):
        ranked = predict_proba(model, features)
        labels = [label for label, _ in ranked]
        y_pred.append(labels[0] if labels else None)
        confidences.append(ranked[0][1] if ranked else 0.0)
        correct += int(bool(labels) and labels[0] == true)
        for k in top_k_list:
            topk[k] += int(true in labels[:k])

    labels_all = sorted(set(test_labels) | {y for y in y_pred if y})
    f1s = []
    for label in labels_all:
        tp = sum(1 for t, p in zip(test_labels, y_pred) if t == label and p == label)
        fp = sum(1 for t, p in zip(test_labels, y_pred) if t != label and p == label)
        fn = sum(1 for t, p in zip(test_labels, y_pred) if t == label and p != label)
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1s.append(2 * precision * recall / (precision + recall) if precision + recall else 0.0)
    return {
        "test_rows": n,
        "accuracy": round(correct / n, 6),
        "topk_accuracy": {str(k): round(topk[k] / n, 6) for k in top_k_list},
        "macro_f1": round(sum(f1s) / len(f1s), 6) if f1s else 0.0,
        "mean_confidence": round(sum(confidences) / n, 6),
    }
