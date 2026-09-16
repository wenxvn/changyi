"""Schema + validator for future real multi-turn inquiry datasets.

This package intentionally ships NO real patient dialogues. Examples are
always marked ``synthetic_example`` and must never be used as clinical evidence.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Mapping, Sequence

SCHEMA_VERSION = "inquiry-dataset/v1"

ALLOWED_SAFETY_STATES = {"EMERGENCY", "URGENT", "ROUTINE", "INSUFFICIENT_INFORMATION"}
ALLOWED_ANSWERS = {"yes", "no", "unsure", "present", "absent", "unknown"}
ALLOWED_ANNOTATION = {"unlabeled", "weak", "expert_reviewed", "rejected"}
ALLOWED_SOURCE = {"synthetic_example", "sandbox_log", "opted_in_clinic", "public_deidentified"}

REQUIRED_SESSION_FIELDS = (
    "schema_version",
    "source",
    "annotation_status",
    "sessions",
)

REQUIRED_TURN_FIELDS = (
    "turn_index",
    "question_id",
    "question_text",
    "answer",
)

PII_PATTERN = re.compile(
    r"(1[3-9]\d{9})|(\d{17}[\dXx])|([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})"
)


def empty_session(session_id: str) -> dict[str, Any]:
    return {
        "session_id": session_id,
        "initial_text": "",
        "extracted_present_symptoms": [],
        "extracted_absent_symptoms": [],
        "safety_state": "ROUTINE",
        "turns": [],
        "department_label": None,
        "final_route": None,
    }


def validate_session(session: Mapping[str, Any], *, index: int = 0) -> list[str]:
    errors: list[str] = []
    for field in ("session_id", "initial_text", "extracted_present_symptoms", "extracted_absent_symptoms", "safety_state", "turns"):
        if field not in session:
            errors.append(f"sessions[{index}].missing:{field}")
    if session.get("safety_state") not in ALLOWED_SAFETY_STATES:
        errors.append(f"sessions[{index}].invalid_safety_state:{session.get('safety_state')}")
    if not isinstance(session.get("extracted_present_symptoms", []), list):
        errors.append(f"sessions[{index}].present_symptoms_not_list")
    if not isinstance(session.get("extracted_absent_symptoms", []), list):
        errors.append(f"sessions[{index}].absent_symptoms_not_list")
    present = set(session.get("extracted_present_symptoms") or [])
    absent = set(session.get("extracted_absent_symptoms") or [])
    if present & absent:
        errors.append(f"sessions[{index}].symptom_both_present_and_absent:{sorted(present & absent)}")

    turns = session.get("turns") or []
    for t_index, turn in enumerate(turns):
        for field in REQUIRED_TURN_FIELDS:
            if field not in turn:
                errors.append(f"sessions[{index}].turns[{t_index}].missing:{field}")
        if turn.get("answer") not in ALLOWED_ANSWERS:
            errors.append(f"sessions[{index}].turns[{t_index}].invalid_answer:{turn.get('answer')}")
        if PII_PATTERN.search(str(turn.get("question_text", ""))) or PII_PATTERN.search(
            str(session.get("initial_text", ""))
        ):
            errors.append(f"sessions[{index}].possible_pii")
    return errors


def validate_dataset(payload: Mapping[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    for field in REQUIRED_SESSION_FIELDS:
        if field not in payload:
            errors.append(f"missing:{field}")
    if payload.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"unsupported_schema:{payload.get('schema_version')}")
    if payload.get("source") not in ALLOWED_SOURCE:
        errors.append(f"invalid_source:{payload.get('source')}")
    if payload.get("annotation_status") not in ALLOWED_ANNOTATION:
        errors.append(f"invalid_annotation_status:{payload.get('annotation_status')}")
    sessions = payload.get("sessions") or []
    if not isinstance(sessions, list):
        errors.append("sessions_not_list")
        sessions = []
    for index, session in enumerate(sessions):
        errors.extend(validate_session(session, index=index))
    return {
        "valid": not errors,
        "errors": errors,
        "session_count": len(sessions),
        "turn_count": sum(len(session.get("turns") or []) for session in sessions),
        "disclaimer": "synthetic/schema-only；不得声称已拥有真实患者多轮数据。",
    }


def synthetic_example_dataset() -> dict[str, Any]:
    """Clearly labeled synthetic structure for validator/tests only."""

    session = empty_session("synthetic-001")
    session.update(
        {
            "initial_text": "synthetic_example: 头晕两天，没有胸痛",
            "extracted_present_symptoms": ["dizziness"],
            "extracted_absent_symptoms": ["chest_pain"],
            "safety_state": "ROUTINE",
            "turns": [
                {
                    "turn_index": 1,
                    "question_id": "duration",
                    "question_text": "synthetic_example: 持续多久了？",
                    "answer": "yes",
                },
                {
                    "turn_index": 2,
                    "question_id": "chest_pain",
                    "question_text": "synthetic_example: 是否有胸痛？",
                    "answer": "no",
                },
            ],
            "department_label": "神经内科",
            "final_route": "OUTPATIENT",
        }
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "source": "synthetic_example",
        "annotation_status": "unlabeled",
        "sessions": [session],
    }


DATA_DIR = Path(__file__).resolve().parent
EXAMPLE_PATH = DATA_DIR / "synthetic_example.json"
GUIDE_PATH = DATA_DIR / "SCHEMA.md"


def write_schema_assets() -> dict[str, Any]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    example = synthetic_example_dataset()
    EXAMPLE_PATH.write_text(json.dumps(example, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    guide = """# Inquiry Dataset Schema（未来采集用）

本目录只定义 schema / 校验器 / **synthetic_example**，不包含真实患者多轮数据。

## 顶层字段

- `schema_version`: `inquiry-dataset/v1`
- `source`: `synthetic_example` | `sandbox_log` | `opted_in_clinic` | `public_deidentified`
- `annotation_status`: `unlabeled` | `weak` | `expert_reviewed` | `rejected`
- `sessions[]`

## Session 字段

| 字段 | 说明 |
| --- | --- |
| `session_id` | 匿名会话 ID，禁止可逆标识 |
| `initial_text` | 用户初始自由文本（须脱敏） |
| `extracted_present_symptoms` | 标准症状码 present |
| `extracted_absent_symptoms` | 标准症状码 absent |
| `safety_state` | EMERGENCY / URGENT / ROUTINE / INSUFFICIENT_INFORMATION |
| `turns[]` | 追问轮次 |
| `department_label` | 标注科室（可空） |
| `final_route` | 最终路由（可空） |

## Turn 字段

`turn_index`, `question_id`, `question_text`, `answer` ∈ {yes,no,unsure,present,absent,unknown}

## 数据质量与匿名化约束

1. 禁止真实姓名、手机号、身份证、邮箱、住址门牌、病历号。
2. `source=synthetic_example` 的样本永远不得并入真实评测集。
3. 红旗相关否定解析不得直接改写生产 Safety；只用于研究标注。
4. 需保留 `annotation_status`；`expert_reviewed` 才可进入训练/校准主表。
5. 入库前运行 `validate_dataset`；失败样本进入隔离区，不得静默丢弃标签错误。
"""
    GUIDE_PATH.write_text(guide, encoding="utf-8")
    report = validate_dataset(example)
    return {"example_path": str(EXAMPLE_PATH), "validation": report}
