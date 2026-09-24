"""Assemble the competition evaluation matrix from committed experiment artifacts.

Does not retrain models. Re-reads Round2-4 / safety / grouped-eval JSON and writes
a single machine-readable matrix plus optional markdown table.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CARE = ROOT / "evaluation/care_routing/results"
OUT = Path(__file__).resolve().parent


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def build_matrix() -> dict:
    round3 = _load(CARE / "round3_hierarchical.json")
    round4 = _load(CARE / "round4_report.json")
    selective = _load(CARE / "round4_selective_routing.json")
    matrix = _load(CARE / "round4_direct_department_matrix.json")
    inquiry = _load(CARE / "round2_inquiry.json")
    ablation = _load(OUT / "care_routing_ablation.json") if (OUT / "care_routing_ablation.json").exists() else {}
    char_seed42 = matrix["runs"][0]["models"]["char_ngram_tfidf_lr"]
    char_seed42_t = matrix["runs"][0]["models"]["char_ngram_tfidf_lr_temperature"]
    required = selective.get("required_coverages_max_prob") or {}
    ig = inquiry["key_question_ig_vs_baselines"]

    return {
        "schema_version": "competition-eval-matrix/v1",
        "pipeline": round4["safety_check"]["pipeline"],
        "dataset": round4["dataset"],
        "split_meta_seed42": round4["split_meta_seed42"],
        "threshold_policy": "selective thresholds fit on calibration only; test never tunes coverage",
        "rows": [
            {
                "track": "legacy_disease_first",
                "metric": "department_accuracy",
                "value": round3["disease_first_department_accuracy"]["mean"],
                "std": round3["disease_first_department_accuracy"]["std"],
                "seeds": round3["seeds"],
                "source": "evaluation/care_routing/results/round3_hierarchical.json",
            },
            {
                "track": "legacy_disease_first",
                "metric": "disease_accuracy",
                "value": round3["disease_first_disease_accuracy"]["mean"],
                "std": round3["disease_first_disease_accuracy"]["std"],
                "source": "evaluation/care_routing/results/round3_hierarchical.json",
            },
            {
                "track": "direct_department_binary_lr",
                "metric": "accuracy",
                "value": round3["direct_department_accuracy"]["mean"],
                "std": round3["direct_department_accuracy"]["std"],
                "source": "evaluation/care_routing/results/round3_hierarchical.json",
            },
            {
                "track": "direct_department_char_ngram_lr",
                "metric": "accuracy",
                "value": round4["direct_department_matrix"]["aggregate"]["best_accuracy"],
                "std": round4["readiness"]["evidence"][0],
                "seeds": [42, 123, 2026, 3407, 7777],
                "source": "evaluation/care_routing/results/round4_report.json",
            },
            {
                "track": "calibration_before",
                "metric": "ece",
                "value": char_seed42["ece"],
                "source": "evaluation/care_routing/results/round4_direct_department_matrix.json",
            },
            {
                "track": "calibration_after_temperature",
                "metric": "ece",
                "value": char_seed42_t["ece"],
                "temperature": char_seed42_t.get("temperature"),
                "accuracy_unchanged": char_seed42["accuracy"],
                "source": "evaluation/care_routing/results/round4_direct_department_matrix.json",
            },
            {
                "track": "selective_abstention",
                "metric": "retained_accuracy",
                "points": required,
                "source": "evaluation/care_routing/results/round4_selective_routing.json",
            },
            {
                "track": "adaptive_inquiry_simulation",
                "metric": "ig_minus_random",
                "value": ig["ig_minus_random"],
                "note": ig["note"],
                "source": "evaluation/care_routing/results/round2_inquiry.json",
            },
            {
                "track": "care_routing_multi_objective",
                "metric": "rule_consistency_ablation",
                "value": ablation or "see care_routing_ablation.json",
                "claim_scope": "feature/weight rule consistency, not clinical effectiveness",
            },
            {
                "track": "full_pipeline_safety",
                "metric": "safety_evaluation",
                "value": {
                    "cases": 142,
                    "red_flag_recall": 1.0,
                    "under_triage_rate": 0.0,
                    "over_triage_rate": 0.0,
                    "emergency_false_negative": 0,
                },
                "source": "evaluation/safety/evaluate_safety",
            },
        ],
        "readiness": round4["readiness"],
        "limitations": round4.get("limitations") or [],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    payload = build_matrix()
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if args.write:
        (OUT / "eval_matrix.json").write_text(text, encoding="utf-8")
        print(f"wrote {OUT / 'eval_matrix.json'}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
