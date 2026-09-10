"""Build safe, read-only resource detail views for the versioned API."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


HOSPITAL_PUBLIC_FIELDS = (
    "id",
    "name",
    "alias",
    "level",
    "type",
    "address",
    "phone",
    "description",
    "lat",
    "lng",
    "emergency",
    "departments",
    "strengths",
)

HOSPITAL_BRIEF_FIELDS = (
    "id",
    "name",
    "alias",
    "level",
    "type",
    "address",
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
)


def _public_record(source: Mapping[str, Any], fields: tuple[str, ...]) -> dict[str, Any]:
    return {field: source[field] for field in fields if field in source}


def _provenance(source_class: str, status: str, notice: str) -> dict[str, Any]:
    return {
        "source_class": source_class,
        "status": status,
        "last_updated": None,
        "license_status": "not_recorded",
        "field_level_status": "not_available",
        "notice": notice,
    }


def build_hospital_detail(hospital: Mapping[str, Any], *, doctor_count: int) -> dict[str, Any]:
    """Return only fields approved for the public hospital detail boundary."""

    return {
        "resource_type": "hospital",
        "resource": _public_record(hospital, HOSPITAL_PUBLIC_FIELDS),
        "source": "legacy_catalog_pending_provenance",
        "provenance": _provenance(
            "legacy_catalog_pending_provenance",
            "migration_pending",
            "医院目录逐字段来源、许可和更新时间尚未完成登记；资料仅用于演示展示。",
        ),
        "related": {"doctor_count": doctor_count},
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
