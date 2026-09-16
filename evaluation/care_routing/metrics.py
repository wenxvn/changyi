"""Shared metric helpers for care-routing experiments."""

from __future__ import annotations

import math
from collections import Counter, defaultdict
from typing import Any, Mapping, Sequence

from .disease_department import department_for
from .uncertainty import (
    expected_calibration_error,
    predict_distribution,
    top1_confidence,
    distribution_entropy,
    should_clarify,
)


def accuracy(rows: Sequence[bool]) -> float:
    return round(sum(1 for item in rows if item) / len(rows), 6) if rows else 0.0


def macro_f1(y_true: Sequence[str], y_pred: Sequence[str | None]) -> dict[str, float]:
    labels = sorted(set(y_true) | {item for item in y_pred if item})
    per_class = {}
    for label in labels:
        tp = sum(1 for t, p in zip(y_true, y_pred) if t == label and p == label)
        fp = sum(1 for t, p in zip(y_true, y_pred) if t != label and p == label)
        fn = sum(1 for t, p in zip(y_true, y_pred) if t == label and p != label)
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        per_class[label] = round(f1, 6)
    macro = round(sum(per_class.values()) / len(per_class), 6) if per_class else 0.0
    return {"macro_f1": macro, "per_class_f1": per_class}


def evaluate_uncertainty_split(
    model: Mapping[str, Any],
    rows: Sequence[Mapping[str, Any]],
    *,
    temperature: float = 1.0,
    conformal: Mapping[str, Any] | None = None,
    confidence_threshold: float = 0.55,
    entropy_ratio_threshold: float = 0.55,
) -> dict[str, Any]:
    confidences: list[float] = []
    correct_flags: list[bool] = []
    entropies: list[float] = []
    y_true: list[str] = []
    y_pred: list[str | None] = []
    dept_true: list[str] = []
    dept_pred: list[str | None] = []
    set_sizes: list[int] = []
    clarify_flags: list[bool] = []
    coverage_flags: list[bool] = []
    error_by_conf: dict[str, list[bool]] = defaultdict(list)

    from .uncertainty import prediction_set as conformal_set

    for row in rows:
        ranked = predict_distribution(model, row["symptoms"], temperature=temperature)
        if not ranked:
            confidences.append(0.0)
            correct_flags.append(False)
            entropies.append(0.0)
            y_true.append(row["disease"])
            y_pred.append(None)
            dept_true.append(department_for(row["disease"]))
            dept_pred.append(None)
            set_sizes.append(0)
            clarify_flags.append(True)
            coverage_flags.append(False)
            continue
        confidence = top1_confidence(ranked)
        entropy = distribution_entropy(ranked)
        correct = ranked[0][0] == row["disease"]
        confidences.append(confidence)
        correct_flags.append(correct)
        entropies.append(entropy)
        y_true.append(row["disease"])
        y_pred.append(ranked[0][0])
        dept_true.append(department_for(row["disease"]))
        dept_pred.append(department_for(ranked[0][0]))

        if conformal:
            items = conformal_set(ranked, conformal)
            in_set = [item["disease"] for item in items if item["in_set"]]
            coverage_flags.append(row["disease"] in in_set)
        else:
            in_set = [label for label, _ in ranked[:3]]
            coverage_flags.append(row["disease"] in in_set)
        set_sizes.append(len(in_set))
        max_entropy = math.log2(len(ranked)) if len(ranked) > 1 else 0.0
        clarify = should_clarify(
            entropy=entropy,
            confidence=confidence,
            set_size=len(in_set),
            max_entropy=max_entropy,
            confidence_threshold=confidence_threshold,
            entropy_ratio_threshold=entropy_ratio_threshold,
        )
        clarify_flags.append(clarify)
        bucket = f"{int(confidence * 10) / 10:.1f}"
        error_by_conf[bucket].append(correct)

    ece = expected_calibration_error(confidences, correct_flags)
    disease_f1 = macro_f1(y_true, y_pred)
    dept_f1 = macro_f1(dept_true, dept_pred)
    clarify_correct = [c for c, clarify in zip(correct_flags, clarify_flags) if clarify]
    clarify_wrong = [c for c, clarify in zip(correct_flags, clarify_flags) if clarify]
    # Among clarified: accuracy should be lower (we target hard cases).
    # Among non-clarified: accuracy should be higher (confident path).
    non_clarify = [c for c, clarify in zip(correct_flags, clarify_flags) if not clarify]

    error_conf_table = []
    for bucket, flags in sorted(error_by_conf.items()):
        error_conf_table.append(
            {
                "confidence_bucket": bucket,
                "n": len(flags),
                "accuracy": accuracy(flags),
                "error_rate": round(1.0 - accuracy(flags), 6),
            }
        )

    return {
        "test_rows": len(rows),
        "accuracy": accuracy(correct_flags),
        "department_accuracy": accuracy([t == p for t, p in zip(dept_true, dept_pred)]),
        "macro_f1": disease_f1["macro_f1"],
        "department_macro_f1": dept_f1["macro_f1"],
        "ece": ece["ece"],
        "ece_bins": ece["bins"],
        "mean_confidence": round(sum(confidences) / len(confidences), 6) if confidences else 0.0,
        "mean_entropy": round(sum(entropies) / len(entropies), 6) if entropies else 0.0,
        "mean_prediction_set_size": round(sum(set_sizes) / len(set_sizes), 6) if set_sizes else 0.0,
        "coverage": accuracy(coverage_flags),
        "should_clarify_rate": round(sum(clarify_flags) / len(clarify_flags), 6) if clarify_flags else 0.0,
        "accuracy_when_clarified": accuracy(clarify_correct) if clarify_flags and any(clarify_flags) else None,
        "accuracy_when_not_clarified": accuracy(non_clarify) if non_clarify else None,
        "error_vs_confidence": error_conf_table,
        "temperature": temperature,
        "conformal_alpha": None if not conformal else conformal.get("alpha"),
    }


def summarize_inquiry_runs(runs: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    completed = [run for run in runs if not run.get("skipped")]
    if not completed:
        return {
            "cases": 0,
            "initial_accuracy": None,
            "final_accuracy": None,
            "accuracy_delta": None,
            "average_questions": None,
            "mean_initial_entropy": None,
            "mean_final_entropy": None,
            "mean_entropy_reduction": None,
            "stop_reasons": {},
        }
    initial_correct = [bool(run["initial"]["correct"]) for run in completed]
    final_correct = [bool(run["final"]["correct"]) for run in completed]
    questions = [int(run["questions_asked"]) for run in completed]
    initial_h = [float(run["initial"]["entropy"]) for run in completed]
    final_h = [float(run["final"]["entropy"]) for run in completed]
    reductions = [float(run["final"]["entropy_reduction_total"]) for run in completed]
    stop_reasons = Counter(run.get("stop_reason", "unknown") for run in completed)
    return {
        "cases": len(completed),
        "initial_accuracy": accuracy(initial_correct),
        "final_accuracy": accuracy(final_correct),
        "accuracy_delta": round(accuracy(final_correct) - accuracy(initial_correct), 6),
        "average_questions": round(sum(questions) / len(questions), 6),
        "questions_distribution": dict(Counter(questions)),
        "mean_initial_entropy": round(sum(initial_h) / len(initial_h), 6),
        "mean_final_entropy": round(sum(final_h) / len(final_h), 6),
        "mean_entropy_reduction": round(sum(reductions) / len(reductions), 6),
        "stop_reasons": dict(stop_reasons),
    }
