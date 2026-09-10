"""Pure doctor resource policy helpers.

These helpers preserve the legacy visit-strategy, resource-fit and mismatch
penalty semantics.  They receive all triage and resource facts explicitly so
the policy can be tested without Flask, repositories, models, or global data.
"""

from __future__ import annotations

from typing import Any

from .scoring import clamp


def resource_strategy(triage: dict[str, Any] | None, expert_preference: str | None) -> dict[str, Any]:
    triage = triage or {}
    level = triage.get("level", "routine")
    preference = expert_preference or "system"
    if level == "emergency":
        return {
            "code": "emergency_fast_track",
            "title": "急症优先",
            "visit_path": "急诊优先",
            "expert_preference": preference,
            "expert_enabled": False,
            "top_expert_allowed": True,
            "notice": "当前命中急症红旗，系统不按专家号偏好排序，优先推荐最近急诊能力与120处置。",
        }
    if level == "urgent":
        is_specialty_followup = triage.get("severity_bucket") == "专科病情/需评估" or triage.get("matched_rule") in ("心血管专科病情", "慢病专科随访")
        return {
            "code": "specialty_followup" if is_specialty_followup else "specialty_priority",
            "title": "专科病情 · 专科门诊优先" if is_specialty_followup else "中重症专科优先",
            "visit_path": "专科门诊/必要时专家号" if is_specialty_followup else "专科门诊/专家号",
            "expert_preference": preference,
            "expert_enabled": preference not in ("no_expert",),
            "top_expert_allowed": preference in ("must_expert", "named_followup"),
            "notice": "当前属于明确专科病情，系统提高专科匹配、医院专科能力和连续照护权重；若出现急症红旗请优先急诊。" if is_specialty_followup else "当前病情建议尽快就医，系统提高专科匹配和医院专科能力权重。",
        }
    if preference == "must_expert":
        return {
            "code": "routine_must_expert",
            "title": "普通病症 · 专家号优先",
            "visit_path": "专家号",
            "expert_preference": preference,
            "expert_enabled": True,
            "top_expert_allowed": True,
            "notice": "当前病情倾向普通病症，系统尊重专家号选择，但不建议优先占用顶级专家资源。",
        }
    if preference in ("wish_expert", "named_followup"):
        return {
            "code": "routine_soft_expert",
            "title": "普通病症 · 专家号适度加权",
            "visit_path": "专科门诊/专家号",
            "expert_preference": preference,
            "expert_enabled": True,
            "top_expert_allowed": False,
            "notice": "当前病情倾向普通病症，系统优先推荐科室匹配、距离合适的门诊资源，专家号仅适度加权。",
        }
    return {
        "code": "routine_outpatient",
        "title": "普通病症 · 普通门诊优先",
        "visit_path": "普通门诊",
        "expert_preference": preference,
        "expert_enabled": False,
        "top_expert_allowed": False,
        "notice": "当前病情未触发重症/急症信号，系统降低顶级专家资源占用权重，优先考虑科室匹配、距离和可及门诊资源。",
    }


def apply_resource_fit(
    score: float,
    tier: str,
    triage_level: str,
    expert_preference: str | None,
    strategy: dict[str, Any],
    access_score: float,
) -> tuple[float, list[str], float]:
    adjusted = score
    notes: list[str] = []
    cap = 1.0
    preference = expert_preference or "system"

    if triage_level == "routine":
        if tier == "top_expert" and not strategy.get("top_expert_allowed"):
            cap = 0.68 if preference in ("system", "no_expert") else 0.76
            adjusted -= 0.16
            notes.append("普通病症降低顶级专家资源占用")
        elif tier == "expert" and preference in ("wish_expert", "must_expert", "named_followup"):
            adjusted += 0.05
            notes.append("已按专家号意图适度加权")
        elif tier in ("general", "specialist") and preference in ("system", "no_expert"):
            adjusted += 0.08 * access_score
            notes.append("普通病症优先匹配可及门诊资源")
        if preference == "must_expert" and tier == "top_expert":
            cap = 0.88
            adjusted -= 0.04
            notes.append("尊重必须专家号选择并保留资源节约提醒")
    elif triage_level == "urgent":
        if tier in ("expert", "top_expert"):
            adjusted += 0.06
            notes.append("中重症提高专科专家适配")
        if tier == "top_expert" and not strategy.get("top_expert_allowed"):
            cap = 0.90
    elif triage_level == "emergency":
        notes.append("急症按急诊能力与距离优先")

    return clamp(min(adjusted, cap)), notes, cap


def doctor_resource_mismatch_penalty(
    doc: dict[str, Any] | None,
    hospital: dict[str, Any] | None,
    tier: str,
    triage_level: str,
    expert_preference: str | None,
    specialty_score: float,
    hospital_score: float,
    access_score: float,
    target_dept: str | None,
) -> tuple[float, list[dict[str, Any]]]:
    """Return the internal H-TriageRank resource mismatch penalty."""

    preference = expert_preference or "system"
    details: list[dict[str, Any]] = []
    total = 0.0

    def add(code: str, label: str, value: float) -> None:
        nonlocal total
        if value <= 0:
            return
        value = round(value, 4)
        total += value
        details.append({"code": code, "label": label, "value": value})

    if triage_level == "routine":
        if tier == "top_expert" and preference in ("system", "no_expert", "wish_expert"):
            add("overuse", "普通病症占用顶级专家资源", 0.10 if preference in ("system", "no_expert") else 0.06)
        if access_score < 0.45:
            add("access", "普通病症距离/可达性不优", 0.04)
    elif triage_level == "urgent":
        if tier == "general":
            add("underuse", "较重病情匹配到低层级医生资源", 0.08)
        if hospital_score < 0.58:
            add("underuse", "较重病情对应医院专科能力不足", 0.10)
        if access_score < 0.40:
            add("access", "较重病情到院距离不优", 0.05)
    elif triage_level == "emergency":
        if hospital and not hospital.get("emergency"):
            add("emergency", "急症路径未匹配急诊能力", 0.18)
        if access_score < 0.55:
            add("access", "急症场景到院可达性不足", 0.10)

    if target_dept and specialty_score < 0.55:
        add("specialty", "病症与医生专科方向匹配不足", 0.06)
    if preference == "must_expert" and triage_level == "routine" and tier == "top_expert":
        add("preference", "尊重专家号选择但保留资源分流提醒", 0.03)
    if preference == "no_expert" and triage_level in ("urgent", "emergency") and tier in ("general", "specialist"):
        add("preference", "较重病情下不建议过度降低医生层级", 0.04)

    return clamp(total, 0.0, 0.30), details
