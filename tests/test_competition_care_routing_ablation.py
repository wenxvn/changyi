"""Care-routing multi-objective behavior checks (rule consistency, not clinical effect)."""

from __future__ import annotations

from unittest import TestCase

from backend.app.domain.recommendation.features import (
    hospital_availability_data_available,
    hospital_availability_score,
    hospital_risk_penalty,
    continuity_score,
)
from backend.app.domain.recommendation.pipeline import rerank_hospital_candidates
from backend.app.domain.recommendation.scoring import rebalance_weights, score_hospital_candidate


class CareRoutingAblationTests(TestCase):
    def test_leave_one_feature_weight_changes_composite_in_expected_direction(self):
        weights = {
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
        base = score_hospital_candidate(**feats, weights=weights, traffic_access={})[0]
        without_clinical = dict(weights)
        without_clinical["clinical"] = 0.0
        total = sum(without_clinical.values()) or 1.0
        without_clinical = {k: v / total for k, v in without_clinical.items()}
        dropped = score_hospital_candidate(**feats, weights=without_clinical, traffic_access={})[0]
        self.assertLess(dropped, base)

    def test_missing_location_rebalances_and_zeroes_unavailable_weight(self):
        rebalanced = rebalance_weights(
            {"clinical": 0.4, "availability": 0.2, "accessibility": 0.2, "quality": 0.2},
            {"accessibility"},
        )
        self.assertEqual(rebalanced["accessibility"], 0.0)
        self.assertAlmostEqual(sum(rebalanced.values()), 1.0, places=6)

    def test_distance_preference_vs_specialty_preference_flip_ranking(self):
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
        self.assertGreater(d_near, d_far)
        self.assertGreater(s_far, s_near)

    def test_emergency_bypasses_routine_diversity_rerank_and_penalizes_missing_emergency(self):
        candidates = [
            {"hospital": {"district": "天宁区", "level": "三级甲等"}, "composite_score": 99},
            {"hospital": {"district": "天宁区", "level": "三级甲等"}, "composite_score": 98},
            {"hospital": {"district": "天宁区", "level": "三级甲等"}, "composite_score": 97},
        ]
        emergency = rerank_hospital_candidates(
            [dict(item) for item in candidates], "emergency", 3, lambda h: h["district"]
        )
        routine = rerank_hospital_candidates(
            [dict(item) for item in candidates], "routine", 3, lambda h: h["district"]
        )
        self.assertTrue(all(item["rerank_adjustment"] in (0, 0.0) for item in emergency))
        self.assertTrue(any(item["rerank_adjustment"] < 0 for item in routine))

        no_flag = hospital_risk_penalty(
            "胸痛", "心内科", {"emergency": False, "name": "x", "type": "综合", "departments": []}, {"level": "emergency"}
        )
        with_flag = hospital_risk_penalty(
            "胸痛", "心内科", {"emergency": True, "name": "x", "type": "综合", "departments": ["急诊"]}, {"level": "emergency"}
        )
        self.assertGreater(no_flag, with_flag)

    def test_continuity_language_required_and_missing_capacity_never_scores_high(self):
        self.assertGreater(
            continuity_score("慢病复诊配药", "内科", {"name": "综合", "type": "综合", "departments": ["内科"]}),
            continuity_score("首次不适", "内科", {"name": "综合", "type": "综合", "departments": ["内科"]}),
        )
        self.assertFalse(hospital_availability_data_available({"emergency": True}))
        self.assertEqual(hospital_availability_score({"emergency": True}), 0.0)
        self.assertTrue(
            hospital_availability_data_available({"beds": 1800, "daily_outpatients": 1200})
        )
