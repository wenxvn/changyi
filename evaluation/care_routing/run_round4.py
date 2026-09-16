"""Round4 orchestrator: Safety-Constrained Selective Care Routing experiments."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

from .department_confusion import (
    data_gap_map,
    department_confusion_report,
    shared_symptom_stats,
)
from .direct_department import fit_direct_department_models, run_direct_department_matrix
from .disease_department import department_for
from .round3_split_audit import load_expanded, quota_split
from .round4_learning import direct_department_learning_curve, representation_ablation_from_matrix
from .round4_robustness_safety import robustness_selective, safety_first_offline_check
from .selective_routing import run_selective_routing

RESULTS = Path(__file__).with_name("results")
SEEDS = (42, 123, 2026, 3407, 7777)
ROUND3_DIRECT_DEPT = 0.450262


def readiness_decision(payload: dict[str, Any]) -> dict[str, Any]:
    matrix = payload["direct_department_matrix"]
    best = matrix["aggregate"]["best_model"]
    best_acc = matrix["aggregate"]["best_accuracy"]
    headline = matrix["aggregate"]["headline"]
    best_std = headline[best]["accuracy"]["std"] if best else None

    selective = payload["selective_routing"]
    required = selective.get("required_coverages_max_prob") or {}
    acc_80 = (required.get("80%") or {}).get("retained_accuracy")
    acc_70 = (required.get("70%") or {}).get("retained_accuracy")
    acc_60 = (required.get("60%") or {}).get("retained_accuracy")
    wbc_80 = (required.get("80%") or {}).get("wrong_but_confident_rate")

    improved = best_acc is not None and best_acc >= ROUND3_DIRECT_DEPT + 0.03
    stable = (best_std or 0) <= 0.08
    risk_cov_ok = acc_80 is not None and acc_80 >= 0.60
    wrong_conf_ok = wbc_80 is not None and wbc_80 <= 0.08
    safety_ok = payload["safety_check"]["all_pass"]
    calib = headline[best]["ece"]["mean"] if best else None
    calib_ok = calib is not None and calib <= 0.15
    # Coverage of retained departments
    test_depts = None
    if matrix["runs"]:
        test_depts = matrix["runs"][0]["split_meta"]["test_departments"]
    coverage_ok = (test_depts or 0) >= 10

    conditions = {
        "better_than_round3_direct": bool(improved),
        "multi_seed_stable": bool(stable),
        "risk_coverage_retained_acc_ok": bool(risk_cov_ok),
        "wrong_but_confident_ok": bool(wrong_conf_ok),
        "calibration_ok": bool(calib_ok),
        "safety_regression_unchanged": bool(safety_ok),
        "department_coverage_ok": bool(coverage_ok),
    }

    if all(conditions.values()) and (best_acc or 0) >= 0.70 and (acc_80 or 0) >= 0.70:
        decision = "CANDIDATE_FOR_SHADOW_MODE"
    elif conditions["better_than_round3_direct"] and conditions["safety_regression_unchanged"]:
        decision = "RESEARCH_ONLY"
    else:
        decision = "RESEARCH_ONLY"

    return {
        "decision": decision,
        "conditions": conditions,
        "evidence": [
            f"best={best} acc={best_acc}±{best_std} (Round3 direct was {ROUND3_DIRECT_DEPT})",
            f"retained acc @80/70/60% = {acc_80}/{acc_70}/{acc_60}",
            f"wrong-but-confident @80% = {wbc_80}",
            f"ECE={calib}",
            f"test_departments={test_depts}",
            f"safety_check={safety_ok}",
        ],
        "note": "即使 CANDIDATE_FOR_SHADOW_MODE 也不替换生产模型",
    }


def eight_answers(payload: dict[str, Any]) -> dict[str, Any]:
    matrix = payload["direct_department_matrix"]
    agg = matrix["aggregate"]
    best = agg["best_model"]
    selective = payload["selective_routing"]
    confusion = payload["department_confusion"]
    gap = payload["data_gap_map"]
    ablation = payload["representation_ablation"]
    curve = payload["learning_curve"]
    readiness = payload["readiness"]

    hardest_pairs = confusion.get("top_confusion_pairs") or []
    top_pair = hardest_pairs[0] if hardest_pairs else None

    return {
        "1_best_direct_department_model": {
            "model": best,
            "accuracy": agg["best_accuracy"],
            "ranking": agg["ranking"][:5],
        },
        "2_vs_round3_0_45": {
            "round3": ROUND3_DIRECT_DEPT,
            "round4": agg["best_accuracy"],
            "delta": round((agg["best_accuracy"] or 0) - ROUND3_DIRECT_DEPT, 6),
        },
        "3_risk_coverage": selective.get("required_coverages_max_prob"),
        "4_accuracy_at_coverages": {
            "80%": (selective.get("required_coverages_max_prob") or {}).get("80%"),
            "70%": (selective.get("required_coverages_max_prob") or {}).get("70%"),
            "60%": (selective.get("required_coverages_max_prob") or {}).get("60%"),
        },
        "5_hardest_department_pair": top_pair,
        "6_top_data_gaps": gap.get("top_n_to_collect") or [],
        "7_best_representation": {
            "under_lr": ablation.get("best_representation_under_lr"),
            "ranking": ablation.get("lr_representation_ranking"),
        },
        "8_shadow_mode": readiness,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--quick", action="store_true")
    args = parser.parse_args()
    RESULTS.mkdir(parents=True, exist_ok=True)
    seeds = (42, 123) if args.quick else SEEDS
    curve_seeds = (42,) if args.quick else (42, 123, 2026)

    print("[1/8] load expanded dataset ...")
    bundle = load_expanded()
    rows = bundle.rows
    print(f"  rows={len(rows)}")

    print("[2/8] Direct Department matrix ...")
    t0 = time.time()
    matrix = run_direct_department_matrix(rows, seeds=seeds, threshold=0.8)
    print(f"  best={matrix['aggregate']['best_model']} acc={matrix['aggregate']['best_accuracy']} ({time.time()-t0:.1f}s)")

    print("[3/8] Selective routing ...")
    train, cal, test, split_meta = quota_split(rows, threshold=0.8, seed=42)
    best_model = matrix["aggregate"]["best_model"] or "logistic_regression_binary"
    selective = run_selective_routing(
        train, cal, test, seed=42, model_name=best_model
    )
    selective["matrix_best_model"] = best_model
    selective["selective_evaluated_model"] = best_model

    print("[4/8] Confusion + shared features ...")
    fitted = fit_direct_department_models(train, cal, test, seed=42)
    preds = fitted["_predictions"][best_model]
    confusion = department_confusion_report(preds["y_true"], preds["y_pred"])
    # Enrich with shared stats for top pair
    if confusion["top_confusion_pairs"]:
        pair = confusion["top_confusion_pairs"][0]
        confusion["top_pair_shared_features"] = shared_symptom_stats(
            train, pair["true"], pair["pred"]
        )

    print("[5/8] Data gap map ...")
    recall_map = fitted["models"][best_model].get("per_department_recall") or {}
    gap = data_gap_map(
        rows,
        y_true=preds["y_true"],
        y_pred=preds["y_pred"],
        per_department_recall=recall_map,
        threshold=0.8,
        seed=42,
    )

    print("[6/8] Learning curve + ablation ...")
    curve = direct_department_learning_curve(
        rows,
        seeds=curve_seeds,
        model_keys=("logistic_regression_binary", "char_ngram_tfidf_lr"),
        threshold=0.8,
    )
    ablation = representation_ablation_from_matrix(matrix)

    print("[7/8] Robustness + Safety ...")
    robust = robustness_selective(rows, seed=42, threshold=0.8)
    safety = safety_first_offline_check(
        department_model_accuracy=matrix["aggregate"]["best_accuracy"]
    )

    print("[8/8] Readiness + answers ...")
    payload = {
        "schema_version": "care-routing-round4/v1",
        "disclaimer": "离线研究；Safety Gate 未改；非临床验证；数据为公开文本集",
        "dataset": bundle.sources,
        "split_meta_seed42": split_meta,
        "direct_department_matrix": matrix,
        "selective_routing": selective,
        "department_confusion": confusion,
        "data_gap_map": gap,
        "learning_curve": curve,
        "representation_ablation": ablation,
        "robustness_selective": robust,
        "safety_check": safety,
    }
    payload["readiness"] = readiness_decision(payload)
    payload["eight_answers"] = eight_answers(payload)
    payload["limitations"] = [
        "expanded_41 为公开文本，不是常州就诊分布",
        "char n-gram 作用在症状码拼接文本，不是原始中文口语全文",
        "Selective 阈值仅来自 calibration；test 未调参",
        "数据优先级不是医疗重要性排名",
    ]

    if args.write:
        for name, obj in [
            ("round4_direct_department_matrix.json", matrix),
            ("round4_selective_routing.json", selective),
            ("round4_department_confusion.json", confusion),
            ("round4_data_gap_map.json", gap),
            ("round4_learning_curve.json", curve),
            ("round4_representation_ablation.json", ablation),
            ("round4_robustness_selective.json", robust),
            ("round4_safety_check.json", safety),
            ("round4_report.json", payload),
        ]:
            (RESULTS / name).write_text(
                json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
        # Risk-coverage CSV
        lines = ["signal,target_coverage,test_coverage,retained_accuracy,retained_macro_f1,error_rate,wrong_but_confident_rate"]
        for signal, curve_payload in (selective.get("risk_coverage") or {}).items():
            for point in curve_payload.get("points") or []:
                lines.append(
                    f"{signal},{point['target_coverage']},{point['coverage']},"
                    f"{point['retained_accuracy']},{point['retained_macro_f1']},"
                    f"{point['retained_error_rate']},{point['retained_wrong_but_confident_rate']}"
                )
        (RESULTS / "round4_risk_coverage.csv").write_text("\n".join(lines) + "\n", encoding="utf-8")
        # Data gap CSV
        gap_lines = [
            "priority_rank,department,train_count,component_count,test_count,recall,unseen_symptom_ratio,data_priority_score"
        ]
        for entry in gap["departments"]:
            gap_lines.append(
                f"{entry['priority_rank']},{entry['department']},{entry['train_count']},"
                f"{entry['component_count']},{entry['test_count']},{entry['recall']},"
                f"{entry['unseen_symptom_ratio']},{entry['data_priority_score']}"
            )
        (RESULTS / "round4_data_gap_map.csv").write_text("\n".join(gap_lines) + "\n", encoding="utf-8")

    summary = {
        "best_model": matrix["aggregate"]["best_model"],
        "best_accuracy": matrix["aggregate"]["best_accuracy"],
        "ranking_top3": matrix["aggregate"]["ranking"][:3],
        "selective_80_70_60": {
            key: (selective.get("required_coverages_max_prob") or {}).get(key)
            for key in ("80%", "70%", "60%")
        },
        "top_confusion_pair": (confusion.get("top_confusion_pairs") or [None])[0],
        "top_data_gaps": [item["department"] for item in (gap.get("top_n_to_collect") or [])[:5]],
        "best_representation": ablation.get("best_representation_under_lr"),
        "learning_trend": curve.get("trend"),
        "safety_all_pass": safety.get("all_pass"),
        "readiness": payload["readiness"]["decision"],
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
