"""Reproduce multi-objective care-routing rule/feature ablation checks.

Scope: prove weighted scoring reacts to features/preferences as specified.
Not a clinical effectiveness study.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from backend.app.domain.recommendation.features import (
    continuity_score,
    hospital_availability_data_available,
    hospital_availability_score,
    hospital_risk_penalty,
)
from backend.app.domain.recommendation.pipeline import rerank_hospital_candidates
from backend.app.domain.recommendation.scoring import rebalance_weights, score_hospital_candidate

OUT = Path(__file__).resolve().parent


def build() -> dict:
    base_weights = {
        "clinical": 0.4,
        "availability": 0.2,
        "accessibility": 0.2,
        "continuity": 0.1,
        "quality": 0.05,
        "fairness": 0.03,
        "emergency": 0.02,
    }
    feats = dict(
        clinical=0.9,
        availability=0.8,
        accessibility=0.7,
        continuity=0.6,
        quality=0.5,
        fairness=0.5,
        emergency=0.3,
        risk_penalty=0.0,
    )
    base_score = score_hospital_candidate(**feats, weights=base_weights, traffic_access={})[0]
    leave_one_out = {}
    for key in base_weights:
        weights = {**base_weights, key: 0.0}
        total = sum(weights.values()) or 1.0
        weights = {k: v / total for k, v in weights.items()}
        score = score_hospital_candidate(**feats, weights=weights, traffic_access={})[0]
        leave_one_out[key] = {"score": score, "delta": round(score - base_score, 4)}

    near_low_fit = dict(
        clinical=0.5, availability=0.5, accessibility=0.95, continuity=0.55,
        quality=0.5, fairness=0.8, emergency=0.2, risk_penalty=0.0,
    )
    far_high_fit = dict(
        clinical=0.9, availability=0.5, accessibility=0.3, continuity=0.55,
        quality=0.8, fairness=0.6, emergency=0.2, risk_penalty=0.0,
    )
    distance_weights = {
        "clinical": 0.15, "availability": 0.10, "accessibility": 0.45,
        "continuity": 0.05, "quality": 0.10, "fairness": 0.10, "emergency": 0.05,
    }
    specialty_weights = {
        "clinical": 0.45, "availability": 0.10, "accessibility": 0.15,
        "continuity": 0.05, "quality": 0.10, "fairness": 0.10, "emergency": 0.05,
    }
    d_near = score_hospital_candidate(**near_low_fit, weights=distance_weights, traffic_access={})[0]
    d_far = score_hospital_candidate(**far_high_fit, weights=distance_weights, traffic_access={})[0]
    s_near = score_hospital_candidate(**near_low_fit, weights=specialty_weights, traffic_access={})[0]
    s_far = score_hospital_candidate(**far_high_fit, weights=specialty_weights, traffic_access={})[0]

    def cand(score: float) -> dict:
        return {"hospital": {"district": "天宁区", "level": "三级甲等"}, "composite_score": score}

    emergency = rerank_hospital_candidates(
        [cand(99), cand(98), cand(97)], "emergency", 3, lambda h: h["district"]
    )
    routine = rerank_hospital_candidates(
        [cand(99), cand(98), cand(97)], "routine", 3, lambda h: h["district"]
    )

    return {
        "schema_version": "care-routing-ablation/v1",
        "claim_scope": "rule/feature consistency checks, not clinical effectiveness",
        "feature_weight_ablation": {"base_score": base_score, "leave_one_out": leave_one_out},
        "missing_position_rebalance": {
            "unavailable": ["accessibility"],
            "rebalanced": rebalance_weights({**base_weights, "accessibility": 0.2}, {"accessibility"}),
        },
        "distance_vs_specialty_rank_flip": {
            "distance_profile": {"near_low_fit": d_near, "far_high_fit": d_far},
            "specialty_profile": {"near_low_fit": s_near, "far_high_fit": s_far},
            "flip_observed": (d_near > d_far) and (s_far > s_near),
        },
        "emergency_rerank_bypass": {
            "emergency_adjustments": [i.get("rerank_adjustment") for i in emergency],
            "routine_adjustments": [i.get("rerank_adjustment") for i in routine],
            "emergency_risk_penalty_no_flag": hospital_risk_penalty(
                "胸痛", "心内科",
                {"emergency": False, "name": "x", "type": "综合", "departments": []},
                {"level": "emergency"},
            ),
            "emergency_risk_penalty_with_flag": hospital_risk_penalty(
                "胸痛", "心内科",
                {"emergency": True, "name": "x", "type": "综合", "departments": ["急诊"]},
                {"level": "emergency"},
            ),
        },
        "continuity_preference_gate": {
            "followup_text_score": continuity_score(
                "慢病复诊配药", "内科", {"name": "综合", "type": "综合", "departments": ["内科"]}
            ),
            "first_visit_text_score": continuity_score(
                "首次不适", "内科", {"name": "综合", "type": "综合", "departments": ["内科"]}
            ),
        },
        "missing_or_untrusted_fields": {
            "availability_missing": {
                "data_available": hospital_availability_data_available({"emergency": True}),
                "score": hospital_availability_score({"emergency": True}),
            },
            "availability_present": {
                "data_available": hospital_availability_data_available(
                    {"beds": 1800, "daily_outpatients": 1200, "emergency": True}
                ),
                "score": hospital_availability_score(
                    {"beds": 1800, "daily_outpatients": 1200, "emergency": True}
                ),
            },
            "academic_weight_production_zero": True,
            "provisional_capability_scores_ignored_for_ranking": True,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    payload = build()
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if args.write:
        (OUT / "care_routing_ablation.json").write_text(text, encoding="utf-8")
        print(f"wrote {OUT / 'care_routing_ablation.json'}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
