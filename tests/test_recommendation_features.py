from __future__ import annotations

from unittest import TestCase

from backend.app.domain.recommendation.features import (
    continuity_score,
    fairness_score,
    hospital_availability_score,
    hospital_quality_score,
    hospital_recommend_reasons,
    hospital_risk_penalty,
    hospital_strength_for_department,
    special_population_fit,
)


class RecommendationFeatureTests(TestCase):
    def test_strength_uses_public_department_facts_not_provisional_scores(self):
        hospital = {
            "level": "三级甲等",
            "rating": 4.8,
            "derived_capability_scores": {"心血管内科": 96},
            "strength_scores": {"心血管内科": 95},
            "departments": ["呼吸与危重症医学科"],
        }
        exact = {**hospital, "departments": ["心血管内科"]}
        self.assertEqual(hospital_strength_for_department(exact, "心血管内科"), 0.82)
        self.assertEqual(hospital_strength_for_department(hospital, "呼吸"), 0.72)
        self.assertEqual(hospital_strength_for_department(hospital, "眼科"), 0.5)
        self.assertGreater(hospital_quality_score(hospital), hospital_quality_score({"level": "二级", "rating": 3.5}))

    def test_availability_prefers_capacity_and_emergency_capability(self):
        capable = {"beds": 1800, "daily_outpatients": 1800, "emergency": True}
        limited = {"beds": 100, "daily_outpatients": 1600, "emergency": False}
        self.assertGreater(
            hospital_availability_score(capable, "emergency"),
            hospital_availability_score(limited, "emergency"),
        )

    def test_special_population_and_continuity_scores_have_safe_fallbacks(self):
        child_hospital = {"name": "常州市儿童医院", "type": "专科医院", "departments": []}
        general_hospital = {"name": "常州市综合医院", "type": "综合医院", "departments": []}
        self.assertGreater(
            special_population_fit("儿童发热", child_hospital),
            special_population_fit("儿童发热", general_hospital),
        )
        self.assertGreater(
            continuity_score("慢病复诊", "内科", general_hospital),
            continuity_score("首次不适", "内科", general_hospital),
        )

    def test_risk_and_explanation_preserve_priority_and_length_limit(self):
        hospital = {
            "name": "常州市综合医院",
            "level": "三级甲等",
            "type": "综合医院",
            "emergency": False,
            "departments": [],
        }
        emergency_hospital = {**hospital, "emergency": True}
        self.assertGreater(
            hospital_risk_penalty("胸痛", "心内科", hospital, {"level": "emergency"}),
            hospital_risk_penalty("胸痛", "心内科", emergency_hospital, {"level": "emergency"}),
        )
        reasons = hospital_recommend_reasons(
            emergency_hospital,
            {
                "clinical": 0.9,
                "quality": 0.9,
                "availability": 0.8,
                "fairness": 0.8,
                "traffic_access": {"public_transport_score": 0.9},
            },
            3.0,
            "心内科",
            "emergency",
        )
        self.assertLessEqual(len(reasons), 4)
        self.assertIn("按公开科室资料综合匹配", reasons)
        self.assertTrue(any("急诊字段" in item for item in reasons))
