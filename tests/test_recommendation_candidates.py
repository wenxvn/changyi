from __future__ import annotations

from unittest import TestCase

from backend.app.domain.recommendation.candidates import (
    build_doctor_query_terms,
    doctor_matches_candidate,
    hospital_supports_emergency_fallback,
    resolve_hospital_candidate_match,
)


class RecommendationCandidateFilterTests(TestCase):
    def test_query_terms_merge_text_mapping_and_triage_summary(self):
        terms = build_doctor_query_terms(
            "胸痛、头晕",
            {"胸痛": "心血管内科", "咳嗽": "呼吸内科"},
            {
                "symptom_tags": [{"tag": "心血管信号", "matched_terms": ["心口疼"]}],
                "disease_candidates": [{"name": "心绞痛", "primary_category": "心血管", "secondary_category": "急症风险"}],
            },
        )
        self.assertTrue({"胸痛", "头晕", "心血管信号", "心口疼", "心绞痛", "心血管", "急症风险"}.issubset(terms))

    def test_department_filter_keeps_related_positive_and_unrelated_negative(self):
        doctor = {"department": "呼吸与危重症医学科", "keywords": []}
        self.assertTrue(doctor_matches_candidate(doctor, "呼吸内科", set()))
        self.assertFalse(doctor_matches_candidate(doctor, "骨科", set()))

    def test_keyword_fallback_matches_keywords_or_department(self):
        doctor = {"department": "心血管内科", "keywords": ["胸痛", "冠心病"]}
        self.assertTrue(doctor_matches_candidate(doctor, None, {"胸痛"}))
        self.assertTrue(doctor_matches_candidate(doctor, None, {"心血管"}))
        self.assertFalse(doctor_matches_candidate(doctor, None, {"皮疹"}))

    def test_hospital_match_prefers_explicit_strength_score(self):
        hospital = {"strength_scores": {"心血管内科": 88}, "departments": ["心血管内科"]}
        self.assertEqual(resolve_hospital_candidate_match(hospital, "心血管内科"), (88, "心血管内科"))

    def test_hospital_match_keeps_department_and_related_fallbacks(self):
        listed = {"strength_scores": {}, "departments": ["骨科"]}
        related = {"strength_scores": {}, "departments": ["呼吸与危重症医学科"]}
        missing = {"strength_scores": {}, "departments": ["眼科"]}
        self.assertEqual(resolve_hospital_candidate_match(listed, "骨科"), (75, "骨科"))
        self.assertEqual(resolve_hospital_candidate_match(related, "呼吸内科"), (70, "呼吸与危重症医学科"))
        self.assertEqual(resolve_hospital_candidate_match(missing, "心血管内科"), (50, "心血管内科"))

    def test_hospital_match_without_target_department_is_neutral(self):
        self.assertEqual(
            resolve_hospital_candidate_match({"strength_scores": {}, "departments": ["骨科"]}, None),
            (50, None),
        )

    def test_emergency_fallback_requires_emergency_hospital_flag(self):
        self.assertTrue(hospital_supports_emergency_fallback({"emergency": True}))
        self.assertFalse(hospital_supports_emergency_fallback({"emergency": False}))
        self.assertFalse(hospital_supports_emergency_fallback({}))
        self.assertFalse(hospital_supports_emergency_fallback(None))
