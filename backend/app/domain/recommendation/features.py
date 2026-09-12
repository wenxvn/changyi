"""Pure hospital recommendation feature functions.

These functions operate only on explicit inputs.  Transit access, distance,
repositories, and model inference remain outside this module so feature
semantics can be tested without starting the web application.
"""

from __future__ import annotations

from typing import Any

from .scoring import clamp


def hospital_strength_for_department(hospital: dict[str, Any] | None, target_dept: str | None) -> float:
    """Explainable department-fit only.

    Provisional legacy scores (`derived_capability_scores` / `strength_scores`)
    are retained in the catalog for migration and debug, but must not decide
    clinical ranking. Ranking uses public department existence facts only.
    """

    if not hospital:
        return 0.5
    if not target_dept:
        return 0.6
    departments = hospital.get("departments", [])
    if target_dept in departments:
        return 0.82
    for dept in departments:
        if target_dept in dept or dept in target_dept:
            return 0.72
    for dept in departments:
        if _dept_pair_related(target_dept, dept):
            return 0.68
    return 0.5


def _dept_pair_related(target_dept: str, dept: str) -> bool:
    families = (
        ("肿瘤",),
        ("消化", "脾胃", "胃肠"),
        ("呼吸", "肺"),
        ("心血管", "心脏"),
        ("神经", "脑"),
        ("骨", "脊柱", "关节"),
        ("妇", "产", "生殖"),
        ("儿", "儿童", "新生儿"),
        ("肾", "泌尿"),
        ("中医", "针灸", "推拿", "康复"),
    )
    for family in families:
        if any(token in target_dept for token in family) and any(token in dept for token in family):
            return True
    return False


def level_score_norm(hospital: dict[str, Any] | None) -> float:
    level = hospital.get("level", "") if hospital else ""
    if level == "三级甲等":
        return 1.0
    if "三级" in level:
        return 0.82
    if "二级甲等" in level:
        return 0.68
    if "二级" in level:
        return 0.58
    return 0.5


def hospital_availability_score(hospital: dict[str, Any] | None, triage_level: str = "routine") -> float:
    beds = (hospital or {}).get("beds")
    daily = (hospital or {}).get("daily_outpatients")
    if not hospital_availability_data_available(hospital):
        return 0.0
    capacity = clamp(float(beds) / 1800.0)
    crowding = float(daily) / max(1.0, float(beds))
    waiting_relief = clamp(1.15 - crowding / 6.0)
    emergency_bonus = 0.12 if hospital and hospital.get("emergency") else 0.0
    if triage_level == "emergency":
        return clamp(capacity * 0.45 + waiting_relief * 0.30 + emergency_bonus + 0.10)
    return clamp(capacity * 0.35 + waiting_relief * 0.50 + emergency_bonus)


def hospital_availability_data_available(hospital: dict[str, Any] | None) -> bool:
    """Return whether capacity inputs are complete enough to rank on."""

    if not hospital:
        return False
    beds = hospital.get("beds")
    daily = hospital.get("daily_outpatients")
    return all(
        isinstance(value, (int, float)) and not isinstance(value, bool) and float(value) >= 0
        for value in (beds, daily)
    )


def hospital_quality_score(hospital: dict[str, Any] | None) -> float:
    level_norm = level_score_norm(hospital)
    rating = (hospital or {}).get("rating")
    if not isinstance(rating, (int, float)):
        return level_norm
    rating_norm = clamp(float(rating) / 5.0)
    return clamp(rating_norm * 0.58 + level_norm * 0.42)


def continuity_score(condition: str, target_dept: str | None, hospital: dict[str, Any] | None) -> float:
    text = condition or ""
    continuity_words = ("复诊", "随访", "慢病", "长期", "配药", "术后", "半年", "一年", "老病号")
    if not any(word in text for word in continuity_words):
        return 0.55
    strength = hospital_strength_for_department(hospital, target_dept)
    if any(word in text for word in ("慢病", "长期", "配药", "随访")) and hospital and "综合" in hospital.get("type", ""):
        strength = max(strength, 0.70)
    if any(word in text for word in ("康复", "术后")) and hospital and any("康复" in dept for dept in hospital.get("departments", [])):
        strength = max(strength, 0.78)
    return clamp(strength)


def special_population_fit(condition: str, hospital: dict[str, Any] | None) -> float:
    text = condition or ""
    name = (hospital or {}).get("name", "")
    hospital_type = (hospital or {}).get("type", "")
    score = 0.55
    if any(word in text for word in ("儿童", "小儿", "婴儿", "新生儿")):
        score = 1.0 if "儿童" in name else 0.48
    elif any(word in text for word in ("孕", "产检", "分娩", "胎动", "产后", "妇科", "月经")):
        score = 1.0 if ("妇幼" in name or "妇" in hospital_type or "妇" in name) else 0.55
    elif any(word in text for word in ("肿瘤", "癌", "放疗", "化疗")):
        score = 1.0 if "肿瘤" in name else 0.62
    elif any(word in text for word in ("口腔", "牙", "正畸", "牙周")):
        score = 1.0 if "口腔" in name else 0.45
    elif any(word in text for word in ("中医", "针灸", "推拿", "骨伤", "脾胃")):
        score = 1.0 if "中医" in name or "中医" in hospital_type else 0.65
    elif any(word in text for word in ("老人", "老年", "慢病", "康复")):
        score = 0.95 if ("老年" in name or any("康复" in dept for dept in hospital.get("departments", []))) else 0.65
    return score


def fairness_score(condition: str, hospital: dict[str, Any] | None, distance: float | None, triage_level: str = "routine") -> float:
    level_norm = level_score_norm(hospital)
    local_bonus = 0.0 if distance is None else (0.18 if distance <= 8 else (0.10 if distance <= 15 else 0.0))
    level_text = hospital.get("level", "") if hospital else ""
    primary_bonus = 0.0
    if triage_level in ("routine", "first_visit"):
        if "二级" in level_text:
            primary_bonus = 0.18
        elif "三级乙等" in level_text:
            primary_bonus = 0.08
    elif triage_level == "urgent" and "三级" in level_text:
        primary_bonus = 0.06
    fairness = 0.50 + local_bonus + primary_bonus - (0.08 if triage_level in ("routine", "first_visit") and level_norm >= 1.0 else 0)
    return clamp(fairness)


def hospital_risk_penalty(
    condition: str,
    target_dept: str | None,
    hospital: dict[str, Any],
    triage: dict[str, Any] | None,
) -> float:
    triage_level = (triage or {}).get("level", "routine")
    penalty = 0.0
    if triage_level == "emergency" and not hospital.get("emergency"):
        penalty += 0.35
    if target_dept:
        matched = hospital_strength_for_department(hospital, target_dept)
        if matched < 0.58:
            penalty += 0.10
    population_fit = special_population_fit(condition, hospital)
    if population_fit < 0.50:
        penalty += 0.12
    return clamp(penalty, 0.0, 0.45)


def hospital_recommend_reasons(
    hospital: dict[str, Any],
    feature_scores: dict[str, Any],
    distance: float | None,
    matched_dept: str | None,
    triage_level: str,
    *,
    district: str | None = None,
    district_preference: str | None = None,
) -> list[str]:
    reasons = []
    if triage_level == "emergency" and hospital.get("emergency"):
        reasons.append("目录资料标记设有急诊字段（非实时接诊能力）")
    if matched_dept:
        departments = hospital.get("departments") or []
        if matched_dept in departments:
            reasons.append(f"设有{matched_dept}")
        elif any(matched_dept in dept or dept in matched_dept for dept in departments):
            reasons.append(f"公开资料显示存在{matched_dept}相关专科方向")
        elif departments:
            reasons.append("公开资料显示存在相关专科方向")
        else:
            reasons.append("按公开科室资料综合匹配")
    if distance is not None:
        reasons.append(f"到院直线距离约{distance}km（仅在你提供位置时估算）")
    elif triage_level != "emergency":
        reasons.append("未提供精确位置，本次未按距离排序")
    if district and hospital.get("district") == district:
        reasons.append(f"位于你选择的{district}")
        if district_preference == "prefer_home_district":
            reasons.append("已按“优先本区”偏好综合排序")
    elif district_preference == "allow_cross_district" and district and hospital.get("district") and hospital.get("district") != district:
        reasons.append("可接受跨区就医，未因跨区大幅降权")
    if feature_scores["quality"] >= 0.85:
        reasons.append("医院等级和综合质量较高")
    if feature_scores["availability"] >= 0.72 and (hospital.get("beds") is not None or hospital.get("daily_outpatients") is not None):
        reasons.append("承载能力/就诊可用性较好")
    if feature_scores["fairness"] >= 0.70:
        reasons.append("符合分级诊疗与就近可及原则")
    traffic = feature_scores.get("traffic_access") or {}
    if distance is not None and traffic.get("used_in_ranking") and traffic.get("public_transport_score", 0) >= 0.75 and triage_level != "emergency":
        reasons.append("公交/出租车到院可达性较好")
    if not reasons:
        reasons.append("按临床匹配、医院等级和安全能力综合排序")
    return reasons[:4]


EXCLUDED_EVIDENCE_NOTICES = (
    "科研资料仅作公开资料展示，不参与 patient-fit 排序。",
    "当前交通数据未通过正式质量门，仅作参考，不参与排序。",
)
