"""Run P0 uncertainty + adaptive-inquiry experiments offline.

Usage:
    .venv/bin/python -m evaluation.care_routing.run_experiments
    .venv/bin/python -m evaluation.care_routing.run_experiments --write

Artifacts land in evaluation/care_routing/results/.
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from typing import Any

from data.symptom_disease_model.labels import load_disease_name_map
from data.symptom_disease_model.train import fit, load_dataset, split_dataset

from evaluation.model.evaluate_grouped import (
    ALPHA,
    MIN_SYMPTOM_DF,
    SEED,
    TEST_SIZE,
    grouped_fingerprint_split,
    near_duplicate_components,
    sha256_file,
)

from .disease_department import DISEASE_TO_DEPARTMENT, department_for
from .inquiry import class_conditional_symptom_probs, run_adaptive_inquiry
from .metrics import evaluate_uncertainty_split, summarize_inquiry_runs
from .uncertainty import (
    build_uncertainty_payload,
    conformal_threshold,
    fit_temperature,
    predict_distribution,
)

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATASET = ROOT / "data/symptom_disease_model/data/disease_symptom_structured_41diseases_long.csv"
DEFAULT_MODEL = ROOT / "data/symptom_disease_model/models/symptom_disease_41_nb.json"
RESULTS_DIR = Path(__file__).with_name("results")
REPORT_PATH = RESULTS_DIR / "care_routing_experiment_report.json"
EXAMPLES_PATH = RESULTS_DIR / "uncertainty_examples.json"
INQUIRY_TRACE_PATH = RESULTS_DIR / "inquiry_traces.json"


def _split_calibration(rows: list[dict[str, Any]], fraction: float = 0.5, seed: int = SEED):
    rng = random.Random(seed)
    shuffled = rows[:]
    rng.shuffle(shuffled)
    cut = max(1, int(len(shuffled) * fraction))
    if cut >= len(shuffled):
        cut = len(shuffled) - 1
    return shuffled[:cut], shuffled[cut:]


def load_maps():
    disease_name_map = load_disease_name_map()
    return disease_name_map


def build_splits(rows: list[dict[str, Any]]) -> dict[str, tuple[list, list]]:
    random_train, random_test = split_dataset(rows, TEST_SIZE, SEED)
    grouped_train, grouped_test, _ = grouped_fingerprint_split(rows, TEST_SIZE, SEED)
    near_train, _, near_test = component_triple_split(rows, seed=SEED)
    return {
        "random_baseline": (random_train, random_test),
        "grouped_fingerprint": (grouped_train, grouped_test),
        "near_duplicate_same_label": (near_train, near_test),
    }


def component_triple_split(
    rows: list[dict[str, Any]],
    *,
    seed: int = SEED,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Three-way same-label near-duplicate split so calibration matches test shift."""

    components, _ = near_duplicate_components(rows, mode="same_label")
    rng = random.Random(seed)
    by_disease: dict[str, list[list[int]]] = {}
    for component in components:
        disease = rows[component[0]]["disease"]
        by_disease.setdefault(disease, []).append(component)

    train_idx: list[int] = []
    cal_idx: list[int] = []
    test_idx: list[int] = []
    for disease in sorted(by_disease):
        comps = by_disease[disease][:]
        rng.shuffle(comps)
        if len(comps) == 1:
            # Single near-duplicate component cannot be honestly split.
            train_idx.extend(comps[0])
            continue
        if len(comps) == 2:
            train_idx.extend(comps[0])
            cal_idx.extend(comps[1])
            continue
        if len(comps) == 3:
            train_idx.extend(comps[0])
            cal_idx.extend(comps[1])
            test_idx.extend(comps[2])
            continue
        # 4+ components: keep at least 2 for train, 1 cal, remainder test.
        train_idx.extend([i for comp in comps[:2] for i in comp])
        cal_idx.extend(comps[2])
        test_idx.extend([i for comp in comps[3:] for i in comp])

    train = [rows[i] for i in train_idx]
    cal = [rows[i] for i in cal_idx]
    test = [rows[i] for i in test_idx]
    if not test:
        # Fallback: peel the smallest component groups into test.
        leftovers = [rows[i] for i in train_idx[-8:]]
        train = train[:-8]
        test = leftovers
    return train, cal, test


def evaluate_uncertainty_for_split(
    train: list[dict[str, Any]],
    test: list[dict[str, Any]],
    *,
    alpha: float = 0.1,
    cal_rows: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    model = fit(train, ALPHA, MIN_SYMPTOM_DF)
    # Fit temperature and conformal threshold on calibration rows that never
    # enter the test split. Prefer a dedicated calibration set when provided
    # (near-duplicate three-way); otherwise hold out half of train.
    if cal_rows is None:
        cal_fit, cal_threshold = _split_calibration(train, fraction=0.5, seed=SEED)
    else:
        cal_fit = cal_rows
        cal_threshold = cal_rows
    temperature_fit = fit_temperature(model, cal_fit)
    temperature = float(temperature_fit["temperature"])
    conformal = conformal_threshold(model, cal_threshold, alpha=alpha, temperature=temperature)

    raw = evaluate_uncertainty_split(model, test, temperature=1.0)
    calibrated = evaluate_uncertainty_split(
        model, test, temperature=temperature, conformal=conformal
    )
    # Also report uncalibrated conformal for comparison.
    conformal_uncal = conformal_threshold(model, cal_threshold, alpha=alpha, temperature=1.0)
    uncalibrated_conformal = evaluate_uncertainty_split(
        model, test, temperature=1.0, conformal=conformal_uncal
    )
    return {
        "train_rows": len(train),
        "cal_rows": len(cal_fit),
        "test_rows": len(test),
        "temperature_scaling": temperature_fit,
        "conformal": conformal,
        "conformal_uncalibrated_temperature": conformal_uncal,
        "raw_uncalibrated": raw,
        "temperature_only": evaluate_uncertainty_split(model, test, temperature=temperature),
        "temperature_plus_conformal": calibrated,
        "conformal_only": uncalibrated_conformal,
        "comparison_headline": {
            "raw_accuracy": raw["accuracy"],
            "raw_ece": raw["ece"],
            "raw_department_accuracy": raw["department_accuracy"],
            "calibrated_ece": calibrated["ece"],
            "calibrated_coverage": calibrated["coverage"],
            "calibrated_mean_set_size": calibrated["mean_prediction_set_size"],
            "calibrated_should_clarify_rate": calibrated["should_clarify_rate"],
            "calibrated_accuracy_when_not_clarified": calibrated["accuracy_when_not_clarified"],
            "calibrated_accuracy_when_clarified": calibrated["accuracy_when_clarified"],
        },
    }


def evaluate_inquiry_for_split(
    train: list[dict[str, Any]],
    test: list[dict[str, Any]],
    *,
    strategies: tuple[str, ...] = ("information_gain", "random", "most_frequent"),
    max_questions: int = 5,
    initial_symptom_count: int = 1,
    seed: int = SEED,
    cal_rows: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    model = fit(train, ALPHA, MIN_SYMPTOM_DF)
    symptom_probs = class_conditional_symptom_probs(model)
    cal_fit = cal_rows if cal_rows is not None else _split_calibration(train, fraction=0.5, seed=SEED)[0]
    temperature = float(fit_temperature(model, cal_fit)["temperature"])

    modes = {
        "adaptive_stop": False,
        "forced_max_questions": True,
    }
    summaries: dict[str, Any] = {}
    traces: dict[str, Any] = {}
    for mode_name, force in modes.items():
        mode_summary = {}
        mode_traces = {}
        for strategy in strategies:
            runs = [
                run_adaptive_inquiry(
                    model,
                    row,
                    strategy=strategy,
                    initial_symptom_count=initial_symptom_count,
                    max_questions=max_questions,
                    temperature=temperature,
                    seed=seed,
                    symptom_probs=symptom_probs,
                    force_questions=force,
                )
                for row in test
            ]
            mode_summary[strategy] = summarize_inquiry_runs(runs)
            mode_traces[strategy] = [
                {
                    "true_disease": run.get("true_disease"),
                    "initial_symptoms": run.get("initial_symptoms"),
                    "questions_asked": run.get("questions_asked"),
                    "questions": run.get("questions"),
                    "initial": run.get("initial"),
                    "final": run.get("final"),
                    "stop_reason": run.get("stop_reason"),
                }
                for run in runs
                if not run.get("skipped")
            ][:12]
        summaries[mode_name] = mode_summary
        traces[mode_name] = mode_traces
    return {
        "train_rows": len(train),
        "test_rows": len(test),
        "temperature": temperature,
        "max_questions": max_questions,
        "initial_symptom_count": initial_symptom_count,
        "modes": summaries,
        "sample_traces": traces,
    }


def build_examples(model, disease_name_map, rows, limit: int = 8) -> list[dict[str, Any]]:
    examples = []
    for row in rows[:limit]:
        ranked = predict_distribution(model, row["symptoms"], temperature=1.0)
        conformal = {"threshold": 0.55}
        payload = build_uncertainty_payload(
            ranked,
            disease_name_map=disease_name_map,
            department_for=department_for,
            conformal=conformal,
        )
        payload["true_disease"] = row["disease"]
        payload["true_department"] = department_for(row["disease"])
        payload["true_symptoms"] = row["symptoms"]
        examples.append(payload)
    return examples


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--write", action="store_true", help="write report artifacts")
    parser.add_argument("--conformal-alpha", type=float, default=0.1)
    parser.add_argument("--max-questions", type=int, default=5)
    parser.add_argument("--initial-symptoms", type=int, default=1)
    args = parser.parse_args()

    rows = load_dataset(args.dataset)
    disease_name_map = load_maps()
    splits = build_splits(rows)
    near_train, near_cal, near_test = component_triple_split(rows)
    splits["near_duplicate_same_label"] = (near_train, near_test)
    cal_map = {
        "random_baseline": None,
        "grouped_fingerprint": None,
        "near_duplicate_same_label": near_cal,
    }

    uncertainty_results = {}
    inquiry_results = {}
    for name, (train, test) in splits.items():
        uncertainty_results[name] = evaluate_uncertainty_for_split(
            train,
            test,
            alpha=args.conformal_alpha,
            cal_rows=cal_map.get(name),
        )
        inquiry_results[name] = evaluate_inquiry_for_split(
            train,
            test,
            max_questions=args.max_questions,
            initial_symptom_count=args.initial_symptoms,
            cal_rows=cal_map.get(name),
        )

    # Runtime model examples (committed 41-NB artifact, not retrained).
    runtime_model = json.loads(args.model.read_text(encoding="utf-8"))
    random_train, random_test = splits["random_baseline"]
    examples = build_examples(runtime_model, disease_name_map, random_test, limit=8)

    report = {
        "schema_version": "care-routing-experiment/v1",
        "disclaimer": "离线原型实验；概率未做临床校准；不修改 Safety Gate / 红旗规则 / 正式 API。",
        "dataset": {
            "path": str(args.dataset.relative_to(ROOT)),
            "sha256": sha256_file(args.dataset),
            "rows": len(rows),
            "classes": len({row["disease"] for row in rows}),
        },
        "production_model_artifact": {
            "path": str(args.model.relative_to(ROOT)),
            "sha256": sha256_file(args.model),
            "model_type": runtime_model.get("model_type"),
        },
        "configuration": {
            "seed": SEED,
            "test_size": TEST_SIZE,
            "alpha": ALPHA,
            "min_symptom_df": MIN_SYMPTOM_DF,
            "conformal_alpha": args.conformal_alpha,
            "max_questions": args.max_questions,
            "initial_symptoms": args.initial_symptoms,
            "department_map_size": len(DISEASE_TO_DEPARTMENT),
            "split_strategy": "random / fingerprint / near-duplicate three-way component split",
        },
        "uncertainty": uncertainty_results,
        "adaptive_inquiry": inquiry_results,
        "feasibility": {
            "p0_1_uncertainty_aware_triage": "可行",
            "p0_2_information_gain_inquiry": "部分可行（袋状症状模型只能可靠模拟阳性回答；阴性回答缺少显式负特征）",
            "p1_1_hybrid_safety_gate": "部分可行（可叠加不确定性信号，但红旗规则必须保持最高优先级且本轮不改 baseline）",
            "p1_2_multi_objective_routing": "部分可行（已有加权打分；缺号源/等待时间等可核验字段，不能上学习排序）",
            "p2_care_path_kg": "部分可行（症状-疾病-科室边可用；医院-医生边仅目录字段，不适合 GNN）",
        },
        "limitations": [
            "近重复同标签切分下模型泛化很弱，表面 Accuracy 高的随机切分存在泄漏，不能当作临床能力。",
            "温度校准与 conformal 依赖独立 calibration 切片；样本量小，阈值方差大，分布漂移时 coverage 会塌缩。",
            "信息增益追问使用 held-out 标注症状集作 oracle，不是真实患者对话；阴性回答不会写入模型特征。",
            "科室映射是评估用元数据，不等于正式 product routing 的完整规则。",
        ],
    }

    if args.write:
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        REPORT_PATH.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        EXAMPLES_PATH.write_text(
            json.dumps(examples, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        inquiry_trace = {
            name: payload.get("sample_traces")
            for name, payload in inquiry_results.items()
        }
        INQUIRY_TRACE_PATH.write_text(
            json.dumps(inquiry_trace, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    # Compact stdout summary for the operator.
    summary = {
        "uncertainty_headline": {
            split: {
                "raw_accuracy": payload["raw_uncalibrated"]["accuracy"],
                "raw_ece": payload["raw_uncalibrated"]["ece"],
                "raw_dept_acc": payload["raw_uncalibrated"]["department_accuracy"],
                "cal_ece": payload["temperature_plus_conformal"]["ece"],
                "clarify_rate": payload["temperature_plus_conformal"]["should_clarify_rate"],
                "acc_not_clarify": payload["temperature_plus_conformal"]["accuracy_when_not_clarified"],
                "acc_clarify": payload["temperature_plus_conformal"]["accuracy_when_clarified"],
                "mean_set_size": payload["temperature_plus_conformal"]["mean_prediction_set_size"],
                "T": payload["temperature_scaling"]["temperature"],
            }
            for split, payload in uncertainty_results.items()
        },
        "inquiry_headline": {
            split: {
                mode: {
                    strategy: {
                        "initial_acc": summary_payload["initial_accuracy"],
                        "final_acc": summary_payload["final_accuracy"],
                        "delta": summary_payload["accuracy_delta"],
                        "avg_q": summary_payload["average_questions"],
                        "entropy_drop": summary_payload["mean_entropy_reduction"],
                    }
                    for strategy, summary_payload in mode_payload.items()
                }
                for mode, mode_payload in payload["modes"].items()
            }
            for split, payload in inquiry_results.items()
        },
        "wrote": str(REPORT_PATH) if args.write else None,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
