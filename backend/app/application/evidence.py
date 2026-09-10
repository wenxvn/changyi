"""Build the read-only evidence view used by the Trust Center."""

from __future__ import annotations

from collections.abc import Callable, Mapping
import json
from pathlib import Path
from typing import Any


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def _dataset_entry(report: Mapping[str, Any], predicate: Callable[[str], bool]) -> dict[str, Any] | None:
    datasets = report.get("datasets", [])
    if not isinstance(datasets, list):
        return None
    for item in datasets:
        if not isinstance(item, Mapping):
            continue
        path = str(item.get("path") or "")
        if predicate(path):
            return {
                "path": path,
                "sha256": str(item.get("sha256") or "unknown"),
                "format": str(item.get("format") or "unknown"),
                "record_count": item.get("record_count"),
                "collections": item.get("collections") or {},
            }
    return None


def _safe_safety_report(triage_fn: Callable[[str], Mapping[str, Any]]) -> dict[str, Any]:
    try:
        from evaluation.safety.evaluate_safety import evaluate_cases, load_cases

        report = evaluate_cases(load_cases(), triage_fn=triage_fn)
        return {
            "available": True,
            "schema_version": report.get("schema_version", "unknown"),
            "case_count": report.get("case_count", 0),
            "red_flag_count": report.get("red_flag_count", 0),
            "red_flag_recall": report.get("red_flag_recall"),
            "under_triage_rate": report.get("under_triage_rate"),
            "over_triage_rate": report.get("over_triage_rate"),
            "emergency_false_negative": report.get("emergency_false_negative", 0),
            "insufficient_information_count": report.get("insufficient_information_count", 0),
            "insufficient_information_matches": report.get("insufficient_information_matches", 0),
            "review_required": list(report.get("review_required") or []),
        }
    except (OSError, ValueError, TypeError, ImportError):
        return {
            "available": False,
            "error": "safety_evaluation_unavailable",
            "review_required": [],
        }


def build_evidence_payload(
    project_root: Path,
    *,
    app_version: str,
    ranking_version: str,
    triage_rules_version: str,
    model_version: str,
    dataset_version: str,
    region_pack_version: str,
    region_code: str,
    triage_fn: Callable[[str], Mapping[str, Any]],
) -> dict[str, Any]:
    """Assemble evidence from committed reports and the existing safety evaluator."""

    quality_report_path = project_root / "data_validation" / "data_quality_report.json"
    quality_report = _read_json(quality_report_path) or {}
    model_path = project_root / "data" / "symptom_disease_model" / "models" / "symptom_disease_41_nb.json"
    model = _read_json(model_path) or {}
    model_metrics = model.get("metrics") if isinstance(model.get("metrics"), Mapping) else {}
    model_entry = _dataset_entry(quality_report, lambda path: path.endswith("symptom_disease_41_nb.json"))
    training_entry = _dataset_entry(
        quality_report,
        lambda path: path.endswith("disease_symptom_structured_41diseases_long.csv"),
    )
    region_entry = _dataset_entry(quality_report, lambda path: path == "regions/320400/manifest.json")
    safety = _safe_safety_report(triage_fn)

    return {
        "disclaimer": "当前为原型阶段离线评估与数据来源摘要，不代表临床验证、官方推荐或诊断结论。",
        "status": "provisional",
        "region": {
            "code": region_code,
            "pack_version": region_pack_version,
            "source": region_entry,
        },
        "versions": {
            "app": app_version,
            "ranking": ranking_version,
            "triage_rules": triage_rules_version,
            "model": model_version,
            "dataset": dataset_version,
        },
        "safety": {
            **safety,
            "report_source": "evaluation/safety/safety_cases.json + runtime legacy triage",
            "label": "Safety Evaluation · provisional",
        },
        "model": {
            "available": bool(model),
            "label": "症状模型离线评估",
            "model_type": model.get("model_type", "unknown"),
            "training_rows": model.get("training_rows"),
            "test_rows": model_metrics.get("test_rows"),
            "class_count": len(model.get("classes") or []),
            "vocabulary_size": len(model.get("vocabulary") or []),
            "top1_accuracy": model_metrics.get("accuracy"),
            "top3_accuracy": model_metrics.get("top3_accuracy"),
            "evaluation_scope": "单次按疾病类别分层切分；仅作为 prototype/offline evaluation",
            "model_source": model_entry,
            "training_data_source": training_entry,
        },
        "data_quality": {
            "available": bool(quality_report),
            "report_source": "data_validation/data_quality_report.json",
            "schema_version": quality_report.get("schema_version", "unknown"),
            "dataset_count": quality_report.get("dataset_count", 0),
            "issue_count": quality_report.get("issue_count", 0),
            "status": "issues_present" if quality_report.get("issue_count", 0) else "clean",
        },
        "dataset_manifest": [
            {
                "path": str(item.get("path") or ""),
                "sha256": str(item.get("sha256") or "unknown"),
                "format": str(item.get("format") or "unknown"),
                "record_count": item.get("record_count"),
                "collections": item.get("collections") or {},
            }
            for item in quality_report.get("datasets", [])
            if isinstance(item, Mapping)
        ] if isinstance(quality_report.get("datasets", []), list) else [],
        "limitations": [
            "安全评估中的 review_required case 不视为发布放行。",
            "当前医院目录仍处于 migration_pending，逐字段来源、许可和更新时间未齐备。",
            "医生资料为 public_source_mixed，公开资料不等于临床适配或疗效证明。",
            "模型指标来自小数据单次切分，不能代表真实临床表现。",
        ],
    }
