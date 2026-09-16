"""Round-2 orchestrator: error analysis, tri-state inquiry, stopping, calibration, baselines.

Usage:
    .venv/bin/python -m evaluation.care_routing.run_round2 --write
"""

from __future__ import annotations

import argparse
import json
import math
import statistics
from pathlib import Path
from typing import Any, Mapping

from data.symptom_disease_model.train import fit, load_dataset

from evaluation.model.evaluate_grouped import ALPHA, MIN_SYMPTOM_DF, sha256_file

from .error_analysis import run_error_analysis, write_error_analysis_report
from .inquiry_protocol import (
    run_three_state_inquiry,
    summarize_three_state_runs,
    predict_with_states,
)
from .disease_department import department_for
from .metrics import evaluate_uncertainty_split
from .model_baselines import (
    build_binary_features,
    build_tfidf_features,
    evaluate_sklearn_like,
    fit_linear_svm,
    fit_logistic_regression,
)
from .run_experiments import component_triple_split, build_splits
from .stopping import (
    default_policies,
    fit_stopping_thresholds_from_calibration,
    policy_as_callable,
)
from .symptom_state import (
    SymptomState,
    parse_symptom_states_from_text,
)
from .uncertainty import (
    conformal_threshold,
    fit_temperature,
    distribution_entropy,
    top1_confidence,
    top_margin,
)
from .data_schema import write_schema_assets

ROOT = Path(__file__).resolve().parents[2]
DATASET = ROOT / "data/symptom_disease_model/data/disease_symptom_structured_41diseases_long.csv"
RESULTS = Path(__file__).with_name("results")
SEEDS = (42, 123, 2026, 3407, 7777)

# Minimal alias map for offline negation unit behavior (subset of production aliases).
NEGATION_ALIAS_MAP = {
    "胸痛": "chest_pain",
    "发热": "high_fever",
    "咳嗽": "cough",
    "呼吸困难": "breathlessness",
    "头痛": "headache",
    "恶心": "nausea",
    "腹泻": "diarrhoea",
    "头晕": "dizziness",
}


def run_negation_unit_cases() -> dict[str, Any]:
    cases = [
        ("胸痛", "chest_pain", SymptomState.PRESENT),
        ("没有胸痛", "chest_pain", SymptomState.ABSENT),
        ("目前没有明显胸痛", "chest_pain", SymptomState.ABSENT),
        ("不知道有没有发热", "high_fever", SymptomState.UNKNOWN),
        ("有咳嗽，没有胸痛", "cough", SymptomState.PRESENT),
        ("有咳嗽，没有胸痛", "chest_pain", SymptomState.ABSENT),
        ("否认发热，伴有头痛", "high_fever", SymptomState.ABSENT),
        ("否认发热，伴有头痛", "headache", SymptomState.PRESENT),
        ("无呼吸困难", "breathlessness", SymptomState.ABSENT),
        ("不伴腹泻", "diarrhoea", SymptomState.ABSENT),
    ]
    rows = []
    passed = 0
    for text, code, expected in cases:
        parsed = parse_symptom_states_from_text(text, NEGATION_ALIAS_MAP)
        observed = parsed.get(code)
        ok = observed is expected
        passed += int(ok)
        rows.append(
            {
                "text": text,
                "code": code,
                "expected": expected.value,
                "observed": observed.value,
                "pass": ok,
                "features": parsed.as_features(),
            }
        )
    return {
        "total": len(cases),
        "passed": passed,
        "failed": len(cases) - passed,
        "cases": rows,
        "note": "否定解析仅用于离线实验；红旗否定不得接入生产 Safety。",
    }


def calibration_robustness(dataset_path: Path, seeds: tuple[int, ...] = SEEDS) -> dict[str, Any]:
    rows = load_dataset(str(dataset_path))
    per_split: dict[str, list[dict[str, Any]]] = {
        "random_baseline": [],
        "grouped_fingerprint": [],
        "near_duplicate_same_label": [],
    }
    for seed in seeds:
        from data.symptom_disease_model.train import split_dataset
        from evaluation.model.evaluate_grouped import (
            TEST_SIZE,
            grouped_fingerprint_split,
        )

        random_train, random_test = split_dataset(rows, TEST_SIZE, seed)
        grouped_train, grouped_test, _ = grouped_fingerprint_split(rows, TEST_SIZE, seed)
        near_train, near_cal, near_test = component_triple_split(rows, seed=seed)
        splits = {
            "random_baseline": (random_train, random_test),
            "grouped_fingerprint": (grouped_train, grouped_test),
            "near_duplicate_same_label": (near_train, near_test),
        }
        cal_map = {
            "random_baseline": None,
            "grouped_fingerprint": None,
            "near_duplicate_same_label": near_cal,
        }
        for name, (train, test) in splits.items():
            model = fit(train, ALPHA, MIN_SYMPTOM_DF)
            cal_rows = cal_map.get(name)
            if cal_rows is None:
                # half-train calibration
                mid = max(1, len(train) // 2)
                cal_fit, cal_thr = train[:mid], train[mid:]
            else:
                cal_fit = cal_thr = cal_rows
            temperature = float(fit_temperature(model, cal_fit)["temperature"])
            conformal = conformal_threshold(model, cal_thr, alpha=0.1, temperature=temperature)
            raw = evaluate_uncertainty_split(model, test, temperature=1.0)
            calibrated = evaluate_uncertainty_split(
                model, test, temperature=temperature, conformal=conformal
            )
            per_split[name].append(
                {
                    "seed": seed,
                    "temperature": temperature,
                    "conformal_threshold": conformal["threshold"],
                    "raw_ece": raw["ece"],
                    "calibrated_ece": calibrated["ece"],
                    "raw_accuracy": raw["accuracy"],
                    "calibrated_coverage": calibrated["coverage"],
                    "mean_set_size": calibrated["mean_prediction_set_size"],
                    "test_rows": len(test),
                    "cal_rows": len(cal_fit),
                }
            )

    def agg(items: list[dict[str, Any]], key: str) -> dict[str, Any]:
        values = [float(item[key]) for item in items if item.get(key) is not None]
        if not values:
            return {"mean": None, "std": None, "values": []}
        mean = sum(values) / len(values)
        std = statistics.pstdev(values) if len(values) > 1 else 0.0
        return {"mean": round(mean, 6), "std": round(std, 6), "values": values}

    summary = {}
    for name, items in per_split.items():
        summary[name] = {
            "seeds": list(seeds),
            "raw_ece": agg(items, "raw_ece"),
            "calibrated_ece": agg(items, "calibrated_ece"),
            "raw_accuracy": agg(items, "raw_accuracy"),
            "coverage": agg(items, "calibrated_coverage"),
            "mean_set_size": agg(items, "mean_set_size"),
            "temperature": agg(items, "temperature"),
            "runs": items,
        }
    verdict = {
        "question": "Conformal/温度缩放是否适合作为拒答/追问触发器？",
        "answer": "RESEARCH_ONLY",
        "reason": (
            "近重复诚实协议下 coverage/set-size 对分布漂移敏感；"
            "多 seed 结果方差可见，且 calibration 样本很小。"
            "可作为研究展示与不确定性信号之一，不宜作为生产唯一拒答开关。"
        ),
    }
    return {"summary": summary, "verdict": verdict, "seeds": list(seeds)}


def model_baseline_comparison(dataset_path: Path, seed: int = 42) -> dict[str, Any]:
    rows = load_dataset(str(dataset_path))
    train, cal, test = component_triple_split(rows, seed=seed)
    train_labels = [row["disease"] for row in train]
    test_labels = [row["disease"] for row in test]

    # NB reference (current production-family model).
    nb = fit(train, ALPHA, MIN_SYMPTOM_DF)
    from .uncertainty import predict_distribution

    nb_correct = 0
    nb_top3 = 0
    for row in test:
        ranked = predict_distribution(nb, row["symptoms"])
        labels = [label for label, _ in ranked]
        nb_correct += int(bool(labels) and labels[0] == row["disease"])
        nb_top3 += int(row["disease"] in labels[:3])
    n = len(test)
    nb_report = {
        "model": "multinomial_nb",
        "accuracy": round(nb_correct / n, 6) if n else None,
        "top3_accuracy": round(nb_top3 / n, 6) if n else None,
    }

    train_bin = build_binary_features(train)
    test_bin = build_binary_features(test)
    lr = fit_logistic_regression(train_bin, train_labels, epochs=60, lr=0.4, seed=seed)
    lr_report = {"model": "logistic_regression_binary", **evaluate_sklearn_like(lr, test_bin, test_labels)}

    train_tfidf = build_tfidf_features(train, train)
    test_tfidf = build_tfidf_features(train, test)
    lr_tfidf = fit_logistic_regression(train_tfidf, train_labels, epochs=60, lr=0.4, seed=seed)
    lr_tfidf_report = {
        "model": "tfidf_logistic_regression",
        **evaluate_sklearn_like(lr_tfidf, test_tfidf, test_labels),
    }

    svm = fit_linear_svm(train_bin, train_labels, epochs=80, lr=0.15, seed=seed)
    svm_report = {"model": "linear_svm_binary", **evaluate_sklearn_like(svm, test_bin, test_labels)}

    reports = [nb_report, lr_report, lr_tfidf_report, svm_report]
    best = max(reports, key=lambda item: item.get("accuracy") or 0.0)
    verdict = {
        "question": "简单模型升级能否显著改善 near-dup 泛化？",
        "best_model": best["model"],
        "best_accuracy": best["accuracy"],
        "nb_accuracy": nb_report["accuracy"],
        "improvement_over_nb": round((best["accuracy"] or 0) - (nb_report["accuracy"] or 0), 6),
        "conclusion": (
            "若 improvement 很小，则 0.188 主因是数据/表达簇结构，而不是 NB 容量；"
            "若明显改善，再评估是否升级正式 Triage classifier（需 L3）。"
        ),
        "primary_selection_protocol": "near_duplicate_same_label only",
    }
    return {
        "seed": seed,
        "train_rows": len(train),
        "test_rows": len(test),
        "models": reports,
        "verdict": verdict,
    }


def three_state_inquiry_suite(dataset_path: Path, seed: int = 42) -> dict[str, Any]:
    rows = load_dataset(str(dataset_path))
    train, cal, test = component_triple_split(rows, seed=seed)
    model = fit(train, ALPHA, MIN_SYMPTOM_DF)

    # Fit stopping thresholds on calibration using a predict helper.
    def predict_fn(row: Mapping[str, Any]):
        ranked = predict_with_states(model, row["symptoms"], [], temperature=1.0)
        confidence = top1_confidence(ranked)
        entropy = distribution_entropy(ranked)
        margin = top_margin(ranked)
        set_size = min(3, len(ranked))
        max_entropy = math.log2(max(len(ranked), 2))
        return confidence, entropy, margin, set_size, max_entropy

    thresholds = fit_stopping_thresholds_from_calibration(cal, predict_fn)
    policies = default_policies(max_questions=5, thresholds=thresholds)
    strategies = ("information_gain", "random", "most_frequent", "margin", "fixed_order")

    results: dict[str, Any] = {
        "protocol": "three_state_simulation",
        "is_synthetic_oracle": True,
        "seed": seed,
        "train_rows": len(train),
        "cal_rows": len(cal),
        "test_rows": len(test),
        "stopping_thresholds_from_calibration": thresholds,
        "negation_unit": run_negation_unit_cases(),
        "policies": {},
    }

    # Primary comparison under combined stopping + forced max.
    primary: dict[str, Any] = {}
    for strategy in strategies:
        adaptive_runs = [
            run_three_state_inquiry(
                model,
                row,
                strategy=strategy,
                initial_symptom_count=1,
                max_questions=5,
                seed=seed,
                stopping_fn=policy_as_callable(policies[-1]),
            )
            for row in test
        ]
        forced_runs = [
            run_three_state_inquiry(
                model,
                row,
                strategy=strategy,
                initial_symptom_count=1,
                max_questions=5,
                seed=seed,
                force_questions=True,
            )
            for row in test
        ]
        primary[strategy] = {
            "adaptive_combined_stop": summarize_three_state_runs(adaptive_runs),
            "forced_max_questions": summarize_three_state_runs(forced_runs),
        }
    results["strategy_comparison"] = primary

    # Stopping policy comparison under IG strategy.
    stopping_rows = {}
    for policy in policies:
        runs = [
            run_three_state_inquiry(
                model,
                row,
                strategy="information_gain",
                initial_symptom_count=1,
                max_questions=policy.max_questions,
                seed=seed,
                stopping_fn=policy_as_callable(policy),
                force_questions=(policy.name == "fixed_n"),
            )
            for row in test
        ]
        stopping_rows[policy.name] = {
            "policy": policy.as_dict(),
            "metrics": summarize_three_state_runs(runs),
        }
    results["policies"] = stopping_rows

    # Accuracy-question cost points for Pareto (IG, varying max_questions).
    pareto = []
    for max_q in range(0, 6):
        runs = [
            run_three_state_inquiry(
                model,
                row,
                strategy="information_gain",
                initial_symptom_count=1,
                max_questions=max_q,
                seed=seed,
                force_questions=True,
            )
            for row in test
        ]
        summary = summarize_three_state_runs(runs)
        pareto.append(
            {
                "max_questions": max_q,
                "avg_questions": summary["avg_questions"],
                "final_accuracy": summary["final_accuracy"],
                "macro_f1_final": summary["macro_f1_final"],
                "wrong_but_confident_rate": summary["wrong_but_confident_rate"],
            }
        )
    results["accuracy_question_cost_pareto"] = pareto

    # Key scientific question: does IG still beat random/mostfreq with negatives?
    ig_forced = primary["information_gain"]["forced_max_questions"]
    rnd_forced = primary["random"]["forced_max_questions"]
    mf_forced = primary["most_frequent"]["forced_max_questions"]
    results["key_question_ig_vs_baselines"] = {
        "question": "IG 在加入 negative answers 后是否仍优于 Random / MostFreq？",
        "ig_final_accuracy": ig_forced["final_accuracy"],
        "random_final_accuracy": rnd_forced["final_accuracy"],
        "most_frequent_final_accuracy": mf_forced["final_accuracy"],
        "ig_minus_random": round((ig_forced["final_accuracy"] or 0) - (rnd_forced["final_accuracy"] or 0), 6),
        "ig_minus_most_frequent": round((ig_forced["final_accuracy"] or 0) - (mf_forced["final_accuracy"] or 0), 6),
        "note": "oracle 为 held-out 症状集合的三态模拟，不是真实患者。",
    }
    return results


def readiness_decision(
    error_payload: dict[str, Any],
    inquiry_payload: dict[str, Any],
    calibration_payload: dict[str, Any],
    baseline_payload: dict[str, Any],
) -> dict[str, Any]:
    neg = inquiry_payload.get("negation_unit", {})
    ig = inquiry_payload.get("key_question_ig_vs_baselines", {})
    best_gain = max(
        (ig.get("ig_minus_random") or 0),
        (ig.get("ig_minus_most_frequent") or 0),
    )
    honest_acc = error_payload["error_profile"]["accuracy"]
    nb_acc = baseline_payload["verdict"]["nb_accuracy"]
    best_model_acc = baseline_payload["verdict"]["best_accuracy"]
    improvement = baseline_payload["verdict"]["improvement_over_nb"]

    evidence = [
        f"诚实 near-dup Accuracy={honest_acc}，Top-3={error_payload['error_profile']['topk_accuracy'].get('3')}",
        f"单 component 疾病 {error_payload['component_inventory']['single_component_disease_count']}/41",
        f"否定解析单测通过 {neg.get('passed')}/{neg.get('total')}",
        f"三态模拟下 IG-相对优势（forced）≈ {best_gain}（诚实切分上未稳定优于 Random）",
        f"模型对照 best={best_model_acc} vs NB={nb_acc}，Δ={improvement}（test n 小，需更多数据再谈上线）",
        f"校准/conformal verdict={calibration_payload['verdict']['answer']}",
    ]

    # Product readiness: we require honest generalization + real multi-turn data.
    # Neither exists yet → not READY. Conformal is research-only. Inquiry is simulation.
    decision = "RESEARCH_ONLY"
    rationale = (
        "算法链路（不确定→选题→三态更新→停止）可离线复现，且否定解析单测通过；"
        "但真实多轮患者数据缺失、诚实泛化弱、conformal 仅研究可用，故不能接入正式产品决策，"
        "也不应作为 NOT_READY（原型本身有效且可继续研究）。"
    )
    return {
        "question": "当前证据是否足够把 Uncertainty → Adaptive Inquiry 接入正式产品？",
        "decision": decision,
        "rationale": rationale,
        "evidence": evidence,
        "blocked_by": [
            "无真实多轮 inquiry 数据（仅有 synthetic schema）",
            "near-dup 诚实泛化不足，错误仍集中",
            "红旗否定解析禁止直接进 Safety",
            "conformal 在漂移协议下不够稳健",
        ],
        "allowed_now": [
            "继续离线研究与论文/答辩材料",
            "在 Trust/研究页展示不确定性指标（需标注 assistive_only）",
            "准备 opt-in 采集 schema 与质检",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=DATASET)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    RESULTS.mkdir(parents=True, exist_ok=True)

    print("[1/6] error analysis ...")
    error_payload = run_error_analysis(dataset_path=str(args.dataset), seed=args.seed)
    print("[2/6] negation + three-state inquiry ...")
    inquiry_payload = three_state_inquiry_suite(args.dataset, seed=args.seed)
    print("[3/6] calibration robustness (multi-seed) ...")
    calibration_payload = calibration_robustness(args.dataset)
    print("[4/6] model baselines ...")
    baseline_payload = model_baseline_comparison(args.dataset, seed=args.seed)
    print("[5/6] inquiry schema ...")
    schema_payload = write_schema_assets()
    print("[6/6] readiness ...")
    readiness = readiness_decision(error_payload, inquiry_payload, calibration_payload, baseline_payload)

    report = {
        "schema_version": "care-routing-round2/v1",
        "dataset": {
            "path": str(args.dataset.relative_to(ROOT)),
            "sha256": sha256_file(args.dataset),
        },
        "error_analysis": error_payload,
        "three_state_inquiry": inquiry_payload,
        "calibration_robustness": calibration_payload,
        "model_baselines": baseline_payload,
        "inquiry_schema": schema_payload,
        "readiness": readiness,
        "six_answers": {
            "1_near_dup_root_cause": error_payload["root_cause"]["headline"],
            "2_three_state_supports_negatives": (
                "是（解析层）" if inquiry_payload["negation_unit"]["failed"] == 0 else "否（单测未全过）"
            ),
            "3_ig_still_better_with_negatives": inquiry_payload["key_question_ig_vs_baselines"],
            "4_best_stopping_policy": _best_policy_summary(inquiry_payload),
            "5_simple_model_helps_near_dup": baseline_payload["verdict"],
            "6_product_readiness": readiness["decision"],
        },
        "disclaimer": "Round2 离线研究；三态追问为 simulation；不改 Safety Gate / 生产 API。",
        "limitations": [
            "无真实患者多轮对话。",
            "诚实 test 覆盖病种有限。",
            "纯 Python LR/SVM 仅作容量对照，非生产模型。",
            "stopping 阈值来自 calibration 分位数，样本少。",
        ],
    }

    if args.write:
        (RESULTS / "round2_error_analysis.json").write_text(
            json.dumps(error_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        (RESULTS / "round2_inquiry.json").write_text(
            json.dumps(inquiry_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        (RESULTS / "round2_calibration.json").write_text(
            json.dumps(calibration_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        (RESULTS / "round2_model_baselines.json").write_text(
            json.dumps(baseline_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        (RESULTS / "round2_report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        write_error_analysis_report(error_payload, RESULTS / "round2_error_analysis.md")

    summary = {
        "near_dup_accuracy": error_payload["error_profile"]["accuracy"],
        "near_dup_top3": error_payload["error_profile"]["topk_accuracy"].get("3"),
        "single_component_diseases": error_payload["component_inventory"]["single_component_disease_count"],
        "negation_unit": f"{inquiry_payload['negation_unit']['passed']}/{inquiry_payload['negation_unit']['total']}",
        "ig_vs": inquiry_payload["key_question_ig_vs_baselines"],
        "best_policy_accuracy": {
            name: payload["metrics"]["final_accuracy"]
            for name, payload in inquiry_payload["policies"].items()
        },
        "best_policy_avg_q": {
            name: payload["metrics"]["avg_questions"]
            for name, payload in inquiry_payload["policies"].items()
        },
        "model_verdict": baseline_payload["verdict"],
        "calibration_verdict": calibration_payload["verdict"]["answer"],
        "readiness": readiness["decision"],
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


def _best_policy_summary(inquiry_payload: dict[str, Any]) -> dict[str, Any]:
    policies = inquiry_payload.get("policies") or {}
    if not policies:
        return {}
    # Prefer higher accuracy; tie-break lower avg questions.
    ranked = sorted(
        policies.items(),
        key=lambda item: (
            -(item[1]["metrics"]["final_accuracy"] or 0.0),
            item[1]["metrics"]["avg_questions"] or 99,
        ),
    )
    name, payload = ranked[0]
    return {
        "name": name,
        "final_accuracy": payload["metrics"]["final_accuracy"],
        "avg_questions": payload["metrics"]["avg_questions"],
        "wrong_but_confident_rate": payload["metrics"]["wrong_but_confident_rate"],
        "policy": payload["policy"],
    }


if __name__ == "__main__":
    raise SystemExit(main())
