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


def _hospital_catalog_evidence(project_root: Path) -> dict[str, Any]:
    catalog = _read_json(project_root / "data" / "regions" / "320400" / "hospitals" / "catalog.json") or {}
    records = catalog.get("records") if isinstance(catalog.get("records"), list) else []
    field_policy = catalog.get("field_policy") if isinstance(catalog.get("field_policy"), Mapping) else {}
    derived = field_policy.get("derived_features") if isinstance(field_policy.get("derived_features"), Mapping) else {}
    return {
        "available": bool(catalog),
        "dataset_id": catalog.get("dataset_id", "unknown"),
        "status": catalog.get("status", "unknown"),
        "source_class": catalog.get("source_class", "unknown"),
        "source_url": catalog.get("source_url"),
        "last_verified_at": catalog.get("last_verified_at"),
        "license_status": catalog.get("license_status", "unknown"),
        "deidentified": catalog.get("deidentified") is True,
        "record_count": len(records),
        "public_fact_fields": list(field_policy.get("public_facts") or []),
        "derived_fields": {
            str(name): {
                "status": item.get("status", "unknown"),
                "formula_version": item.get("formula_version", "unknown"),
            }
            for name, item in derived.items()
            if isinstance(item, Mapping)
        },
        "unsupported_fields": list(field_policy.get("unsupported_null") or []),
        "notice": "医院公开事实、派生能力线索和不支持字段分开登记；目录仍需外部来源、许可和更新时间核验。",
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
        lambda path: path.endswith("symptom_disease_model/data/disease_symptom_structured_41diseases_long.csv"),
    )
    region_entry = _dataset_entry(quality_report, lambda path: path == "regions/320400/manifest.json")
    safety = _safe_safety_report(triage_fn)
    grouped_report = _read_json(project_root / "evaluation" / "model" / "grouped_split_report.json") or {}

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
            "evaluation_scope": "随机基线 + exact fingerprint grouped + near-duplicate same-label group split；仅作为 prototype/offline evaluation",
            "random_baseline": grouped_report.get("random_baseline"),
            "grouped_fingerprint": grouped_report.get("grouped_fingerprint"),
            "near_duplicate_same_label": grouped_report.get("near_duplicate_same_label"),
            "near_duplicate_global": grouped_report.get("near_duplicate_global"),
            "near_duplicate_components": grouped_report.get("near_duplicate_components"),
            "primary_split": grouped_report.get("primary_split", "near_duplicate_same_label"),
            "near_duplicate_audit": grouped_report.get("near_duplicate_audit"),
            "strict_near_duplicate_isolation": {
                "label": "Strict Near-duplicate Isolation",
                "test_samples": (grouped_report.get("near_duplicate_same_label") or {}).get("test_rows"),
                "present_classes": (grouped_report.get("near_duplicate_same_label") or {}).get("present_class_count"),
                "total_classes": grouped_report.get("dataset", {}).get("class_count"),
                "cross_split_near_duplicates": (
                    (grouped_report.get("near_duplicate_same_label") or {}).get("cross_split_near_duplicates") or {}
                ).get("pair_count"),
                "seed": grouped_report.get("configuration", {}).get("seed"),
                "jaccard_threshold": grouped_report.get("configuration", {}).get("near_duplicate_threshold"),
                "comparable_to_random_split": False,
                "explanation": "严格近重复隔离用于评估去除症状高度相似样本泄漏后的泛化风险。由于当前数据集规模较小，严格隔离后测试子集仅覆盖部分疾病类别，因此该指标不能与随机切分准确率直接等价比较。",
            },
            "split_manifest": "evaluation/model/split_manifest.json",
            "model_source": model_entry,
            "training_data_source": training_entry,
        },
        "hospital_data": _hospital_catalog_evidence(project_root),
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
            "医院目录已迁移到 Region Pack，但逐字段来源、许可和更新时间仍未齐备；派生能力线索不代表官方评级。",
            "医生资料为 public_source_mixed，公开资料不等于临床适配或疗效证明。",
            "模型指标来自 304 条小数据；Near-duplicate Group Split 降低近重复泄漏，指标更贴近泛化风险但不等于临床表现。",
            "严格近重复隔离测试集仅覆盖部分疾病类别，不能与随机切分准确率直接横向比较。",
            "交通样本未全部通过质量门时，可达性按直线距离估算，站点信息仅作参考。",
        ],
    }


class EvidenceApplicationService:
    """Compose the Trust Center evidence view from a fixed project root."""

    def __init__(self, project_root: Path, triage_fn: Callable[[str], Mapping[str, Any]]) -> None:
        self._project_root = project_root
        self._triage_fn = triage_fn

    def build(
        self,
        *,
        app_version: str,
        ranking_version: str,
        triage_rules_version: str,
        model_version: str,
        dataset_version: str,
        region_pack_version: str,
        region_code: str,
    ) -> dict[str, Any]:
        return build_evidence_payload(
            self._project_root,
            app_version=app_version,
            ranking_version=ranking_version,
            triage_rules_version=triage_rules_version,
            model_version=model_version,
            dataset_version=dataset_version,
            region_pack_version=region_pack_version,
            region_code=region_code,
            triage_fn=self._triage_fn,
        )
