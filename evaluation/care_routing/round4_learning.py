"""Round4 learning curve for Direct Department + representation ablation helpers."""

from __future__ import annotations

import random
import statistics
from collections import defaultdict
from typing import Any, Mapping, Sequence

from .direct_department import fit_direct_department_models
from .disease_department import department_for
from .round3_split_audit import quota_split


def _subset_by_fraction(
    train_rows: Sequence[Mapping[str, Any]],
    fraction: float,
    seed: int,
) -> list[dict[str, Any]]:
    if fraction >= 0.999:
        return list(train_rows)
    rng = random.Random(seed)
    by_disease: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in train_rows:
        by_disease[row["disease"]].append(row)
    selected: list[dict[str, Any]] = []
    target = max(1, int(round(len(train_rows) * fraction)))
    diseases = sorted(by_disease)
    pointers = {disease: 0 for disease in diseases}
    while len(selected) < target:
        progressed = False
        for disease in diseases:
            items = by_disease[disease]
            index = pointers[disease]
            if index < len(items):
                selected.append(items[index])
                pointers[disease] = index + 1
                progressed = True
                if len(selected) >= target:
                    break
        if not progressed:
            break
    rng.shuffle(selected)
    return selected


def direct_department_learning_curve(
    rows: Sequence[Mapping[str, Any]],
    *,
    model_keys: Sequence[str] = (
        "logistic_regression_binary",
        "char_ngram_tfidf_lr",
    ),
    fractions: Sequence[float] = (0.2, 0.4, 0.6, 0.8, 1.0),
    seeds: Sequence[int] = (42, 123, 2026),
    threshold: float = 0.8,
) -> dict[str, Any]:
    points = []
    for fraction in fractions:
        per_seed = []
        for seed in seeds:
            train, cal, test, _ = quota_split(rows, threshold=threshold, seed=seed)
            if not test:
                continue
            subset = _subset_by_fraction(train, fraction, seed)
            # Keep a small cal slice from original cal for temperature only.
            fitted = fit_direct_department_models(subset, cal, test, seed=seed)
            row = {
                "seed": seed,
                "train_rows": len(subset),
                "test_rows": len(test),
            }
            for key in model_keys:
                summary = fitted["models"].get(key) or {}
                row[f"{key}_accuracy"] = summary.get("accuracy")
                row[f"{key}_macro_f1"] = summary.get("macro_f1")
                row[f"{key}_top2"] = summary.get("top2_accuracy")
                row[f"{key}_ece"] = summary.get("ece")
            per_seed.append(row)

        def mean_std(key: str) -> dict[str, Any]:
            values = [r[key] for r in per_seed if r.get(key) is not None]
            if not values:
                return {"mean": None, "std": None}
            mean = sum(values) / len(values)
            std = statistics.pstdev(values) if len(values) > 1 else 0.0
            return {"mean": round(mean, 6), "std": round(std, 6)}

        point = {
            "fraction": fraction,
            "train_rows_mean": round(sum(r["train_rows"] for r in per_seed) / len(per_seed), 1)
            if per_seed
            else None,
            "per_seed": per_seed,
        }
        for key in model_keys:
            point[key] = {
                "accuracy": mean_std(f"{key}_accuracy"),
                "macro_f1": mean_std(f"{key}_macro_f1"),
                "top2_accuracy": mean_std(f"{key}_top2"),
                "ece": mean_std(f"{key}_ece"),
            }
        points.append(point)

    # Trend judgment from best of model_keys by last accuracy.
    judgments = {}
    for key in model_keys:
        series = [p[key]["accuracy"]["mean"] for p in points if p[key]["accuracy"]["mean"] is not None]
        if len(series) < 2:
            judgments[key] = "unclear"
            continue
        gain = series[-1] - series[0]
        last_gain = series[-1] - series[-2] if len(series) >= 2 else 0.0
        if gain < 0.03 and abs(last_gain) < 0.02:
            judgments[key] = "saturated"
        elif last_gain > 0.01 or gain > 0.05:
            judgments[key] = "still_rising"
        else:
            judgments[key] = "unclear"

    return {
        "protocol": "direct_department_learning_curve",
        "threshold": threshold,
        "fractions": list(fractions),
        "seeds": list(seeds),
        "model_keys": list(model_keys),
        "points": points,
        "trend": judgments,
        "note": "no clinical-level extrapolation",
    }


def representation_ablation_from_matrix(matrix: Mapping[str, Any]) -> dict[str, Any]:
    """Compare representations using the already-run direct department matrix."""

    headline = matrix.get("aggregate", {}).get("headline") or {}
    keys = [
        "logistic_regression_binary",
        "tfidf_logistic_regression",
        "char_ngram_tfidf_lr",
        "word_char_fusion_lr",
        "three_state_lr",
        "linear_svm_binary",
        "multinomial_nb",
    ]
    table = []
    for key in keys:
        if key not in headline:
            continue
        table.append(
            {
                "model": key,
                "accuracy": headline[key]["accuracy"],
                "macro_f1": headline[key]["macro_f1"],
                "top2_accuracy": headline[key]["top2_accuracy"],
                "ece": headline[key]["ece"],
            }
        )
    # Classifier-fixed comparison: LR variants only.
    lr_keys = [
        "logistic_regression_binary",
        "tfidf_logistic_regression",
        "char_ngram_tfidf_lr",
        "word_char_fusion_lr",
        "three_state_lr",
    ]
    lr_table = [row for row in table if row["model"] in lr_keys]
    lr_table.sort(key=lambda row: -(row["accuracy"]["mean"] or 0))
    best_repr = lr_table[0]["model"] if lr_table else None
    return {
        "all_models": table,
        "lr_representation_ranking": lr_table,
        "best_representation_under_lr": best_repr,
        "answer_hint": (
            "固定 LR 后若 char/fusion 明显高于 binary，则提升来自文本表示；"
            "若接近，则提升主要来自分类器结构。"
        ),
    }
