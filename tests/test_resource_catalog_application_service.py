from __future__ import annotations

from unittest import TestCase

from backend.app.application.resources import (
    DoctorListValidationError,
    ResourceCatalogApplicationService,
)


class ResourceCatalogApplicationServiceTests(TestCase):
    def make_service(self) -> ResourceCatalogApplicationService:
        hospitals = [
            {
                "id": 1,
                "name": "示例医院",
                "level": "三级甲等",
                "type": "综合医院",
                "address": "示例地址",
                "beds": 999,
                "daily_outpatients": 0,
                "departments": ["内科", "外科"],
            },
        ]
        real_doctors = [
            {
                "id": 1001,
                "name": "公开医生",
                "hospital_id": 1,
                "hospital_name": "示例医院",
                "department": "内科",
                "title": "主任医师",
            },
        ]
        fallback_doctors = [
            {
                "id": 7,
                "name": "兼容医生",
                "hospital_id": 1,
                "hospital_name": "示例医院",
                "department": "外科",
                "title": "医师",
            },
        ]
        return ResourceCatalogApplicationService(
            hospitals=lambda: hospitals,
            real_doctors=lambda: real_doctors,
            fallback_doctors=lambda: fallback_doctors,
        )

    def test_lists_keep_source_markers_and_filter_real_doctors(self):
        service = self.make_service()

        hospitals = service.list_hospitals()
        doctors = service.list_doctors(hospital_id=1)

        self.assertEqual(hospitals["count"], 1)
        self.assertEqual(hospitals["source"], "legacy_catalog_pending_provenance")
        self.assertEqual(doctors["items"][0]["id"], 1001)
        self.assertEqual(doctors["source"], "public_source_mixed")
        self.assertEqual(doctors["page"], 1)
        self.assertEqual(doctors["page_size"], 24)
        self.assertEqual(doctors["total"], doctors["count"])
        self.assertFalse(doctors["has_more"])
        self.assertIn("facets", doctors)

    def test_doctor_list_supports_server_side_filters_and_pagination(self):
        doctors = [
            {
                "id": 1000 + index,
                "name": f"医生{index}",
                "hospital_id": 1 if index < 3 else 2,
                "hospital_name": "示例医院" if index < 3 else "另一家医院",
                "department": "内科" if index % 2 == 0 else "外科",
                "title": "主任医师" if index % 2 == 0 else "主治医师",
                "specialty": "高血压" if index == 0 else "关节",
            }
            for index in range(5)
        ]
        service = ResourceCatalogApplicationService(
            hospitals=lambda: [],
            real_doctors=lambda: doctors,
            fallback_doctors=lambda: [],
        )

        page1 = service.list_doctors(page=1, page_size=2)
        page2 = service.list_doctors(page=2, page_size=2)
        page3 = service.list_doctors(page=3, page_size=2)
        filtered = service.list_doctors(q="高血压", department="内科", page=1, page_size=10)
        by_hospital_name = service.list_doctors(hospital_name="另一家医院")
        by_title = service.list_doctors(title="主任医师")

        self.assertEqual(page1["total"], 5)
        self.assertEqual(len(page1["items"]), 2)
        self.assertTrue(page1["has_more"])
        self.assertEqual([item["id"] for item in page2["items"]], [1002, 1003])
        self.assertEqual(len(page3["items"]), 1)
        self.assertFalse(page3["has_more"])
        self.assertEqual(filtered["total"], 1)
        self.assertEqual(filtered["items"][0]["id"], 1000)
        self.assertEqual(by_hospital_name["total"], 2)
        self.assertEqual(by_title["total"], 3)
        self.assertIn("示例医院", page1["facets"]["hospital_names"])

    def test_doctor_list_rejects_invalid_pagination(self):
        service = self.make_service()

        with self.assertRaises(DoctorListValidationError) as page_error:
            service.list_doctors(page=0)
        self.assertEqual(page_error.exception.code, "INVALID_PAGE")

        with self.assertRaises(DoctorListValidationError) as size_error:
            service.list_doctors(page_size=101)
        self.assertEqual(size_error.exception.code, "INVALID_PAGE_SIZE")

    def test_details_apply_public_projection_and_compat_fallback(self):
        service = self.make_service()

        hospital = service.hospital_detail(1)
        doctor = service.doctor_detail(7)

        self.assertNotIn("beds", hospital["resource"])
        self.assertEqual(hospital["related"]["doctor_count"], 1)
        self.assertEqual(doctor["provenance"]["source_class"], "legacy_mock_catalog")
        self.assertEqual(doctor["related"]["hospital"]["name"], "示例医院")
        self.assertIsNone(service.hospital_detail(999))
        self.assertIsNone(service.doctor_detail(999))

    def test_legacy_catalog_payloads_preserve_selection_rules(self):
        service = self.make_service()

        hospitals = service.legacy_hospitals()
        doctors = service.legacy_doctors(department="外科", use_real=False)
        hospital = service.legacy_hospital_detail(1)
        doctor = service.legacy_doctor_detail(7)
        relation = service.legacy_hospital_doctors(1)
        enhanced = service.legacy_enhanced_doctor_detail(1001)

        self.assertEqual(hospitals["count"], 1)
        self.assertEqual(doctors["items"][0]["id"], 7)
        self.assertEqual(doctors["source"], "mock")
        self.assertEqual(hospital["source"], "real")
        self.assertEqual(doctor["doctor"]["id"], 7)
        self.assertEqual(relation["source"], "real")
        self.assertEqual(enhanced["id"], 1001)

    def test_legacy_catalog_indexes_and_stats_remain_derived_from_suppliers(self):
        service = self.make_service()

        self.assertEqual(service.legacy_departments(), ["内科", "外科"])
        self.assertEqual(service.legacy_districts({"甲": (1, 2), "乙": (3, 4)}), ["甲", "乙"])
        self.assertEqual(service.legacy_stats(), {
            "total_hospitals": 1,
            "total_doctors": 1,
            "total_real_doctors": 1,
            "total_mock_doctors": 1,
            "total_beds": 999,
            "daily_outpatients_total": 0,
            "top_departments": ["心血管内科", "骨科", "肿瘤科", "神经内科", "消化内科"],
        })
