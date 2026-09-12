"""Evaluate the symptom model with random and grouped leakage-aware splits.

The runtime model remains unchanged.  This module creates committed evidence
artifacts so the Trust Center can show the existing random baseline next to a
strict fingerprint-grouped result.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from data.symptom_disease_model.train import fit, load_dataset, predict, split_dataset


DEFAULT_DATASET = Path("data/symptom_disease_model/data/disease_symptom_structured_41diseases_long.csv")
DEFAULT_MODEL = Path("data/symptom_disease_model/models/symptom_disease_41_nb.json")
DEFAULT_MANIFEST = Path("evaluation/model/split_manifest.json")
DEFAULT_REPORT = Path("evaluation/model/grouped_split_report.json")
TEST_SIZE = 0.25
SEED = 42
ALPHA = 1.0
MIN_SYMPTOM_DF = 2
ABSTAIN_THRESHOLD = 0.35


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def symptom_fingerprint(row: dict[str, Any]) -> str:
    canonical = "|".join(sorted(set(row["symptoms"])))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def grouped_fingerprint_split(
    rows: list[dict[str, Any]],
    test_size: float,
    seed: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, list[str]]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[symptom_fingerprint(row)].append(row)

    by_disease: dict[str, list[str]] = defaultdict(list)
    for fingerprint, group_rows in groups.items():
        by_disease[group_rows[0]["disease"]].append(fingerprint)

    rng = random.Random(seed)
    train_groups: list[str] = []
    test_groups: list[str] = []
    for disease in sorted(by_disease):
        fingerprints = sorted(by_disease[disease])
        rng.shuffle(fingerprints)
        if len(fingerprints) == 1:
            train_groups.extend(fingerprints)
            continue
        test_count = max(1, round(len(fingerprints) * test_size))
        test_count = min(test_count, len(fingerprints) - 1)
        test_groups.extend(fingerprints[:test_count])
        train_groups.extend(fingerprints[test_count:])

    train_set, test_set = set(train_groups), set(test_groups)
    if train_set & test_set:
        raise AssertionError("fingerprint group leakage detected")
    train = [row for row in rows if symptom_fingerprint(row) in train_set]
    test = [row for row in rows if symptom_fingerprint(row) in test_set]
    rng.shuffle(train)
    rng.shuffle(test)
    return train, test, {
        "train": sorted(train_set),
        "test": sorted(test_set),
    }


def evaluate_metrics(model: dict[str, Any], rows: list[dict[str, Any]]) -> dict[str, Any]:
    labels = sorted(set(model.get("classes") or []) | {row["disease"] for row in rows})
    confusion: dict[str, Counter[str]] = {label: Counter() for label in labels}
    per_class_total = Counter()
    correct = covered_correct = top3_correct = covered = 0

    for row in rows:
        ranked = predict(model, row["symptoms"], top_k=3)
        ranked_labels = [label for label, _ in ranked]
        predicted = ranked_labels[0] if ranked_labels else None
        confidence = float(ranked[0][1]) if ranked else 0.0
        abstained = not predicted or confidence < ABSTAIN_THRESHOLD
        per_class_total[row["disease"]] += 1
        correct += predicted == row["disease"]
        if not abstained:
            covered += 1
            covered_correct += predicted == row["disease"]
            confusion[row["disease"]][predicted] += 1
        else:
            confusion[row["disease"]]["ABSTAIN"] += 1
        top3_correct += row["disease"] in ranked_labels

    present_labels = sorted(label for label in labels if per_class_total[label] > 0)
    per_class_recall = {}
    per_class_precision = {}
    per_class_f1 = {}
    for label in present_labels:
        true_positive = confusion[label][label]
        false_negative = per_class_total[label] - true_positive
        false_positive = sum(row_counts[label] for true_label, row_counts in confusion.items() if true_label != label)
        recall = true_positive / per_class_total[label] if per_class_total[label] else 0.0
        precision = true_positive / (true_positive + false_positive) if true_positive + false_positive else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        per_class_recall[label] = round(recall, 6)
        per_class_precision[label] = round(precision, 6)
        per_class_f1[label] = round(f1, 6)

    row_count = len(rows)
    macro_precision = sum(per_class_precision.values()) / len(present_labels) if present_labels else 0.0
    macro_recall = sum(per_class_recall.values()) / len(present_labels) if present_labels else 0.0
    macro_f1 = sum(per_class_f1.values()) / len(present_labels) if present_labels else 0.0
    return {
        "test_rows": row_count,
        "present_class_count": len(present_labels),
        "accuracy": round(correct / row_count, 6) if row_count else None,
        "covered_accuracy": round(covered_correct / covered, 6) if covered else None,
        "top3_accuracy": round(top3_correct / row_count, 6) if row_count else None,
        "macro_precision": round(macro_precision, 6),
        "macro_recall": round(macro_recall, 6),
        "macro_f1": round(macro_f1, 6),
        "per_class_recall": per_class_recall,
        "confusion_matrix": {label: dict(sorted(counts.items())) for label, counts in confusion.items() if per_class_total[label] > 0},
        "coverage": round(covered / row_count, 6) if row_count else 0.0,
        "abstention_rate": round((row_count - covered) / row_count, 6) if row_count else 0.0,
        "abstention_policy": {
            "confidence_threshold": ABSTAIN_THRESHOLD,
            "description": "top-1 probability below threshold is withheld from the assistive disease display",
        },
        "metric_scope": "macro metrics average only classes present in this test split",
    }


def near_duplicate_audit(rows: list[dict[str, Any]], threshold: float = 0.8) -> dict[str, Any]:
    pairs = cross_label_pairs = 0
    for left, right in itertools.combinations(rows, 2):
        left_set, right_set = set(left["symptoms"]), set(right["symptoms"])
        union = left_set | right_set
        jaccard = len(left_set & right_set) / len(union) if union else 1.0
        if jaccard >= threshold:
            pairs += 1
            cross_label_pairs += left["disease"] != right["disease"]
    return {
        "jaccard_threshold": threshold,
        "pair_count": pairs,
        "cross_label_pair_count": cross_label_pairs,
        "note": "近重复审计不改变训练模型；exact fingerprint 分组保证完全相同症状集合不跨 split。",
    }


def jaccard(left: set[str], right: set[str]) -> float:
    union = left | right
    return len(left & right) / len(union) if union else 1.0


class _UnionFind:
    def __init__(self, size: int) -> None:
        self.parent = list(range(size))
        self.rank = [0] * size

    def find(self, value: int) -> int:
        while self.parent[value] != value:
            self.parent[value] = self.parent[self.parent[value]]
            value = self.parent[value]
        return value

    def union(self, left: int, right: int) -> None:
        left_root, right_root = self.find(left), self.find(right)
        if left_root == right_root:
            return
        if self.rank[left_root] < self.rank[right_root]:
            self.parent[left_root] = right_root
        elif self.rank[left_root] > self.rank[right_root]:
            self.parent[right_root] = left_root
        else:
            self.parent[right_root] = left_root
            self.rank[left_root] += 1


def near_duplicate_components(
    rows: list[dict[str, Any]],
    threshold: float = 0.8,
    mode: str = "same_label",
) -> tuple[list[list[int]], dict[str, Any]]:
    """Build connected components over near-duplicate symptom sets.

    mode="same_label" only links pairs that share the disease label so one giant
    cross-disease component cannot collapse the dataset. mode="global" links any
    pair above the Jaccard threshold and is reported for comparison.
    """

    symptom_sets = [set(row["symptoms"]) for row in rows]
    labels = [row["disease"] for row in rows]
    uf = _UnionFind(len(rows))
    edge_count = 0
    cross_label_edge_count = 0
    for left, right in itertools.combinations(range(len(rows)), 2):
        score = jaccard(symptom_sets[left], symptom_sets[right])
        if score < threshold:
            continue
        cross = labels[left] != labels[right]
        if mode == "same_label" and cross:
            continue
        uf.union(left, right)
        edge_count += 1
        if cross:
            cross_label_edge_count += 1

    buckets: dict[int, list[int]] = defaultdict(list)
    for index in range(len(rows)):
        buckets[uf.find(index)].append(index)
    components = sorted(buckets.values(), key=lambda item: (-len(item), item[0]))
    stats = {
        "mode": mode,
        "jaccard_threshold": threshold,
        "sample_count": len(rows),
        "component_count": len(components),
        "largest_component_size": max((len(item) for item in components), default=0),
        "edge_count": edge_count,
        "cross_label_edge_count": cross_label_edge_count,
        "singleton_count": sum(1 for item in components if len(item) == 1),
    }
    return components, stats


def component_grouped_split(
    rows: list[dict[str, Any]],
    components: list[list[int]],
    test_size: float,
    seed: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, list[int]]]:
    """Assign whole near-duplicate components to train/test by row quota.

    Starts with all components in train, then moves whole components to test
    while keeping at least one component and a minimal train footprint for each
    disease. Smaller components are preferred for test so a disease's dominant
    near-duplicate cluster is not stripped out of training.
    """

    rng = random.Random(seed)
    by_disease: dict[str, list[list[int]]] = defaultdict(list)
    for component in components:
        by_disease[rows[component[0]]["disease"]].append(component)

    moved_to_test: set[int] = set()
    target_test_rows = max(1, round(len(rows) * test_size))
    test_rows = 0
    candidates = list(components)
    rng.shuffle(candidates)
    candidates.sort(key=lambda item: len(item))

    for component in candidates:
        if test_rows >= target_test_rows:
            break
        disease = rows[component[0]]["disease"]
        disease_components = by_disease[disease]
        if len(disease_components) <= 1:
            continue
        remaining = [item for item in disease_components if id(item) not in moved_to_test]
        if len(remaining) <= 1:
            continue
        remaining_rows = sum(len(item) for item in remaining)
        if remaining_rows - len(component) < max(2, round(0.4 * remaining_rows)):
            continue
        moved_to_test.add(id(component))
        test_rows += len(component)

    train_indices: list[int] = []
    test_indices: list[int] = []
    for component in components:
        if id(component) in moved_to_test:
            test_indices.extend(component)
        else:
            train_indices.extend(component)

    train_set, test_set = set(train_indices), set(test_indices)
    if train_set & test_set:
        raise AssertionError("near-duplicate component leakage detected")
    if not test_indices:
        raise AssertionError("near-duplicate split produced an empty test set")
    train = [rows[index] for index in train_indices]
    test = [rows[index] for index in test_indices]
    rng.shuffle(train)
    rng.shuffle(test)
    return train, test, {
        "train": sorted(train_set),
        "test": sorted(test_set),
    }


def cross_split_near_duplicate_count(
    train: list[dict[str, Any]],
    test: list[dict[str, Any]],
    threshold: float = 0.8,
) -> dict[str, int]:
    pair_count = 0
    cross_label = 0
    for left_row in train:
        left_set = set(left_row["symptoms"])
        for right_row in test:
            if jaccard(left_set, set(right_row["symptoms"])) >= threshold:
                pair_count += 1
                if left_row["disease"] != right_row["disease"]:
                    cross_label += 1
    return {
        "pair_count": pair_count,
        "cross_label_pair_count": cross_label,
    }


def assign_components_to_folds(
    rows: list[dict[str, Any]],
    components: list[list[int]],
    n_folds: int,
    seed: int,
) -> list[int]:
    """Assign each whole near-duplicate component to exactly one fold."""

    rng = random.Random(seed)
    by_disease: dict[str, list[list[int]]] = defaultdict(list)
    for component in components:
        by_disease[rows[component[0]]["disease"]].append(component)

    fold_of_index = [0] * len(rows)
    fold_row_counts = [0] * n_folds
    for disease in sorted(by_disease):
        disease_components = sorted(by_disease[disease], key=lambda item: (-len(item), item[0]))
        rng.shuffle(disease_components)
        disease_components.sort(key=lambda item: -len(item))
        for component in disease_components:
            fold = min(range(n_folds), key=lambda index: (fold_row_counts[index], index))
            for row_index in component:
                fold_of_index[row_index] = fold
            fold_row_counts[fold] += len(component)
    return fold_of_index


def grouped_cross_validation(
    rows: list[dict[str, Any]],
    components: list[list[int]],
    n_folds: int = 5,
    seed: int = SEED,
    threshold: float = 0.8,
) -> dict[str, Any]:
    """Run component-grouped k-fold CV with no same-component leakage."""

    if n_folds < 2:
        raise ValueError("n_folds must be >= 2")
    fold_of_index = assign_components_to_folds(rows, components, n_folds, seed)
    folds: list[dict[str, Any]] = []
    metric_keys = (
        "top1_accuracy",
        "top3_accuracy",
        "macro_precision",
        "macro_recall",
        "macro_f1",
        "coverage",
        "abstention_rate",
    )
    weighted_sums = {key: 0.0 for key in metric_keys}
    weighted_rows = 0
    all_present_classes: set[str] = set()
    max_cross_split = 0

    for fold_id in range(n_folds):
        train_indices = [index for index, assigned in enumerate(fold_of_index) if assigned != fold_id]
        validation_indices = [index for index, assigned in enumerate(fold_of_index) if assigned == fold_id]
        if not validation_indices:
            raise AssertionError(f"fold {fold_id} has no validation rows")
        if not train_indices:
            raise AssertionError(f"fold {fold_id} has no train rows")
        train_rows = [rows[index] for index in train_indices]
        validation_rows = [rows[index] for index in validation_indices]
        train_components = {
            component_id
            for component_id, component in enumerate(components)
            if fold_of_index[component[0]] != fold_id
        }
        validation_components = {
            component_id
            for component_id, component in enumerate(components)
            if fold_of_index[component[0]] == fold_id
        }
        if train_components & validation_components:
            raise AssertionError("near-duplicate component leakage across CV folds")
        model = fit(train_rows, ALPHA, MIN_SYMPTOM_DF)
        metrics = evaluate_metrics(model, validation_rows)
        cross = cross_split_near_duplicate_count(train_rows, validation_rows, threshold)
        if cross["pair_count"] > max_cross_split:
            max_cross_split = cross["pair_count"]
        present_classes = sorted(metrics.get("per_class_recall") or {})
        all_present_classes.update(present_classes)
        fold_payload = {
            "fold": fold_id + 1,
            "train_rows": len(train_rows),
            "validation_rows": len(validation_rows),
            "present_class_count": metrics["present_class_count"],
            "present_classes": present_classes,
            "top1_accuracy": metrics["accuracy"],
            "top3_accuracy": metrics["top3_accuracy"],
            "macro_precision": metrics["macro_precision"],
            "macro_recall": metrics["macro_recall"],
            "macro_f1": metrics["macro_f1"],
            "coverage": metrics["coverage"],
            "abstention_rate": metrics["abstention_rate"],
            "cross_split_near_duplicates": cross,
            "train_component_count": len(train_components),
            "validation_component_count": len(validation_components),
        }
        folds.append(fold_payload)
        for key in metric_keys:
            source_key = "accuracy" if key == "top1_accuracy" else key
            weighted_sums[key] += float(metrics.get(source_key) or 0.0) * len(validation_rows)
        weighted_rows += len(validation_rows)

    def _mean(key: str) -> float:
        values = [float(fold[key]) for fold in folds if fold[key] is not None]
        return round(sum(values) / len(values), 6) if values else 0.0

    def _std(key: str) -> float:
        values = [float(fold[key]) for fold in folds if fold[key] is not None]
        if len(values) <= 1:
            return 0.0
        mean = sum(values) / len(values)
        variance = sum((value - mean) ** 2 for value in values) / len(values)
        return round(variance ** 0.5, 6)

    aggregate = {
        key: {
            "mean": _mean(key),
            "std": _std(key),
            "weighted": round(weighted_sums[key] / weighted_rows, 6) if weighted_rows else 0.0,
        }
        for key in metric_keys
    }
    return {
        "strategy": "near_duplicate_same_label_component_grouped_cv",
        "n_folds": n_folds,
        "seed": seed,
        "jaccard_threshold": threshold,
        "fold_count": len(folds),
        "folds": folds,
        "aggregate": aggregate,
        "class_coverage_across_folds": {
            "present_class_count": len(all_present_classes),
            "total_class_count": len({row["disease"] for row in rows}),
            "present_classes": sorted(all_present_classes),
        },
        "cross_split_near_duplicates_max_pair_count": max_cross_split,
        "metric_scope": "每折仅对该折验证集中出现的类别计算 macro 指标；聚合同时报告 mean/std 与按验证行数加权结果。",
        "offline_prototype_only": True,
        "clinical_validation": False,
    }


def build_artifacts(
    dataset_path: Path = DEFAULT_DATASET,
    model_path: Path = DEFAULT_MODEL,
) -> tuple[dict[str, Any], dict[str, Any]]:
    rows = load_dataset(dataset_path)
    random_train, random_test = split_dataset(rows, TEST_SIZE, SEED)
    grouped_train, grouped_test, grouped_groups = grouped_fingerprint_split(rows, TEST_SIZE, SEED)

    same_label_components, same_label_stats = near_duplicate_components(rows, mode="same_label")
    global_components, global_stats = near_duplicate_components(rows, mode="global")
    near_train, near_test, near_indices = component_grouped_split(
        rows, same_label_components, TEST_SIZE, SEED
    )
    global_train, global_test, _ = component_grouped_split(rows, global_components, TEST_SIZE, SEED)
    grouped_cv = grouped_cross_validation(
        rows, same_label_components, n_folds=5, seed=SEED, threshold=0.8
    )

    random_model = fit(random_train, ALPHA, MIN_SYMPTOM_DF)
    grouped_model = fit(grouped_train, ALPHA, MIN_SYMPTOM_DF)
    near_model = fit(near_train, ALPHA, MIN_SYMPTOM_DF)
    global_model = fit(global_train, ALPHA, MIN_SYMPTOM_DF)
    model_payload = json.loads(model_path.read_text(encoding="utf-8"))
    model_hash = sha256_file(model_path)
    dataset_hash = sha256_file(dataset_path)

    random_metrics = evaluate_metrics(random_model, random_test)
    grouped_metrics = evaluate_metrics(grouped_model, grouped_test)
    near_metrics = evaluate_metrics(near_model, near_test)
    global_metrics = evaluate_metrics(global_model, global_test)
    random_metrics["cross_split_near_duplicates"] = cross_split_near_duplicate_count(random_train, random_test)
    grouped_metrics["cross_split_near_duplicates"] = cross_split_near_duplicate_count(grouped_train, grouped_test)
    near_metrics["cross_split_near_duplicates"] = cross_split_near_duplicate_count(near_train, near_test)
    global_metrics["cross_split_near_duplicates"] = cross_split_near_duplicate_count(global_train, global_test)

    manifest = {
        "schema_version": "model-split-manifest/v2",
        "dataset": {
            "path": str(dataset_path),
            "sha256": dataset_hash,
            "row_count": len(rows),
            "class_count": len({row["disease"] for row in rows}),
        },
        "model": {
            "path": str(model_path),
            "sha256": model_hash,
            "model_type": model_payload.get("model_type", "unknown"),
        },
        "configuration": {
            "seed": SEED,
            "test_size": TEST_SIZE,
            "alpha": ALPHA,
            "min_symptom_df": MIN_SYMPTOM_DF,
            "near_duplicate_threshold": 0.8,
        },
        "splits": {
            "random_baseline": {
                "strategy": "per_class_random",
                "train_rows": len(random_train),
                "test_rows": len(random_test),
            },
            "grouped_fingerprint": {
                "strategy": "exact_symptom_fingerprint_grouped",
                "train_rows": len(grouped_train),
                "test_rows": len(grouped_test),
                "train_group_count": len(grouped_groups["train"]),
                "test_group_count": len(grouped_groups["test"]),
                "train_group_fingerprints": grouped_groups["train"],
                "test_group_fingerprints": grouped_groups["test"],
            },
            "near_duplicate_same_label": {
                "strategy": "near_duplicate_same_label_component_grouped",
                "train_rows": len(near_train),
                "test_rows": len(near_test),
                "component_count": same_label_stats["component_count"],
                "train_sample_count": len(near_indices["train"]),
                "test_sample_count": len(near_indices["test"]),
                "component_stats": same_label_stats,
            },
            "near_duplicate_global": {
                "strategy": "near_duplicate_global_component_grouped",
                "train_rows": len(global_train),
                "test_rows": len(global_test),
                "component_count": global_stats["component_count"],
                "component_stats": global_stats,
            },
            "near_duplicate_grouped_cv": {
                "strategy": "near_duplicate_same_label_component_grouped_cv",
                "n_folds": grouped_cv["n_folds"],
                "seed": grouped_cv["seed"],
                "fold_count": grouped_cv["fold_count"],
                "cross_split_near_duplicates_max_pair_count": grouped_cv[
                    "cross_split_near_duplicates_max_pair_count"
                ],
            },
        },
    }

    report = {
        "schema_version": "model-evaluation/v2",
        "dataset": manifest["dataset"],
        "model": manifest["model"],
        "configuration": manifest["configuration"],
        "random_baseline": random_metrics,
        "grouped_fingerprint": grouped_metrics,
        "near_duplicate_same_label": near_metrics,
        "near_duplicate_global": global_metrics,
        "near_duplicate_grouped_cv": grouped_cv,
        "near_duplicate_components": {
            "same_label": same_label_stats,
            "global": global_stats,
        },
        "near_duplicate_audit": near_duplicate_audit(rows),
        "primary_split": "near_duplicate_same_label",
        "evaluation_disclaimer": "offline prototype evaluation / not clinical validation",
        "limitations": [
            "数据集只有 304 条记录，指标是离线原型评估，不代表临床表现。",
            "exact fingerprint 分组无法识别所有语义近重复；Near-duplicate Group Split 用于降低跨 split 近重复泄漏。",
            "same-label 分组避免跨疾病样本被机械合并成超大 component；global 分组仅作对照。",
            "更严格切分可能降低表面指标，但更贴近真实泛化风险。",
            "Grouped Near-Duplicate CV 要求同一 component 永不跨 train/validation；单 component 疾病会整折落在验证侧，部分折覆盖类别有限。",
        ],
    }
    return manifest, report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--write", action="store_true", help="write committed manifest and report artifacts")
    args = parser.parse_args()

    manifest, report = build_artifacts(args.dataset, args.model)
    if args.write:
        for path, payload in ((args.manifest, manifest), (args.report, report)):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "random_baseline": report["random_baseline"],
        "grouped_fingerprint": report["grouped_fingerprint"],
        "near_duplicate_same_label": report["near_duplicate_same_label"],
        "near_duplicate_global": report["near_duplicate_global"],
        "near_duplicate_grouped_cv": report["near_duplicate_grouped_cv"],
        "near_duplicate_components": report["near_duplicate_components"],
        "near_duplicate_audit": report["near_duplicate_audit"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
