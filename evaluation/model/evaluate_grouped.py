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
    labels = sorted(model.get("classes") or {row["disease"] for row in rows})
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

    per_class_recall = {}
    per_class_precision = {}
    per_class_f1 = {}
    for label in labels:
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
    macro_precision = sum(per_class_precision.values()) / len(labels) if labels else 0.0
    macro_recall = sum(per_class_recall.values()) / len(labels) if labels else 0.0
    macro_f1 = sum(per_class_f1.values()) / len(labels) if labels else 0.0
    return {
        "test_rows": row_count,
        "accuracy": round(correct / row_count, 6) if row_count else None,
        "covered_accuracy": round(covered_correct / covered, 6) if covered else None,
        "top3_accuracy": round(top3_correct / row_count, 6) if row_count else None,
        "macro_precision": round(macro_precision, 6),
        "macro_recall": round(macro_recall, 6),
        "macro_f1": round(macro_f1, 6),
        "per_class_recall": per_class_recall,
        "confusion_matrix": {label: dict(sorted(counts.items())) for label, counts in confusion.items()},
        "coverage": round(covered / row_count, 6) if row_count else 0.0,
        "abstention_rate": round((row_count - covered) / row_count, 6) if row_count else 0.0,
        "abstention_policy": {
            "confidence_threshold": ABSTAIN_THRESHOLD,
            "description": "top-1 probability below threshold is withheld from the assistive disease display",
        },
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


def build_artifacts(
    dataset_path: Path = DEFAULT_DATASET,
    model_path: Path = DEFAULT_MODEL,
) -> tuple[dict[str, Any], dict[str, Any]]:
    rows = load_dataset(dataset_path)
    random_train, random_test = split_dataset(rows, TEST_SIZE, SEED)
    grouped_train, grouped_test, grouped_groups = grouped_fingerprint_split(rows, TEST_SIZE, SEED)

    random_model = fit(random_train, ALPHA, MIN_SYMPTOM_DF)
    grouped_model = fit(grouped_train, ALPHA, MIN_SYMPTOM_DF)
    model_payload = json.loads(model_path.read_text(encoding="utf-8"))
    model_hash = sha256_file(model_path)
    dataset_hash = sha256_file(dataset_path)

    manifest = {
        "schema_version": "model-split-manifest/v1",
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
        },
    }

    report = {
        "schema_version": "model-evaluation/v1",
        "dataset": manifest["dataset"],
        "model": manifest["model"],
        "configuration": manifest["configuration"],
        "random_baseline": evaluate_metrics(random_model, random_test),
        "grouped_fingerprint": evaluate_metrics(grouped_model, grouped_test),
        "near_duplicate_audit": near_duplicate_audit(rows),
        "limitations": [
            "数据集只有 304 条记录，指标是离线原型评估，不代表临床表现。",
            "exact fingerprint 分组无法识别所有语义近重复；近重复审计仅作为风险提示。",
            "grouped split 与当前数据的随机 split 行数相同并不意味着不存在近重复风险。",
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
        "near_duplicate_audit": report["near_duplicate_audit"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
