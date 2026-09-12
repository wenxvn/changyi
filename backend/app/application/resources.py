"""Build safe, read-only resource detail views for the versioned API."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any


HOSPITAL_PUBLIC_FIELDS = (
    "id",
    "name",
    "alias",
    "level",
    "type",
    "address",
    "district",
    "phone",
    "lat",
    "lng",
    "emergency",
    "departments",
    "derived_capability_areas",
)

HOSPITAL_BRIEF_FIELDS = (
    "id",
    "name",
    "alias",
    "level",
    "type",
    "address",
    "district",
    "phone",
    "lat",
    "lng",
    "emergency",
)

DOCTOR_PUBLIC_FIELDS = (
    "id",
    "name",
    "title",
    "position",
    "hospital_id",
    "hospital_name",
    "department",
    "specialties",
    "specialty",
    "outpatient_time",
    "photo_url",
    "photo_provenance_status",
    "source_image_url",
    "doctor_page_url",
)

LEGACY_TOP_DEPARTMENTS = (
    "心血管内科",
    "骨科",
    "肿瘤科",
    "神经内科",
    "消化内科",
)


DOCTOR_LIST_DEFAULT_PAGE_SIZE = 24
DOCTOR_LIST_MAX_PAGE_SIZE = 100


class DoctorListValidationError(ValueError):
    """Raised when doctor list query parameters are invalid."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def _doctor_search_blob(doctor: Mapping[str, Any]) -> str:
    specialties = doctor.get("specialties")
    if isinstance(specialties, (list, tuple, set)):
        specialty_text = " ".join(str(item) for item in specialties if item)
    else:
        specialty_text = str(specialties or "")
    return " ".join(
        str(doctor.get(field) or "")
        for field in ("name", "hospital_name", "department", "title", "position", "specialty")
    ) + " " + specialty_text


def _doctor_matches_filters(
    doctor: Mapping[str, Any],
    *,
    q: str | None,
    hospital_id: int | None,
    hospital_name: str | None,
    department: str | None,
    title: str | None,
) -> bool:
    if hospital_id is not None and doctor.get("hospital_id") != hospital_id:
        return False
    if hospital_name and doctor.get("hospital_name") != hospital_name:
        return False
    if department and doctor.get("department") != department:
        return False
    if title:
        doctor_title = doctor.get("title") or doctor.get("position") or ""
        if doctor_title != title:
            return False
    if q:
        needle = q.strip().lower()
        if needle and needle not in _doctor_search_blob(doctor).lower():
            return False
    return True


def _unique_sorted(values: Sequence[str | None]) -> list[str]:
    return sorted({value for value in values if isinstance(value, str) and value.strip()})


@dataclass(frozen=True)
class ResourceCatalogApplicationService:
    """Coordinate read-only catalog access without owning HTTP concerns."""

    hospitals: Callable[[], Sequence[Mapping[str, Any]]]
    real_doctors: Callable[[], Sequence[Mapping[str, Any]]]
    fallback_doctors: Callable[[], Sequence[Mapping[str, Any]]]

    def legacy_hospitals(self) -> dict[str, Any]:
        """Build the unchanged legacy hospital-list payload."""

        items = list(self.hospitals())
        return {"items": items, "count": len(items)}

    def legacy_hospital_detail(self, hospital_id: int) -> dict[str, Any] | None:
        """Build the unchanged legacy hospital detail payload."""

        hospital = next((item for item in self.hospitals() if item.get("id") == hospital_id), None)
        if hospital is None:
            return None
        doctors = [doctor for doctor in self.real_doctors() if doctor.get("hospital_id") == hospital_id]
        if not doctors:
            doctors = [doctor for doctor in self.fallback_doctors() if doctor.get("hospital_id") == hospital_id]
        source = "real" if any(doctor.get("hospital_id") == hospital_id for doctor in self.real_doctors()) else "mock"
        return {"hospital": hospital, "doctors": doctors, "source": source}

    def legacy_doctors(
        self,
        *,
        department: str | None = None,
        hospital_id: int | None = None,
        use_real: bool = True,
    ) -> dict[str, Any]:
        """Build the unchanged legacy doctor index payload."""

        doctors = list(self.real_doctors() if use_real else self.fallback_doctors())
        if not doctors:
            doctors = list(self.fallback_doctors())
        if department:
            doctors = [doctor for doctor in doctors if doctor.get("department") == department]
        if hospital_id:
            doctors = [doctor for doctor in doctors if doctor.get("hospital_id") == hospital_id]
        return {
            "items": doctors,
            "count": len(doctors),
            "source": "real" if use_real else "mock",
        }

    def legacy_doctor_detail(self, doctor_id: int) -> dict[str, Any] | None:
        """Build the original doctor detail response (fallback catalog only)."""

        doctor = next((item for item in self.fallback_doctors() if item.get("id") == doctor_id), None)
        if doctor is None:
            return None
        hospital = next((item for item in self.hospitals() if item.get("id") == doctor.get("hospital_id")), None)
        return {"doctor": doctor, "hospital": hospital}

    def legacy_hospital_doctors(self, hospital_id: int) -> dict[str, Any]:
        """Build the original hospital-doctor relation response."""

        doctors = [doctor for doctor in self.real_doctors() if doctor.get("hospital_id") == hospital_id]
        if not doctors:
            doctors = [doctor for doctor in self.fallback_doctors() if doctor.get("hospital_id") == hospital_id]
        hospital = next((item for item in self.hospitals() if item.get("id") == hospital_id), None)
        return {
            "hospital": hospital,
            "doctors": doctors,
            "count": len(doctors),
            "source": "real" if any(doctor.get("id", 0) >= 1000 for doctor in doctors) else "mock",
        }

    def legacy_departments(self) -> list[str]:
        """Return the original sorted hospital department index."""

        departments = {
            department
            for hospital in self.hospitals()
            for department in hospital.get("departments", [])
        }
        return sorted(departments)

    @staticmethod
    def legacy_districts(locations: Mapping[str, Any]) -> list[str]:
        """Return region names in the original mapping order."""

        return list(locations)

    def legacy_stats(self) -> dict[str, Any]:
        """Return the original catalog statistics read model."""

        hospitals = list(self.hospitals())
        real_doctors = list(self.real_doctors())
        fallback_doctors = list(self.fallback_doctors())
        return {
            "total_hospitals": len(hospitals),
            "total_doctors": len(real_doctors) if real_doctors else len(fallback_doctors),
            "total_real_doctors": len(real_doctors),
            "total_mock_doctors": len(fallback_doctors),
            "total_beds": (
                sum(hospital["beds"] for hospital in hospitals)
                if hospitals and all(isinstance(hospital.get("beds"), (int, float)) for hospital in hospitals)
                else None
            ),
            "daily_outpatients_total": (
                sum(hospital["daily_outpatients"] for hospital in hospitals)
                if hospitals and all(isinstance(hospital.get("daily_outpatients"), (int, float)) for hospital in hospitals)
                else None
            ),
            "top_departments": list(LEGACY_TOP_DEPARTMENTS),
        }

    def legacy_enhanced_doctor_detail(self, doctor_id: int) -> dict[str, Any] | None:
        """Build the original enhanced doctor detail response."""

        doctor = next((item for item in self.real_doctors() if item.get("id") == doctor_id), None)
        if doctor is not None:
            return doctor
        doctor = next((item for item in self.fallback_doctors() if item.get("id") == doctor_id), None)
        if doctor is None:
            return None
        hospital = next((item for item in self.hospitals() if item.get("id") == doctor.get("hospital_id")), None)
        return {"doctor": doctor, "hospital": hospital}

    def list_hospitals(self) -> dict[str, Any]:
        items = list(self.hospitals())
        return {
            "items": items,
            "count": len(items),
            "source": "legacy_catalog_pending_provenance",
            "provenance": {
                "status": "provisional",
                "source_class": "legacy_catalog_import",
                "last_updated": None,
                "license_status": "not_recorded",
            },
        }

    def list_doctors(
        self,
        *,
        hospital_id: int | None = None,
        q: str | None = None,
        hospital_name: str | None = None,
        department: str | None = None,
        title: str | None = None,
        page: int = 1,
        page_size: int = DOCTOR_LIST_DEFAULT_PAGE_SIZE,
    ) -> dict[str, Any]:
        """Return a filtered, paginated doctor list without loading all rows to the client."""

        if page < 1:
            raise DoctorListValidationError("INVALID_PAGE", "page 必须 >= 1")
        if page_size < 1 or page_size > DOCTOR_LIST_MAX_PAGE_SIZE:
            raise DoctorListValidationError(
                "INVALID_PAGE_SIZE",
                f"page_size 必须在 1–{DOCTOR_LIST_MAX_PAGE_SIZE} 之间",
            )

        rows = list(self.real_doctors())
        filtered = [
            row
            for row in rows
            if _doctor_matches_filters(
                row,
                q=q,
                hospital_id=hospital_id,
                hospital_name=hospital_name,
                department=department,
                title=title,
            )
        ]
        total = len(filtered)
        start = (page - 1) * page_size
        end = start + page_size
        items = filtered[start:end]
        return {
            "items": items,
            "page": page,
            "page_size": page_size,
            "total": total,
            "count": total,
            "has_more": end < total,
            "source": "public_source_mixed",
            "filters": {
                "q": q or None,
                "hospital_id": hospital_id,
                "hospital_name": hospital_name or None,
                "department": department or None,
                "title": title or None,
            },
            "facets": {
                "hospital_names": _unique_sorted([row.get("hospital_name") for row in rows]),
                "departments": _unique_sorted([row.get("department") for row in rows]),
                "titles": _unique_sorted(
                    [(row.get("title") or row.get("position")) for row in rows]
                ),
            },
        }

    def hospital_detail(self, hospital_id: int) -> dict[str, Any] | None:
        hospital = next((item for item in self.hospitals() if item.get("id") == hospital_id), None)
        if hospital is None:
            return None
        doctors = [doctor for doctor in self.real_doctors() if doctor.get("hospital_id") == hospital_id]
        if not doctors:
            doctors = [doctor for doctor in self.fallback_doctors() if doctor.get("hospital_id") == hospital_id]
        return build_hospital_detail(hospital, doctors=doctors)

    def doctor_detail(self, doctor_id: int) -> dict[str, Any] | None:
        doctor = next((item for item in self.real_doctors() if item.get("id") == doctor_id), None)
        source_class = "public_source_mixed"
        if doctor is None:
            doctor = next((item for item in self.fallback_doctors() if item.get("id") == doctor_id), None)
            source_class = "legacy_mock_catalog"
        if doctor is None:
            return None
        hospital = next((item for item in self.hospitals() if item.get("id") == doctor.get("hospital_id")), None)
        return build_doctor_detail(doctor, hospital=hospital, source_class=source_class)


def _public_record(source: Mapping[str, Any], fields: tuple[str, ...]) -> dict[str, Any]:
    return {field: source[field] for field in fields if field in source}


def _provenance(
    source_class: str,
    status: str,
    notice: str,
    *,
    catalog_status: str | None = None,
    field_level_status: str = "not_available",
) -> dict[str, Any]:
    return {
        "source_class": source_class,
        "status": status,
        "catalog_status": catalog_status or status,
        "last_updated": None,
        "license_status": "not_recorded",
        "field_level_status": field_level_status,
        "unsupported_fields": ["beds", "daily_outpatients", "rating", "description"],
        "notice": notice,
    }


def build_hospital_detail(
    hospital: Mapping[str, Any],
    *,
    doctor_count: int | None = None,
    doctors: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Return only fields approved for the public hospital detail boundary."""

    related_doctors = list(doctors or ())
    if doctor_count is None:
        doctor_count = len(related_doctors)
    derived_scores = hospital.get("derived_capability_scores") or {}
    return {
        "resource_type": "hospital",
        "resource": _public_record(hospital, HOSPITAL_PUBLIC_FIELDS),
        "source": "legacy_catalog_pending_provenance",
        "provenance": _provenance(
            "legacy_catalog_pending_provenance",
            "migration_pending",
            "医院目录已从应用代码迁移到 Region Pack，但逐字段来源、许可和更新时间尚未完成登记；资料仅用于演示展示。",
            catalog_status="provisional",
            field_level_status="public_facts_and_derived_features",
        ),
        "derived_capability": {
            "areas": list(hospital.get("derived_capability_areas") or []),
            "scores": dict(derived_scores),
            "status": "provisional",
            "formula_version": "legacy-strength-score-v1",
            "notice": "派生能力线索仅供匹配解释，不代表官方评级、疗效或临床质量结论。",
        },
        "related": {
            "doctor_count": doctor_count,
            "doctors": [_public_record(doctor, DOCTOR_PUBLIC_FIELDS) for doctor in related_doctors],
        },
    }


def build_doctor_detail(
    doctor: Mapping[str, Any],
    *,
    hospital: Mapping[str, Any] | None,
    source_class: str,
) -> dict[str, Any]:
    """Return public doctor fields and a minimal related hospital brief."""

    return {
        "resource_type": "doctor",
        "resource": _public_record(doctor, DOCTOR_PUBLIC_FIELDS),
        "source": source_class,
        "provenance": _provenance(
            source_class,
            "available" if source_class == "public_source_mixed" else "fallback",
            "公开资料索引不等于临床适配、疗效证明或官方推荐；完整出处和更新时间仍需后续登记。",
        ),
        "related": {
            "hospital": _public_record(hospital, HOSPITAL_BRIEF_FIELDS) if hospital else None,
        },
    }
