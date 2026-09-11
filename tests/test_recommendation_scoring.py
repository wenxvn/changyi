from __future__ import annotations

from unittest import TestCase

from backend.app.domain.recommendation.scoring import (
    as_text,
    clamp,
    departments_related,
    doctor_resource_tier,
    doctor_title_score,
    score_hospital_candidate,
    score_doctor_candidate,
)


class RecommendationScoringTests(TestCase):
    def test_clamp_and_text_helpers_keep_legacy_boundaries(self):
        self.assertEqual(clamp(-1), 0.0)
        self.assertEqual(clamp(2), 1.0)
        self.assertEqual(clamp(5, 1, 3), 3)
        self.assertEqual(as_text(["心内", "", "呼吸"]), "心内 呼吸")
        self.assertEqual(as_text("胸痛"), "胸痛")
        self.assertEqual(as_text(None), "")

    def test_department_family_matching_handles_positive_and_negative_cases(self):
        self.assertTrue(departments_related("呼吸与危重症医学科", "呼吸内科"))
        self.assertTrue(departments_related("中医科", "针灸推拿科"))
        self.assertFalse(departments_related("心血管内科", "骨科"))
        self.assertFalse(departments_related("", "骨科"))

    def test_doctor_title_scores_preserve_ordering(self):
        self.assertGreater(
            doctor_title_score({"title": "主任医师"}),
            doctor_title_score({"title": "副主任医师"}),
        )
        self.assertGreater(
            doctor_title_score({"title": "主治医师"}),
            doctor_title_score({"title": "医师"}),
        )

    def test_resource_tier_is_internal_and_uses_hospital_context(self):
        tier = doctor_resource_tier(
            {"title": "主任医师", "national_funding": True, "sci_papers": 25},
            {"level": "三级甲等"},
            specialty_score=0.9,
            academic_score=0.8,
            surgery_score=0.7,
        )
        self.assertEqual(tier, "top_expert")
        self.assertEqual(
            doctor_resource_tier({}, None, 0.1, 0.1, 0.1),
            "general",
        )

    def test_resource_tier_does_not_promote_on_academic_only(self):
        academic_only = doctor_resource_tier(
            {"title": "主治医师", "national_funding": True, "sci_papers": 30},
            {"level": "三级甲等"},
            specialty_score=0.55,
            academic_score=0.95,
            surgery_score=0.2,
        )
        self.assertEqual(academic_only, "specialist")

    def test_hospital_score_combines_weights_and_risk_penalty(self):
        score, features = score_hospital_candidate(
            clinical=1.0,
            availability=1.0,
            accessibility=1.0,
            continuity=1.0,
            quality=1.0,
            fairness=1.0,
            emergency=1.0,
            risk_penalty=0.1,
            weights={
                "clinical": 0.4,
                "availability": 0.2,
                "accessibility": 0.2,
                "continuity": 0.1,
                "quality": 0.05,
                "fairness": 0.04,
                "emergency": 0.01,
            },
            traffic_access={"used_in_ranking": True},
        )
        self.assertEqual(score, 90.0)
        self.assertEqual(features["risk_penalty"], 0.1)
        self.assertEqual(features["traffic_access"], {"used_in_ranking": True})

    def test_hospital_score_clamps_out_of_range_composite(self):
        score, features = score_hospital_candidate(
            clinical=2.0,
            availability=2.0,
            accessibility=2.0,
            continuity=2.0,
            quality=2.0,
            fairness=2.0,
            emergency=2.0,
            risk_penalty=-1.0,
            weights={key: 1.0 for key in (
                "clinical", "availability", "accessibility", "continuity",
                "quality", "fairness", "emergency",
            )},
            traffic_access={},
        )
        self.assertEqual(score, 100.0)
        self.assertEqual(features["clinical"], 2.0)

    def test_hospital_score_preserves_low_score_floor(self):
        score, _ = score_hospital_candidate(
            clinical=0.0,
            availability=0.0,
            accessibility=0.0,
            continuity=0.0,
            quality=0.0,
            fairness=0.0,
            emergency=0.0,
            risk_penalty=0.8,
            weights={key: 0.1 for key in (
                "clinical", "availability", "accessibility", "continuity",
                "quality", "fairness", "emergency",
            )},
            traffic_access={},
        )
        self.assertEqual(score, 0.0)

    def test_doctor_score_combines_base_and_extra_features(self):
        score = score_doctor_candidate(
            surgery_score=1.0,
            specialty_score=0.4,
            academic_score=1.0,
            title_score=1.0,
            hospital_score=1.0,
            access_score=1.0,
            availability_score=1.0,
            continuity_score=1.0,
            fairness_score=1.0,
            risk_penalty=0.1,
            weights={key: 1 / 6 for key in ("surgery", "specialty", "academic", "title", "hospital", "access")},
            extra_weights={"availability": 0.05, "continuity": 0.03, "fairness": 0.02},
        )
        self.assertAlmostEqual(score, 0.81)

    def test_doctor_score_applies_specialty_boost_only_above_threshold(self):
        common = {
            "surgery_score": 0.5,
            "academic_score": 0.5,
            "title_score": 0.5,
            "hospital_score": 0.5,
            "access_score": 0.5,
            "availability_score": 0.5,
            "continuity_score": 0.5,
            "fairness_score": 0.5,
            "risk_penalty": 0.0,
            "weights": {key: 1 / 6 for key in ("surgery", "specialty", "academic", "title", "hospital", "access")},
            "extra_weights": {"availability": 0.05, "continuity": 0.03, "fairness": 0.02},
        }
        boosted = score_doctor_candidate(specialty_score=0.6, **common)
        unboosted = score_doctor_candidate(specialty_score=0.5, **common)
        self.assertGreater(boosted, unboosted)

    def test_doctor_score_clamps_after_risk_penalty(self):
        score = score_doctor_candidate(
            surgery_score=0.0,
            specialty_score=0.0,
            academic_score=0.0,
            title_score=0.0,
            hospital_score=0.0,
            access_score=0.0,
            availability_score=0.0,
            continuity_score=0.0,
            fairness_score=0.0,
            risk_penalty=1.0,
            weights={key: 1 / 6 for key in ("surgery", "specialty", "academic", "title", "hospital", "access")},
            extra_weights={"availability": 0.05, "continuity": 0.03, "fairness": 0.02},
        )
        self.assertEqual(score, 0.0)
