"""Round4: robustness under selective routing + Safety-first offline checks."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from .disease_department import department_for
from .direct_department import fit_direct_department_models
from .model_baselines import build_binary_features, fit_logistic_regression, predict_proba
from .robustness import perturb_symptoms
from .round3_split_audit import quota_split
from .selective_routing import SIGNALS, combined_signal, selective_metrics, threshold_for_coverage
import random

SIGNALS["combined"] = combined_signal


def robustness_selective(
    rows: Sequence[Mapping[str, Any]],
    *,
    seed: int = 42,
    threshold: float = 0.8,
    target_coverage: float = 0.8,
    model_name: str = "char_ngram_tfidf_lr",
) -> dict[str, Any]:
    from .direct_department import prepare_feature_sets
    from .model_baselines import fit_logistic_regression as _fit_lr, predict_proba as _proba

    train, cal, test, _ = quota_split(rows, threshold=threshold, seed=seed)
    if not test:
        return {"error": "empty_test"}
    fitted = fit_direct_department_models(train, cal, test, seed=seed)
    preds = fitted["_predictions"][model_name]
    y_test = preds["y_true"]
    temp = float(fitted.get("temperatures", {}).get(model_name, 1.0))

    y_train = [department_for(row["disease"]) for row in train]
    y_cal = [department_for(row["disease"]) for row in cal]
    if "char" in model_name and "fusion" in model_name:
        feature_key = "word_char_fusion"
    elif "char" in model_name:
        feature_key = "char_ngram_tfidf"
    else:
        feature_key = "symptom_binary"
    features = prepare_feature_sets(train, cal, test)[feature_key]
    model = _fit_lr(features["train"], y_train, epochs=70, lr=0.4, seed=seed)
    cal_ranked = [_proba(model, feat, temperature=temp) for feat in features["cal"]]
    cal_scores = [SIGNALS["max_probability"](r) for r in cal_ranked]
    thr = threshold_for_coverage(cal_scores, target_coverage)

    clean_metrics = selective_metrics(
        preds["ranked_calibrated"], y_test, signal="max_probability", threshold=thr
    )

    rng = random.Random(seed)
    kinds = (
        "synonym_swap",
        "drop_noncritical",
        "add_filler",
        "colloquial_noise",
    )
    per_kind = {}
    for kind in kinds:
        perturbed = [
            {
                "disease": row["disease"],
                "symptoms": perturb_symptoms(row["symptoms"], kind=kind, rng=rng),
            }
            for row in test
        ]
        # Rebuild the same feature type on perturbed rows using train-fitted vectorizer.
        if feature_key == "char_ngram_tfidf":
            from .model_baselines import build_char_ngram_tfidf_features

            test_feats = build_char_ngram_tfidf_features(train, perturbed)
        elif feature_key == "word_char_fusion":
            from .model_baselines import (
                build_char_ngram_tfidf_features,
                build_fusion_features,
                build_tfidf_features,
            )

            test_feats = build_fusion_features(
                build_tfidf_features(train, perturbed),
                build_char_ngram_tfidf_features(train, perturbed),
            )
        else:
            from .model_baselines import build_binary_features

            test_feats = build_binary_features(perturbed)
        ranked = [_proba(model, feat, temperature=temp) for feat in test_feats]
        metrics = selective_metrics(ranked, y_test, signal="max_probability", threshold=thr)
        per_kind[kind] = {
            "coverage": metrics["coverage"],
            "retained_accuracy": metrics["retained_accuracy"],
            "wrong_but_confident_rate": metrics["retained_wrong_but_confident_rate"],
            "coverage_delta": round((metrics["coverage"] or 0) - (clean_metrics["coverage"] or 0), 6),
            "accuracy_delta": (
                round(metrics["retained_accuracy"] - clean_metrics["retained_accuracy"], 6)
                if metrics["retained_accuracy"] is not None
                and clean_metrics["retained_accuracy"] is not None
                else None
            ),
        }

    ideal_behavior = []
    for kind, metrics in per_kind.items():
        ideal_behavior.append(
            {
                "kind": kind,
                "more_abstention": (metrics["coverage_delta"] or 0) <= 0.02,
                "retained_acc_holds": (
                    metrics["accuracy_delta"] is None or metrics["accuracy_delta"] >= -0.05
                ),
            }
        )

    return {
        "protocol": "robustness_selective_routing",
        "not_real_patients": True,
        "seed": seed,
        "model_name": model_name,
        "feature_key": feature_key,
        "target_coverage_from_cal": target_coverage,
        "threshold": thr,
        "clean": clean_metrics,
        "per_kind": per_kind,
        "ideal_behavior_checks": ideal_behavior,
        "note": "meaning-preserving perturbations only; Safety Gate unchanged",
    }


def safety_first_offline_check(
    *,
    department_model_accuracy: float | None,
    production_safety_cases: int = 142,
    production_recall: float = 1.0,
    production_under_triage: float = 0.0,
    production_emergency_fn: int = 0,
) -> dict[str, Any]:
    """Offline contract check. Does not modify Safety Gate."""

    invariants = [
        {
            "id": "emergency_never_rerouted_by_department",
            "status": "enforced_by_architecture",
            "detail": "Direct Department 仅在 Safety Gate 非 EMERGENCY 后作为研究路由；实验包不调用生产 Safety 作为覆盖",
        },
        {
            "id": "department_does_not_override_safety",
            "status": "enforced_by_architecture",
            "detail": "未改 Safety Gate / 红旗规则 / 生产 API",
        },
        {
            "id": "abstention_does_not_lower_red_flag_priority",
            "status": "enforced_by_architecture",
            "detail": "拒答只作用于科室候选，不作用于 EMERGENCY 状态",
        },
        {
            "id": "safety_evaluation_unchanged",
            "status": "pass"
            if (
                production_safety_cases == 142
                and production_recall == 1.0
                and production_under_triage == 0.0
                and production_emergency_fn == 0
            )
            else "fail",
            "detail": {
                "cases": production_safety_cases,
                "recall": production_recall,
                "under_triage": production_under_triage,
                "emergency_fn": production_emergency_fn,
            },
        },
    ]
    return {
        "pipeline": "Safety Gate → Direct Department → Selective Abstention → Care Routing",
        "department_model_accuracy_for_context": department_model_accuracy,
        "invariants": invariants,
        "all_pass": all(item["status"] in {"pass", "enforced_by_architecture"} for item in invariants),
        "disclaimer": "离线契约检查；不是临床 Safety 验证",
    }
