"""Round3 orchestrator: expanded honest eval + linear model validation."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

from .hierarchical_triage import run_hierarchical_comparison
from .learning_curve import learning_curve
from .robustness import run_robustness
from .round3_models import run_model_matrix, SEEDS
from .round3_split_audit import (
    load_expanded,
    load_structured,
    evaluate_component_definition_limits,
    quota_split,
    write_external_eval_schema,
    cross_split_leakage_audit,
)
from .data_schema import write_schema_assets

ROOT = Path(__file__).resolve().parents[2]
RESULTS = Path(__file__).with_name("results")


def readiness_decision(payload: dict[str, Any]) -> dict[str, Any]:
    matrix = payload["model_matrix"]
    headline = matrix["headline"]
    nb_acc = headline["multinomial_nb"]["accuracy"]["mean"]
    lr_acc = headline["logistic_regression"]["accuracy"]["mean"]
    svm_acc = headline["linear_svm"]["accuracy"]["mean"]
    nb_dept = headline["multinomial_nb"]["department_accuracy"]["mean"]
    lr_dept = headline["logistic_regression"]["department_accuracy"]["mean"]
    test_rows = None
    if matrix["runs"]:
        test_rows = matrix["runs"][0]["split_meta"]["test_rows"]
    test_diseases = None
    if matrix["runs"]:
        test_diseases = matrix["runs"][0]["split_meta"]["test_diseases"]

    lr_better = lr_acc is not None and nb_acc is not None and (lr_acc - nb_acc) >= 0.10
    svm_better = svm_acc is not None and nb_acc is not None and (svm_acc - nb_acc) >= 0.10
    multi_seed_stable = matrix["run_count"] >= 3 and (
        (headline["logistic_regression"]["accuracy"]["std"] or 0) <= 0.15
    )
    dept_ok = lr_dept is not None and lr_dept >= 0.5
    ece_ok = (
        headline["logistic_regression_temperature"]["ece"]["mean"] is not None
        and headline["logistic_regression_temperature"]["ece"]["mean"] <= 0.15
    )
    honest_scale_ok = (test_rows or 0) >= 50 and (test_diseases or 0) >= 10

    conditions = {
        "larger_honest_eval": honest_scale_ok,
        "lr_or_svm_stably_better_than_nb": bool(lr_better or svm_better) and multi_seed_stable,
        "department_metrics_reliable": bool(dept_ok),
        "calibration_acceptable": bool(ece_ok),
        "safety_regression_unaffected": True,  # production Safety path untouched
    }
    if all(conditions.values()):
        decision = "CANDIDATE_FOR_SHADOW_MODE"
    elif conditions["larger_honest_eval"] and conditions["lr_or_svm_stably_better_than_nb"]:
        decision = "CANDIDATE_FOR_SHADOW_MODE" if dept_ok else "RESEARCH_ONLY"
    else:
        decision = "RESEARCH_ONLY"

    # Extra guard: if expanded test still small, never claim shadow candidate.
    if (test_rows or 0) < 80 or (test_diseases or 0) < 12:
        decision = "RESEARCH_ONLY"

    return {
        "decision": decision,
        "conditions": conditions,
        "evidence": [
            f"expanded honest test_rows≈{test_rows}, test_diseases≈{test_diseases}",
            f"NB acc={nb_acc}, LR acc={lr_acc}, SVM acc={svm_acc}",
            f"NB dept={nb_dept}, LR dept={lr_dept}",
            f"LR ECE(calibrated)={headline['logistic_regression_temperature']['ece']['mean']}",
            f"multi-seed runs={matrix['run_count']}",
            "Safety Gate / production API untouched this round",
        ],
        "note": "即使 CANDIDATE_FOR_SHADOW_MODE，也不得未经下一轮验收直接替换正式模型。",
    }


def seven_answers(payload: dict[str, Any]) -> dict[str, Any]:
    matrix = payload["model_matrix"]
    h = matrix["headline"]
    curve = payload["learning_curve"]
    robust = payload["robustness"]
    hier = payload["hierarchical"]
    split = payload["split_audit"]["expanded"]
    readiness = payload["readiness"]

    nb = h["multinomial_nb"]["accuracy"]
    lr = h["logistic_regression"]["accuracy"]
    svm = h["linear_svm"]["accuracy"]

    # Occurrence vs real: if test grew a lot and LR still >> NB across seeds, not n=16 fluke.
    test_rows = matrix["runs"][0]["split_meta"]["test_rows"] if matrix["runs"] else 0
    not_fluke = test_rows >= 80 and (lr["mean"] or 0) - (nb["mean"] or 0) >= 0.05

    gain = curve["accuracy_gain_20_to_100"]
    data_helps = any(
        gain.get(key) is not None and gain[key] >= 0.05 for key in ("nb", "lr", "svm")
    )

    worst = robust.get("worst_case") or {}
    most_robust = min(
        ("nb", "lr", "svm"),
        key=lambda name: (worst.get(name) or {}).get("mean_drop") if (worst.get(name) or {}).get("mean_drop") is not None else 999,
    )

    direct = hier["direct_department_accuracy"]["mean"]
    disease_dept = hier["disease_first_department_accuracy"]["mean"]
    if direct is not None and disease_dept is not None:
        hier_choice = "direct_department" if direct >= disease_dept else "disease_first"
    else:
        hier_choice = "inconclusive"

    # Error severity from first LR run
    routing = None
    if matrix["runs"]:
        routing = matrix["runs"][0]["models"]["logistic_regression"]["routing_error"]
    if routing:
        same = routing["same_department_error"]
        cross = routing["cross_department_error"]
        severity_main = "same_department" if same >= cross else "cross_department"
    else:
        severity_main = "unknown"

    return {
        "1_lr_svm_still_better_on_expanded_honest_eval": {
            "nb": nb,
            "lr": lr,
            "svm": svm,
            "answer": "yes" if (lr["mean"] or 0) > (nb["mean"] or 0) else "no",
        },
        "2_is_1.0_only_n16_fluke": {
            "answer": "not_just_n16" if not_fluke else "still_uncertain",
            "expanded_test_rows": test_rows,
            "reason": (
                "扩大诚实 test 后优势仍在多 seed 上出现" if not_fluke
                else "扩大后优势不稳定或 test 仍偏小，不能排除偶然"
            ),
        },
        "3_learning_curve_more_data_helps": {
            "answer": "yes" if data_helps else "plateau_or_unclear",
            "gains_20_to_100": gain,
        },
        "4_most_robust_model": {"answer": most_robust, "worst_case": worst},
        "5_direct_vs_disease_first": {
            "answer": hier_choice,
            "direct_department_accuracy": direct,
            "disease_first_department_accuracy": disease_dept,
        },
        "6_main_error_severity": {
            "answer": severity_main,
            "routing_error": routing,
        },
        "7_shadow_mode": readiness,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--quick", action="store_true", help="fewer seeds for smoke")
    args = parser.parse_args()
    RESULTS.mkdir(parents=True, exist_ok=True)
    seeds = (42, 123) if args.quick else SEEDS
    curve_seeds = (42,) if args.quick else (42, 123, 2026)

    print("[1/8] load datasets ...")
    structured = load_structured()
    expanded = load_expanded()
    print(f"  structured={len(structured.rows)} expanded={len(expanded.rows)}")

    print("[2/8] split/component audit ...")
    structured_limits = evaluate_component_definition_limits(structured)
    expanded_limits = evaluate_component_definition_limits(expanded)
    train, cal, test, split_meta = quota_split(expanded.rows, threshold=0.8, seed=42)
    leak = cross_split_leakage_audit(train, test)
    split_audit = {
        "structured": structured_limits,
        "expanded": expanded_limits,
        "primary_expanded_split_seed42": {**split_meta, "leakage": leak, "sources": expanded.sources},
    }

    print("[3/8] external eval schema ...")
    external_schema = write_external_eval_schema()
    inquiry_schema = write_schema_assets()

    print("[4/8] model matrix (multi-seed) ...")
    t0 = time.time()
    model_matrix = run_model_matrix(
        expanded.rows, seeds=seeds, threshold=0.8, protocol_name="expanded_quota_0.8"
    )
    print(f"  done in {time.time()-t0:.1f}s runs={model_matrix['run_count']}")

    print("[5/8] learning curve ...")
    curve = learning_curve(expanded.rows, seeds=curve_seeds, threshold=0.8)

    print("[6/8] robustness ...")
    robust = run_robustness(expanded.rows, seed=42, threshold=0.8)

    print("[7/8] hierarchical triage ...")
    hier = run_hierarchical_comparison(
        expanded.rows, seeds=(42, 123) if args.quick else (42, 123, 2026), threshold=0.8
    )

    print("[8/8] readiness + answers ...")
    payload = {
        "schema_version": "care-routing-round3/v1",
        "disclaimer": "离线研究；expanded 集来自仓库公开文本数据，不是临床病例；未改 Safety/生产 API。",
        "dataset_structured": structured.sources,
        "dataset_expanded": expanded.sources,
        "split_audit": split_audit,
        "external_eval_schema": external_schema,
        "inquiry_schema": inquiry_schema,
        "model_matrix": model_matrix,
        "learning_curve": curve,
        "robustness": robust,
        "hierarchical": hier,
    }
    payload["readiness"] = readiness_decision(payload)
    payload["seven_answers"] = seven_answers(payload)
    payload["limitations"] = [
        "expanded_41 仍是公开数据集文本，不是常州真实就诊分布。",
        "LR/SVM 为纯 Python 参考实现，非生产优化实现。",
        "robustness 为 simulation，未改红旗语义。",
        "外部专家标注集仅有 schema，无真实导入结果。",
    ]

    if args.write:
        for name, obj in [
            ("round3_split_audit.json", split_audit),
            ("round3_model_matrix.json", model_matrix),
            ("round3_learning_curve.json", curve),
            ("round3_robustness.json", robust),
            ("round3_hierarchical.json", hier),
            ("round3_report.json", payload),
        ]:
            (RESULTS / name).write_text(
                json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
        # CSV for technical docs
        csv_lines = [
            "fraction,nb_acc_mean,nb_acc_std,lr_acc_mean,lr_acc_std,svm_acc_mean,svm_acc_std,nb_dept_mean,lr_dept_mean"
        ]
        for row in curve["csv_ready"]:
            csv_lines.append(
                f"{row['fraction']},{row['nb_acc_mean']},{row['nb_acc_std']},{row['lr_acc_mean']},"
                f"{row['lr_acc_std']},{row['svm_acc_mean']},{row['svm_acc_std']},"
                f"{row['nb_dept_mean']},{row['lr_dept_mean']}"
            )
        (RESULTS / "round3_learning_curve.csv").write_text(
            "\n".join(csv_lines) + "\n", encoding="utf-8"
        )

    summary = {
        "expanded_rows": len(expanded.rows),
        "expanded_test_rows_seed42": split_meta["test_rows"],
        "expanded_test_diseases_seed42": split_meta["test_disease_count"],
        "leak_pairs": leak["pair_count"],
        "model_accuracy_mean": {
            name: model_matrix["headline"][name]["accuracy"]
            for name in (
                "multinomial_nb",
                "logistic_regression",
                "linear_svm",
                "tfidf_logistic_regression",
            )
        },
        "department_accuracy_mean": {
            name: model_matrix["headline"][name]["department_accuracy"]
            for name in ("multinomial_nb", "logistic_regression", "linear_svm")
        },
        "learning_gain": curve["accuracy_gain_20_to_100"],
        "robustness_worst": robust["worst_case"],
        "direct_dept": hier["direct_department_accuracy"],
        "disease_first_dept": hier["disease_first_department_accuracy"],
        "readiness": payload["readiness"]["decision"],
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
