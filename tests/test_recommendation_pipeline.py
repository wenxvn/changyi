from __future__ import annotations

from unittest import TestCase

from backend.app.domain.recommendation.pipeline import rerank_hospital_candidates


def _district(hospital):
    return hospital["district"]


def _candidate(score, district, level="二级"):
    return {
        "hospital": {"district": district, "level": level},
        "composite_score": score,
    }


class RecommendationPipelineTests(TestCase):
    def test_routine_applies_district_and_tertiary_adjustments(self):
        candidates = [
            _candidate(99, "天宁区", "三级甲等"),
            _candidate(98, "天宁区", "三级甲等"),
            _candidate(97, "天宁区", "三级甲等"),
            _candidate(96, "武进区", "二级"),
        ]
        selected = rerank_hospital_candidates(candidates, "routine", 4, _district)
        self.assertEqual(selected[0]["composite_score"], 99)
        self.assertEqual(selected[1]["composite_score"], 98)
        self.assertEqual(selected[2]["rerank_adjustment"], 0.0)
        self.assertEqual(selected[3]["rerank_adjustment"], -3.5)

    def test_urgent_uses_district_diversity_but_not_tertiary_cap(self):
        candidates = [
            _candidate(99, "天宁区", "三级甲等"),
            _candidate(98, "天宁区", "三级甲等"),
            _candidate(97, "天宁区", "三级甲等"),
        ]
        selected = rerank_hospital_candidates(candidates, "urgent", 3, _district)
        self.assertEqual(selected[2]["rerank_adjustment"], -1.5)

    def test_emergency_bypasses_diversity_constraints(self):
        candidates = [
            _candidate(99, "天宁区", "三级甲等"),
            _candidate(98, "天宁区", "三级甲等"),
            _candidate(97, "天宁区", "三级甲等"),
        ]
        selected = rerank_hospital_candidates(candidates, "emergency", 3, _district)
        self.assertEqual([item["composite_score"] for item in selected], [99, 98, 97])
        self.assertEqual([item["rerank_adjustment"] for item in selected], [0.0, 0.0, 0.0])
