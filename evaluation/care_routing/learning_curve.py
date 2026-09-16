"""Learning-curve experiments: does more data close the NB vs LR gap?"""

from __future__ import annotations

import random
import statistics
from collections import defaultdict
from typing import Any, Mapping, Sequence

from data.symptom_disease_model.train import fit

from evaluation.model.evaluate_grouped import ALPHA, MIN_SYMPTOM_DF, near_duplicate_components

from .model_baselines import (
    build_binary_features,
    build_tfidf_features,
    fit_linear_svm,
    fit_logistic_regression,
    predict_proba,
)
from .round3_split_audit import quota_split
from .round3_models import macro_f1, summarize_predictions
from .uncertainty import predict_distribution


def _subset_by_fraction(
    train_rows: Sequence[Mapping[str, Any]],
    fraction: float,
    seed: int,
) -> list[dict[str, Any]]:
    """Subsample train by whole disease groups when possible, else by rows."""

    if fraction >= 0.999:
        return list(train_rows)
    rng = random.Random(seed)
    by_disease: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in train_rows:
        by_disease[row["disease"]].append(row)
    selected: list[dict[str, Any]] = []
    target = max(1, int(round(len(train_rows) * fraction)))
    diseases = sorted(by_disease)
    rng.shuffle(diseases)
    # Round-robin take rows so all diseases remain represented when fraction allows.
    pointers = {disease: 0 for disease in diseases}
    order = diseases
    while len(selected) < target:
        progressed = False
        for disease in order:
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


def learning_curve(
    rows: Sequence[Mapping[str, Any]],
    *,
    fractions: Sequence[float] = (0.2, 0.4, 0.6, 0.8, 1.0),
    seeds: Sequence[int] = (42, 123, 2026),
    threshold: float = 0.8,
) -> dict[str, Any]:
    points: list[dict[str, Any]] = []
    for fraction in fractions:
        per_seed = []
        for seed in seeds:
            train, cal, test, meta = quota_split(rows, threshold=threshold, seed=seed)
            if not test:
                continue
            subset = _subset_by_fraction(train, fraction, seed)
            y_train = [row["disease"] for row in subset]
            y_test = [row["disease"] for row in test]

            nb = fit(subset, ALPHA, MIN_SYMPTOM_DF)
            nb_ranked = [predict_distribution(nb, row["symptoms"]) for row in test]
            nb_sum = summarize_predictions(nb_ranked, y_test)

            train_bin = build_binary_features(subset)
            test_bin = build_binary_features(test)
            lr = fit_logistic_regression(train_bin, y_train, epochs=50, lr=0.4, seed=seed)
            lr_ranked = [predict_proba(lr, feat) for feat in test_bin]
            lr_sum = summarize_predictions(lr_ranked, y_test)

            svm = fit_linear_svm(train_bin, y_train, epochs=60, lr=0.15, seed=seed)
            svm_ranked = [predict_proba(svm, feat) for feat in test_bin]
            svm_sum = summarize_predictions(svm_ranked, y_test)

            per_seed.append(
                {
                    "seed": seed,
                    "train_rows": len(subset),
                    "test_rows": len(test),
                    "test_diseases": len({row["disease"] for row in test}),
                    "nb_accuracy": nb_sum["accuracy"],
                    "nb_department_accuracy": nb_sum["department_accuracy"],
                    "nb_macro_f1": nb_sum["macro_f1"],
                    "lr_accuracy": lr_sum["accuracy"],
                    "lr_department_accuracy": lr_sum["department_accuracy"],
                    "lr_macro_f1": lr_sum["macro_f1"],
                    "svm_accuracy": svm_sum["accuracy"],
                    "svm_department_accuracy": svm_sum["department_accuracy"],
                    "svm_macro_f1": svm_sum["macro_f1"],
                }
            )

        def mean_std(key: str) -> dict[str, Any]:
            values = [row[key] for row in per_seed if row.get(key) is not None]
            if not values:
                return {"mean": None, "std": None}
            mean = sum(values) / len(values)
            std = statistics.pstdev(values) if len(values) > 1 else 0.0
            return {"mean": round(mean, 6), "std": round(std, 6)}

        points.append(
            {
                "fraction": fraction,
                "seeds": [row["seed"] for row in per_seed],
                "train_rows_mean": round(
                    sum(row["train_rows"] for row in per_seed) / len(per_seed), 1
                )
                if per_seed
                else None,
                "test_rows_mean": round(
                    sum(row["test_rows"] for row in per_seed) / len(per_seed), 1
                )
                if per_seed
                else None,
                "nb_accuracy": mean_std("nb_accuracy"),
                "lr_accuracy": mean_std("lr_accuracy"),
                "svm_accuracy": mean_std("svm_accuracy"),
                "nb_department_accuracy": mean_std("nb_department_accuracy"),
                "lr_department_accuracy": mean_std("lr_department_accuracy"),
                "svm_department_accuracy": mean_std("svm_department_accuracy"),
                "nb_macro_f1": mean_std("nb_macro_f1"),
                "lr_macro_f1": mean_std("lr_macro_f1"),
                "svm_macro_f1": mean_std("svm_macro_f1"),
                "per_seed": per_seed,
            }
        )

    # Slope heuristic: last vs first point for LR and NB.
    def slope(model_key: str) -> float | None:
        if len(points) < 2:
            return None
        first = points[0][model_key]["mean"]
        last = points[-1][model_key]["mean"]
        if first is None or last is None:
            return None
        return round(last - first, 6)

    return {
        "threshold": threshold,
        "fractions": list(fractions),
        "seeds": list(seeds),
        "points": points,
        "accuracy_gain_20_to_100": {
            "nb": slope("nb_accuracy"),
            "lr": slope("lr_accuracy"),
            "svm": slope("svm_accuracy"),
        },
        "csv_ready": [
            {
                "fraction": point["fraction"],
                "nb_acc_mean": point["nb_accuracy"]["mean"],
                "nb_acc_std": point["nb_accuracy"]["std"],
                "lr_acc_mean": point["lr_accuracy"]["mean"],
                "lr_acc_std": point["lr_accuracy"]["std"],
                "svm_acc_mean": point["svm_accuracy"]["mean"],
                "svm_acc_std": point["svm_accuracy"]["std"],
                "lr_dept_mean": point["lr_department_accuracy"]["mean"],
                "nb_dept_mean": point["nb_department_accuracy"]["mean"],
            }
            for point in points
        ],
        "interpretation_hint": (
            "若 20%→100% 曲线仍陡峭，说明补数据收益大；"
            "若早早平台且 LR≫NB，说明模型结构差异稳定存在。"
        ),
    }
