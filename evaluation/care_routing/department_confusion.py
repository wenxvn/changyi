"""Department confusion analysis + targeted data gap map."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any, Mapping, Sequence

from evaluation.model.evaluate_grouped import near_duplicate_components

from .disease_department import department_for
from .round3_split_audit import quota_split


def department_confusion_report(
    y_true: Sequence[str],
    y_pred: Sequence[str | None],
    *,
    ranked_list: Sequence[Sequence[tuple[str, float]]] | None = None,
) -> dict[str, Any]:
    """Purely statistical department confusion; no invented medical rules."""

    n = len(y_true)
    confusion: dict[str, Counter[str]] = defaultdict(Counter)
    for true, pred in zip(y_true, y_pred):
        confusion[true][pred or "ABSTAIN"] += 1

    pairs = []
    for true_label, counts in confusion.items():
        for pred_label, count in counts.items():
            if pred_label == true_label or pred_label == "ABSTAIN":
                continue
            reverse = confusion.get(pred_label, Counter())[true_label]
            pairs.append(
                {
                    "true": true_label,
                    "pred": pred_label,
                    "count": count,
                    "reverse_count": reverse,
                    "bidirectional": reverse > 0,
                }
            )
    pairs.sort(key=lambda item: (-item["count"], item["true"], item["pred"]))

    per_dept = []
    for label in sorted(set(y_true)):
        total = sum(1 for t in y_true if t == label)
        tp = confusion[label][label]
        top_confusions = [
            {"pred": pred, "count": count}
            for pred, count in confusion[label].most_common()
            if pred != label
        ][:5]
        per_dept.append(
            {
                "department": label,
                "support": total,
                "recall": round(tp / total, 6) if total else 0.0,
                "top_confusions": top_confusions,
            }
        )
    per_dept.sort(key=lambda item: (item["recall"], -item["support"]))

    # Shared distinguishing features from train symptom stats if provided via ranked? skip.
    return {
        "test_rows": n,
        "top_confusion_pairs": pairs[:20],
        "per_department": per_dept,
        "lowest_recall_departments": [item for item in per_dept if item["support"] > 0][:10],
    }


def shared_symptom_stats(
    train_rows: Sequence[Mapping[str, Any]],
    department_a: str,
    department_b: str,
    *,
    top_k: int = 8,
) -> dict[str, Any]:
    """Statistical symptom overlap between two departments from train only."""

    def dept_symptoms(dept: str) -> Counter:
        counter: Counter = Counter()
        for row in train_rows:
            if department_for(row["disease"]) == dept:
                counter.update(row["symptoms"])
        return counter

    a = dept_symptoms(department_a)
    b = dept_symptoms(department_b)
    shared = sorted(set(a) & set(b), key=lambda s: -(a[s] + b[s]))[:top_k]
    only_a = sorted(set(a) - set(b), key=lambda s: -a[s])[:top_k]
    only_b = sorted(set(b) - set(a), key=lambda s: -b[s])[:top_k]
    return {
        "department_a": department_a,
        "department_b": department_b,
        "shared_top_symptoms": [
            {"symptom": s, "count_a": a[s], "count_b": b[s]} for s in shared
        ],
        "distinguishing_a": [{"symptom": s, "count": a[s]} for s in only_a],
        "distinguishing_b": [{"symptom": s, "count": b[s]} for s in only_b],
        "note": "train statistics only; not clinical rules",
    }


def data_gap_map(
    rows: Sequence[Mapping[str, Any]],
    *,
    y_true: Sequence[str] | None = None,
    y_pred: Sequence[str | None] | None = None,
    per_department_recall: Mapping[str, float] | None = None,
    learning_curve_slopes: Mapping[str, float] | None = None,
    threshold: float = 0.8,
    seed: int = 42,
) -> dict[str, Any]:
    """Model-data priority map. Explicitly NOT a clinical importance ranking."""

    train, cal, test, meta = quota_split(rows, threshold=threshold, seed=seed)
    components, _ = near_duplicate_components(list(rows), mode="same_label", threshold=threshold)
    comp_by_dept: Counter = Counter()
    for component in components:
        comp_by_dept[department_for(rows[component[0]]["disease"])] += 1

    train_by_dept = Counter(department_for(row["disease"]) for row in train)
    test_by_dept = Counter(department_for(row["disease"]) for row in test)
    confusion: dict[str, Counter[str]] = defaultdict(Counter)
    if y_true is not None and y_pred is not None:
        for true, pred in zip(y_true, y_pred):
            if true != pred:
                confusion[true][pred or "ABSTAIN"] += 1

    # Unseen symptom ratio on test vs train per department.
    train_symptoms_by_dept: dict[str, set[str]] = defaultdict(set)
    for row in train:
        train_symptoms_by_dept[department_for(row["disease"])].update(row["symptoms"])
    unseen: dict[str, float] = {}
    for row in test:
        dept = department_for(row["disease"])
        symptoms = row["symptoms"]
        if not symptoms:
            continue
        missing = [s for s in symptoms if s not in train_symptoms_by_dept[dept]]
        unseen.setdefault(dept, 0.0)
        # average later
    # recompute properly
    unseen_counts: dict[str, list[float]] = defaultdict(list)
    for row in test:
        dept = department_for(row["disease"])
        symptoms = row["symptoms"]
        if not symptoms:
            continue
        missing = [s for s in symptoms if s not in train_symptoms_by_dept[dept]]
        unseen_counts[dept].append(len(missing) / len(symptoms))
    for dept, values in unseen_counts.items():
        unseen[dept] = round(sum(values) / len(values), 6)

    entries = []
    departments = sorted(set(train_by_dept) | set(test_by_dept))
    for dept in departments:
        recall = None
        if per_department_recall:
            recall = per_department_recall.get(dept)
        top_confusions = [
            {"pred": pred, "count": count}
            for pred, count in confusion.get(dept, Counter()).most_common(3)
        ]
        slope = (learning_curve_slopes or {}).get(dept)
        # Priority score: low recall, high confusion, few components, rising curve.
        priority = 0.0
        if recall is not None:
            priority += (1.0 - recall) * 3.0
        priority += min(sum(item["count"] for item in top_confusions) / 10.0, 1.5)
        components_n = comp_by_dept.get(dept, 0)
        if components_n <= 3:
            priority += 1.0
        if slope is not None and slope > 0.02:
            priority += 0.8
        entries.append(
            {
                "department": dept,
                "train_count": train_by_dept.get(dept, 0),
                "component_count": components_n,
                "test_count": test_by_dept.get(dept, 0),
                "recall": recall,
                "top_confusions": top_confusions,
                "unseen_symptom_ratio": unseen.get(dept),
                "learning_curve_slope": slope,
                "data_priority_score": round(priority, 4),
            }
        )
    entries.sort(key=lambda item: (-item["data_priority_score"], item["department"]))
    for index, entry in enumerate(entries, start=1):
        entry["priority_rank"] = index

    return {
        "threshold": threshold,
        "seed": seed,
        "disclaimer": "模型数据优先级，不是医疗重要性排名",
        "departments": entries,
        "top_n_to_collect": [
            {
                "department": entry["department"],
                "reason": (
                    f"recall={entry['recall']}, components={entry['component_count']}, "
                    f"top_confusions={entry['top_confusions'][:2]}"
                ),
            }
            for entry in entries[:10]
        ],
    }
