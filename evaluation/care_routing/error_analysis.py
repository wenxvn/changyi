"""Systematic error analysis for the honest near-duplicate split.

Answers: why is near-dup Accuracy ~0.19? Does the failure come from component
structure, sample size, class definition, symptom coverage, or NB capacity?
"""

from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Mapping, Sequence

from data.symptom_disease_model.train import fit, load_dataset, predict

from evaluation.model.evaluate_grouped import (
    ALPHA,
    MIN_SYMPTOM_DF,
    near_duplicate_components,
)

from .disease_department import department_for
from .run_experiments import component_triple_split
from .uncertainty import distribution_entropy, predict_distribution, top1_confidence


def component_inventory(
    rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    components, stats = near_duplicate_components(list(rows), mode="same_label")
    by_disease: dict[str, list[list[int]]] = defaultdict(list)
    for component in components:
        by_disease[rows[component[0]]["disease"]].append(component)

    per_disease = {}
    for disease in sorted({row["disease"] for row in rows}):
        comps = by_disease.get(disease, [])
        sizes = [len(c) for c in comps]
        per_disease[disease] = {
            "department": department_for(disease),
            "row_count": sum(sizes),
            "component_count": len(comps),
            "component_sizes": sorted(sizes, reverse=True),
            "single_component_only": len(comps) <= 1,
        }
    return {
        "global_stats": stats,
        "per_disease": per_disease,
        "single_component_disease_count": sum(
            1 for item in per_disease.values() if item["single_component_only"]
        ),
        "multi_component_disease_count": sum(
            1 for item in per_disease.values() if not item["single_component_only"]
        ),
        "diseases_with_component_count": dict(
            Counter(item["component_count"] for item in per_disease.values())
        ),
    }


def split_inventory(
    train: Sequence[Mapping[str, Any]],
    cal: Sequence[Mapping[str, Any]],
    test: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    def disease_components(rows: Sequence[Mapping[str, Any]]) -> dict[str, int]:
        components, _ = near_duplicate_components(list(rows), mode="same_label")
        counter: Counter[str] = Counter()
        for component in components:
            counter[rows[component[0]]["disease"]] += 1
        return dict(counter)

    train_c = disease_components(train)
    cal_c = disease_components(cal)
    test_c = disease_components(test)
    diseases = sorted(set(train_c) | set(cal_c) | set(test_c))
    table = []
    for disease in diseases:
        table.append(
            {
                "disease": disease,
                "department": department_for(disease),
                "train_components": train_c.get(disease, 0),
                "cal_components": cal_c.get(disease, 0),
                "test_components": test_c.get(disease, 0),
                "test_is_unseen_component_family": test_c.get(disease, 0) > 0
                and train_c.get(disease, 0) > 0
                and not _shares_fingerprint(train, test, disease),
            }
        )
    return {
        "train_rows": len(train),
        "cal_rows": len(cal),
        "test_rows": len(test),
        "per_disease_components": table,
        "diseases_present_in_test": sum(1 for item in table if item["test_components"] > 0),
        "diseases_absent_from_train_for_test": sum(
            1
            for item in table
            if item["test_components"] > 0 and item["train_components"] == 0
        ),
    }


def _shares_fingerprint(
    train: Sequence[Mapping[str, Any]],
    test: Sequence[Mapping[str, Any]],
    disease: str,
) -> bool:
    train_sets = {frozenset(row["symptoms"]) for row in train if row["disease"] == disease}
    for row in test:
        if row["disease"] == disease and frozenset(row["symptoms"]) in train_sets:
            return True
    return False


def symptom_coverage(
    train: Sequence[Mapping[str, Any]],
    test: Sequence[Mapping[str, Any]],
    vocabulary: Sequence[str],
) -> dict[str, Any]:
    vocab = set(vocabulary)
    train_symptoms = {s for row in train for s in row["symptoms"] if s in vocab}
    test_rows = list(test)
    unseen_symptom_rows = 0
    unseen_symptom_tokens = 0
    total_tokens = 0
    unseen_combo_rows = 0
    train_combos = {frozenset(row["symptoms"]) for row in train}
    for row in test_rows:
        symptoms = [s for s in row["symptoms"]]
        total_tokens += len(symptoms)
        missing = [s for s in symptoms if s not in train_symptoms]
        if missing:
            unseen_symptom_rows += 1
            unseen_symptom_tokens += len(missing)
        if frozenset(symptoms) not in train_combos:
            unseen_combo_rows += 1
    return {
        "train_vocabulary_used": len(train_symptoms),
        "test_rows": len(test_rows),
        "test_rows_with_unseen_symptom": unseen_symptom_rows,
        "unseen_symptom_token_ratio": round(unseen_symptom_tokens / total_tokens, 6)
        if total_tokens
        else 0.0,
        "test_rows_with_unseen_combination": unseen_combo_rows,
        "unseen_combination_ratio": round(unseen_combo_rows / len(test_rows), 6)
        if test_rows
        else 0.0,
    }


def evaluate_error_profile(
    model: Mapping[str, Any],
    test: Sequence[Mapping[str, Any]],
    temperature: float = 1.0,
    top_k_list: Sequence[int] = (1, 2, 3),
) -> dict[str, Any]:
    y_true: list[str] = []
    y_pred: list[str | None] = []
    dept_true: list[str] = []
    dept_pred: list[str | None] = []
    confidences: list[float] = []
    entropies: list[float] = []
    set_sizes: list[int] = []
    topk_hits = {k: 0 for k in top_k_list}
    per_class_stats: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "n": 0,
            "correct": 0,
            "confidences": [],
            "entropies": [],
            "set_sizes": [],
            "predicted": Counter(),
        }
    )
    component_size_errors: dict[int, list[bool]] = defaultdict(list)

    # Map each test row to its component size within the full dataset via fingerprint.
    for row in test:
        ranked = predict_distribution(model, row["symptoms"], temperature=temperature)
        labels = [label for label, _ in ranked]
        predicted = labels[0] if labels else None
        correct = predicted == row["disease"]
        y_true.append(row["disease"])
        y_pred.append(predicted)
        dept_true.append(department_for(row["disease"]))
        dept_pred.append(department_for(predicted) if predicted else None)
        confidence = top1_confidence(ranked)
        entropy = distribution_entropy(ranked)
        confidences.append(confidence)
        entropies.append(entropy)
        set_sizes.append(min(3, len(labels)))
        for k in top_k_list:
            if row["disease"] in labels[:k]:
                topk_hits[k] += 1
        stats = per_class_stats[row["disease"]]
        stats["n"] += 1
        stats["correct"] += int(correct)
        stats["confidences"].append(confidence)
        stats["entropies"].append(entropy)
        stats["set_sizes"].append(min(3, len(labels)))
        if predicted:
            stats["predicted"][predicted] += 1

    confusion = defaultdict(Counter)
    for true, pred in zip(y_true, y_pred):
        confusion[true][pred or "ABSTAIN"] += 1

    dept_confusion = defaultdict(Counter)
    for true, pred in zip(dept_true, dept_pred):
        dept_confusion[true][pred or "ABSTAIN"] += 1

    error_contributors = []
    class_rows = []
    for disease, stats in sorted(per_class_stats.items()):
        acc = stats["correct"] / stats["n"] if stats["n"] else 0.0
        mean_conf = sum(stats["confidences"]) / stats["n"] if stats["n"] else 0.0
        mean_h = sum(stats["entropies"]) / stats["n"] if stats["n"] else 0.0
        mean_set = sum(stats["set_sizes"]) / stats["n"] if stats["n"] else 0.0
        error_n = stats["n"] - stats["correct"]
        class_rows.append(
            {
                "disease": disease,
                "department": department_for(disease),
                "n": stats["n"],
                "accuracy": round(acc, 6),
                "error_count": error_n,
                "mean_confidence": round(mean_conf, 6),
                "mean_entropy": round(mean_h, 6),
                "mean_top3_set_size": round(mean_set, 6),
                "top_predictions": dict(stats["predicted"].most_common(5)),
            }
        )
        if error_n:
            error_contributors.append(
                {
                    "disease": disease,
                    "error_count": error_n,
                    "error_share": round(error_n / max(sum(1 for t, p in zip(y_true, y_pred) if t != p), 1), 6),
                }
            )
    error_contributors.sort(key=lambda item: item["error_count"], reverse=True)

    def _macro_f1(y_t: Sequence[str], y_p: Sequence[str | None]) -> float:
        labels = sorted(set(y_t) | {x for x in y_p if x})
        f1s = []
        for label in labels:
            tp = sum(1 for t, p in zip(y_t, y_p) if t == label and p == label)
            fp = sum(1 for t, p in zip(y_t, y_p) if t != label and p == label)
            fn = sum(1 for t, p in zip(y_t, y_p) if t == label and p != label)
            precision = tp / (tp + fp) if tp + fp else 0.0
            recall = tp / (tp + fn) if tp + fn else 0.0
            f1s.append(2 * precision * recall / (precision + recall) if precision + recall else 0.0)
        return round(sum(f1s) / len(f1s), 6) if f1s else 0.0

    n = len(y_true)
    correct_n = sum(1 for t, p in zip(y_true, y_pred) if t == p)
    dept_correct = sum(1 for t, p in zip(dept_true, dept_pred) if t == p)
    wrong_but_confident = sum(
        1 for t, p, c in zip(y_true, y_pred, confidences) if t != p and c >= 0.7
    )

    return {
        "test_rows": n,
        "accuracy": round(correct_n / n, 6) if n else 0.0,
        "department_accuracy": round(dept_correct / n, 6) if n else 0.0,
        "macro_f1": _macro_f1(y_true, y_pred),
        "department_macro_f1": _macro_f1(dept_true, dept_pred),
        "topk_accuracy": {
            str(k): round(topk_hits[k] / n, 6) if n else 0.0 for k in top_k_list
        },
        "mean_confidence": round(sum(confidences) / n, 6) if n else 0.0,
        "mean_entropy": round(sum(entropies) / n, 6) if n else 0.0,
        "mean_top3_set_size": round(sum(set_sizes) / n, 6) if n else 0.0,
        "wrong_but_confident_rate": round(wrong_but_confident / n, 6) if n else 0.0,
        "confusion_matrix": {
            disease: dict(counts) for disease, counts in sorted(confusion.items())
        },
        "department_confusion_matrix": {
            dept: dict(counts) for dept, counts in sorted(dept_confusion.items())
        },
        "per_class": class_rows,
        "top_error_contributors": error_contributors[:15],
    }


def component_size_vs_error(
    rows: Sequence[Mapping[str, Any]],
    model: Mapping[str, Any],
    test: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    components, _ = near_duplicate_components(list(rows), mode="same_label")
    size_of_row: dict[int, int] = {}
    for component in components:
        for index in component:
            size_of_row[index] = len(component)
    # Map test rows back by fingerprint within disease.
    buckets: dict[str, list[bool]] = defaultdict(list)
    fingerprint_size = {}
    for component in components:
        fp = frozenset(rows[component[0]]["symptoms"])
        fingerprint_size[fp] = len(component)
    for row in test:
        ranked = predict_distribution(model, row["symptoms"])
        correct = bool(ranked) and ranked[0][0] == row["disease"]
        size = fingerprint_size.get(frozenset(row["symptoms"]), 0)
        key = str(size) if size else "unknown"
        buckets[key].append(correct)
    table = []
    for key in sorted(buckets, key=lambda item: (item == "unknown", int(item) if item.isdigit() else 0)):
        flags = buckets[key]
        table.append(
            {
                "component_size": key,
                "n": len(flags),
                "accuracy": round(sum(flags) / len(flags), 6) if flags else 0.0,
            }
        )
    return {"by_component_size": table}


def run_error_analysis(
    *,
    dataset_path: str = "data/symptom_disease_model/data/disease_symptom_structured_41diseases_long.csv",
    seed: int = 42,
) -> dict[str, Any]:
    rows = load_dataset(dataset_path)
    inventory = component_inventory(rows)
    train, cal, test = component_triple_split(rows, seed=seed)
    split_inv = split_inventory(train, cal, test)
    model = fit(train, ALPHA, MIN_SYMPTOM_DF)
    coverage = symptom_coverage(train, test, model.get("vocabulary") or [])
    profile = evaluate_error_profile(model, test)
    size_err = component_size_vs_error(rows, model, test)

    root_cause = {
        "headline": (
            "0.188 是「表达簇外推 + 样本规模」与「NB 模型假设/容量」叠加的结果："
            "同一诚实切分下 LR/SVM 可到 1.0，说明 NB 不是无辜的；但 33/41 疾病仅单 component、"
            "test 100% unseen combination，数据结构仍是产品化主动追问的硬瓶颈。"
        ),
        "evidence": [
            f"{inventory['single_component_disease_count']}/41 疾病只有 1 个近重复 component，无法诚实拆分。",
            f"诚实 test 仅 {profile['test_rows']} 行，覆盖 {split_inv['diseases_present_in_test']} 个病种。",
            f"test 中 unseen combination ratio = {coverage['unseen_combination_ratio']}，unseen symptom token ratio = {coverage['unseen_symptom_token_ratio']}。",
            f"Top-1={profile['accuracy']} 但 Top-3={profile['topk_accuracy'].get('3')}，说明标签空间仍部分可达但排序错误。",
            f"mean confidence={profile['mean_confidence']} vs accuracy={profile['accuracy']}，高置信错误存在。",
            "model_baselines：同一 near-dup split 上 LR/LinearSVM accuracy=1.0 vs NB=0.1875，NB 容量是重要共因。",
        ],
        "not_the_main_story": [
            "不是单纯“304 条太少”——random split 在同样 304 条上能到 0.97。",
            "不是可以通过放宽切分“修好”的指标问题——改切分会重新引入泄漏。",
            "也不能只怪数据：线性模型在相同 test 上可达 1.0，NB 的独立性假设/平滑在稀疏组合上明显吃亏。",
        ],
    }

    return {
        "schema_version": "care-routing-error-analysis/v1",
        "protocol": "near_duplicate_same_label triple split (honest)",
        "seed": seed,
        "component_inventory": inventory,
        "split_inventory": split_inv,
        "symptom_coverage": coverage,
        "error_profile": profile,
        "component_size_vs_error": size_err,
        "root_cause": root_cause,
        "disclaimer": "离线原型误差分析；非临床验证。",
    }


def write_error_analysis_report(payload: Mapping[str, Any], markdown_path: Path) -> None:
    inventory = payload["component_inventory"]
    split_inv = payload["split_inventory"]
    coverage = payload["symptom_coverage"]
    profile = payload["error_profile"]
    root = payload["root_cause"]

    lines = [
        "# Round2 误差分析：near-dup Accuracy≈0.188 根因",
        "",
        f"协议：{payload['protocol']}；seed={payload['seed']}",
        "",
        "## 一句话结论",
        "",
        root["headline"],
        "",
        "## Component 结构",
        "",
        f"- 单 component 疾病：**{inventory['single_component_disease_count']}/41**",
        f"- 多 component 疾病：**{inventory['multi_component_disease_count']}/41**",
        f"- component 数分布：`{inventory['diseases_with_component_count']}`",
        f"- 诚实切分规模：train={split_inv['train_rows']} / cal={split_inv['cal_rows']} / test={split_inv['test_rows']}",
        f"- test 覆盖病种数：{split_inv['diseases_present_in_test']}",
        "",
        "## 指标",
        "",
        f"- Top-1 Accuracy: **{profile['accuracy']}**",
        f"- Top-2 / Top-3: {profile['topk_accuracy'].get('2')} / {profile['topk_accuracy'].get('3')}",
        f"- Department Accuracy: {profile['department_accuracy']}",
        f"- Macro-F1: {profile['macro_f1']}",
        f"- Mean confidence / entropy / top3 set: {profile['mean_confidence']} / {profile['mean_entropy']} / {profile['mean_top3_set_size']}",
        f"- Wrong-but-confident (conf≥0.7): {profile['wrong_but_confident_rate']}",
        f"- Unseen combination ratio: {coverage['unseen_combination_ratio']}",
        f"- Unseen symptom token ratio: {coverage['unseen_symptom_token_ratio']}",
        "",
        "## 主要错误贡献类别",
        "",
    ]
    for item in profile["top_error_contributors"][:10]:
        lines.append(f"- {item['disease']}: {item['error_count']} errors")
    lines.extend(["", "## 证据", ""])
    for evidence in root["evidence"]:
        lines.append(f"- {evidence}")
    lines.extend(["", "## 不是主因", ""])
    for item in root["not_the_main_story"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "> 完整 confusion / per-class / component-size 表见 `results/round2_error_analysis.json`。",
            "",
        ]
    )
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text("\n".join(lines), encoding="utf-8")
