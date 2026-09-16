"""Recompute only seed=42 selective/confusion/robustness for the best Direct Department model.

Used to refresh Round4 artifacts without re-running the full multi-seed matrix.
"""

from __future__ import annotations

import json
from pathlib import Path

from evaluation.care_routing.department_confusion import (
    data_gap_map,
    department_confusion_report,
    shared_symptom_stats,
)
from evaluation.care_routing.direct_department import fit_direct_department_models
from evaluation.care_routing.round3_split_audit import load_expanded, quota_split
from evaluation.care_routing.round4_robustness_safety import (
    robustness_selective,
    safety_first_offline_check,
)
from evaluation.care_routing.selective_routing import run_selective_routing

RESULTS = Path(__file__).resolve().parent / "results"


def main() -> int:
    rows = load_expanded().rows
    train, cal, test, split_meta = quota_split(rows, threshold=0.8, seed=42)
    report_path = RESULTS / "round4_report.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    best_model = report["direct_department_matrix"]["aggregate"]["best_model"]
    print("best_model", best_model)

    print("selective ...")
    selective = run_selective_routing(train, cal, test, seed=42, model_name=best_model)
    selective["matrix_best_model"] = best_model
    selective["selective_evaluated_model"] = best_model

    print("confusion ...")
    fitted = fit_direct_department_models(train, cal, test, seed=42)
    preds = fitted["_predictions"][best_model]
    confusion = department_confusion_report(preds["y_true"], preds["y_pred"])
    if confusion["top_confusion_pairs"]:
        pair = confusion["top_confusion_pairs"][0]
        confusion["top_pair_shared_features"] = shared_symptom_stats(
            train, pair["true"], pair["pred"]
        )

    print("data gap ...")
    recall_map = fitted["models"][best_model].get("per_department_recall") or {}
    gap = data_gap_map(
        rows,
        y_true=preds["y_true"],
        y_pred=preds["y_pred"],
        per_department_recall=recall_map,
        threshold=0.8,
        seed=42,
    )

    print("robustness ...")
    robust = robustness_selective(rows, seed=42, threshold=0.8, model_name=best_model)
    safety = safety_first_offline_check(
        department_model_accuracy=report["direct_department_matrix"]["aggregate"]["best_accuracy"]
    )

    # Update readiness with refreshed selective numbers.
    from evaluation.care_routing.run_round4 import eight_answers, readiness_decision

    report["selective_routing"] = selective
    report["department_confusion"] = confusion
    report["data_gap_map"] = gap
    report["robustness_selective"] = robust
    report["safety_check"] = safety
    report["readiness"] = readiness_decision(report)
    report["eight_answers"] = eight_answers(report)

    for name, obj in [
        ("round4_selective_routing.json", selective),
        ("round4_department_confusion.json", confusion),
        ("round4_data_gap_map.json", gap),
        ("round4_robustness_selective.json", robust),
        ("round4_safety_check.json", safety),
        ("round4_report.json", report),
    ]:
        (RESULTS / name).write_text(
            json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    lines = [
        "signal,target_coverage,test_coverage,retained_accuracy,retained_macro_f1,error_rate,wrong_but_confident_rate"
    ]
    for signal, curve_payload in (selective.get("risk_coverage") or {}).items():
        for point in curve_payload.get("points") or []:
            lines.append(
                f"{signal},{point['target_coverage']},{point['coverage']},"
                f"{point['retained_accuracy']},{point['retained_macro_f1']},"
                f"{point['retained_error_rate']},{point['retained_wrong_but_confident_rate']}"
            )
    (RESULTS / "round4_risk_coverage.csv").write_text("\n".join(lines) + "\n", encoding="utf-8")

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
        "best_model": best_model,
        "best_accuracy": report["direct_department_matrix"]["aggregate"]["best_accuracy"],
        "selective": selective.get("required_coverages_max_prob"),
        "top_pair": (confusion.get("top_confusion_pairs") or [None])[0],
        "top_gaps": [x["department"] for x in (gap.get("top_n_to_collect") or [])[:5]],
        "readiness": report["readiness"]["decision"],
        "conditions": report["readiness"]["conditions"],
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
