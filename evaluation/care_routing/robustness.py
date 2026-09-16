"""Robustness simulation under meaning-preserving text/symptom perturbations.

All perturbations are labeled ``robustness_simulation`` and never retrain on
perturbed test items.
"""

from __future__ import annotations

import random
from typing import Any, Mapping, Sequence

from data.symptom_disease_model.train import fit

from evaluation.model.evaluate_grouped import ALPHA, MIN_SYMPTOM_DF

from .model_baselines import (
    build_binary_features,
    fit_linear_svm,
    fit_logistic_regression,
    predict_proba,
)
from .round3_models import summarize_predictions
from .round3_split_audit import quota_split
from .uncertainty import predict_distribution


# Meaning-preserving synonym map on standard codes (not free text rewriting).
# Used only to stress the classifier input representation.
SYNONYM_CODE_SWAPS: dict[str, list[str]] = {
    "high_fever": ["mild_fever"],
    "mild_fever": ["high_fever"],
    "cough": ["phlegm"],
    "phlegm": ["cough"],
    "headache": ["dizziness"],
    "dizziness": ["headache"],
    "vomiting": ["nausea"],
    "nausea": ["vomiting"],
    "joint_pain": ["back_pain"],
    "back_pain": ["joint_pain"],
}

# Non-red-flag filler codes that should not change the true label.
FILLER_CODES = ["fatigue", "malaise", "loss_of_appetite"]


def perturb_symptoms(
    symptoms: Sequence[str],
    *,
    kind: str,
    rng: random.Random,
) -> list[str]:
    items = list(symptoms)
    if not items:
        return items
    if kind == "order_shuffle":
        shuffled = items[:]
        rng.shuffle(shuffled)
        return shuffled
    if kind == "synonym_swap":
        out = []
        used = False
        for code in items:
            if not used and code in SYNONYM_CODE_SWAPS:
                out.append(rng.choice(SYNONYM_CODE_SWAPS[code]))
                used = True
            else:
                out.append(code)
        return out
    if kind == "drop_noncritical":
        if len(items) <= 2:
            return items
        drop_index = rng.randrange(len(items))
        return [code for i, code in enumerate(items) if i != drop_index]
    if kind == "add_filler":
        filler = rng.choice(FILLER_CODES)
        if filler not in items:
            return items + [filler]
        return items
    if kind == "colloquial_noise":
        # Simulate noisy extraction: drop one token with 50% and add filler with 50%.
        out = items[:]
        if len(out) > 2 and rng.random() < 0.5:
            out.pop(rng.randrange(len(out)))
        if rng.random() < 0.5:
            filler = rng.choice(FILLER_CODES)
            if filler not in out:
                out.append(filler)
        return out
    return items


def run_robustness(
    rows: Sequence[Mapping[str, Any]],
    *,
    seed: int = 42,
    threshold: float = 0.8,
    kinds: Sequence[str] = (
        "order_shuffle",
        "synonym_swap",
        "drop_noncritical",
        "add_filler",
        "colloquial_noise",
    ),
) -> dict[str, Any]:
    train, cal, test, meta = quota_split(rows, threshold=threshold, seed=seed)
    if not test:
        return {"error": "empty_test"}
    y_train = [row["disease"] for row in train]
    y_test = [row["disease"] for row in test]

    nb = fit(train, ALPHA, MIN_SYMPTOM_DF)
    train_bin = build_binary_features(train)
    test_bin = build_binary_features(test)
    lr = fit_logistic_regression(train_bin, y_train, epochs=50, lr=0.4, seed=seed)
    svm = fit_linear_svm(train_bin, y_train, epochs=60, lr=0.15, seed=seed)

    def predict_model(model_name: str, feature_rows: Sequence[Mapping[str, Any]]):
        if model_name == "nb":
            return [predict_distribution(nb, row["symptoms"]) for row in feature_rows]
        feats = build_binary_features(feature_rows)
        if model_name == "lr":
            return [predict_proba(lr, feat) for feat in feats]
        return [predict_proba(svm, feat) for feat in feats]

    clean = {
        name: summarize_predictions(predict_model(name, test), y_test)
        for name in ("nb", "lr", "svm")
    }

    rng = random.Random(seed)
    per_kind: dict[str, Any] = {}
    for kind in kinds:
        perturbed_rows = []
        for row in test:
            symptoms = perturb_symptoms(row["symptoms"], kind=kind, rng=rng)
            # Order-only perturbation for bag-of-tags models is a no-op by design.
            if kind == "order_shuffle":
                symptoms = list(row["symptoms"])
            perturbed_rows.append({"disease": row["disease"], "symptoms": symptoms})
        kind_metrics = {}
        for name in ("nb", "lr", "svm"):
            summary = summarize_predictions(predict_model(name, perturbed_rows), y_test)
            drop = round(clean[name]["accuracy"] - summary["accuracy"], 6)
            dept_drop = round(
                clean[name]["department_accuracy"] - summary["department_accuracy"], 6
            )
            kind_metrics[name] = {
                "accuracy": summary["accuracy"],
                "department_accuracy": summary["department_accuracy"],
                "robustness_drop_accuracy": drop,
                "robustness_drop_department": dept_drop,
                "macro_f1": summary["macro_f1"],
            }
        per_kind[kind] = kind_metrics

    # Aggregate worst-case drop per model.
    worst = {}
    for name in ("nb", "lr", "svm"):
        drops = [per_kind[kind][name]["robustness_drop_accuracy"] for kind in per_kind]
        worst[name] = {
            "mean_drop": round(sum(drops) / len(drops), 6) if drops else None,
            "max_drop": round(max(drops), 6) if drops else None,
        }

    return {
        "protocol": "robustness_simulation",
        "not_real_patients": True,
        "seed": seed,
        "threshold": threshold,
        "test_rows": len(test),
        "clean": {name: {k: clean[name][k] for k in ("accuracy", "department_accuracy", "macro_f1")} for name in clean},
        "per_kind": per_kind,
        "worst_case": worst,
        "notes": [
            "order_shuffle 对 bag-of-tags 模型应为 0 drop（表示层置换不变）",
            "禁止用扰动样本回训后再在同一扰动集上测试",
            "红旗语义未被扰动生成器修改",
        ],
    }
