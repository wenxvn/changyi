"""Validate repository datasets without modifying source data.

The report is intentionally conservative: an anomaly is recorded with its
dataset and field context, but no value is repaired or silently discarded.
The validator does not include symptom text or other potentially sensitive
row content in its output.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_ROOT = ROOT / "data"
DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def issue(dataset: str, code: str, message: str) -> dict[str, str]:
    return {"dataset": dataset, "code": code, "message": message}


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _check_coordinates(rows: Iterable[dict[str, Any]], dataset: str, lat_key: str, lng_key: str) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    for index, row in enumerate(rows, start=1):
        lat, lng = row.get(lat_key), row.get(lng_key)
        if not _is_number(lat) or not 18 <= float(lat) <= 55:
            issues.append(issue(dataset, "COORDINATE_LATITUDE", f"row {index}: {lat_key} 不在中国大陆纬度范围"))
        if not _is_number(lng) or not 73 <= float(lng) <= 136:
            issues.append(issue(dataset, "COORDINATE_LONGITUDE", f"row {index}: {lng_key} 不在中国大陆经度范围"))
    return issues


def _duplicate_issues(rows: list[dict[str, Any]], dataset: str, key: str) -> list[dict[str, str]]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for row in rows:
        value = row.get(key)
        if value in (None, ""):
            continue
        value_text = str(value)
        if value_text in seen:
            duplicates.add(value_text)
        seen.add(value_text)
    if not duplicates:
        return []
    return [issue(dataset, "DUPLICATE_KEY", f"{key} 重复 {len(duplicates)} 个（仅输出数量，不输出原始值）")]


def _parse_time(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None


def _validate_known_json(path: Path, value: Any, data_root: Path) -> list[dict[str, str]]:
    relative = str(path.relative_to(data_root))
    issues: list[dict[str, str]] = []
    if path.name == "bus_routes.json" and isinstance(value, dict):
        rows = value.get("routes")
        if isinstance(rows, list):
            issues.extend(_duplicate_issues(rows, relative, "route_id"))
            for index, row in enumerate(rows, start=1):
                if _is_number(row.get("bus_count")) and row["bus_count"] < 0:
                    issues.append(issue(relative, "NEGATIVE_VALUE", f"row {index}: bus_count 为负数"))
                if _is_number(row.get("ticket")) and row["ticket"] < 0:
                    issues.append(issue(relative, "NEGATIVE_VALUE", f"row {index}: ticket 为负数"))
                start, end = _parse_time(row.get("morning_peak_start")), _parse_time(row.get("morning_peak_end"))
                if start and end and end < start:
                    issues.append(issue(relative, "TIME_ORDER", f"row {index}: morning_peak_end 早于 morning_peak_start"))
                evening_start, evening_end = _parse_time(row.get("evening_peak_start")), _parse_time(row.get("evening_peak_end"))
                if evening_start and evening_end and evening_end < evening_start:
                    issues.append(issue(relative, "TIME_ORDER", f"row {index}: evening_peak_end 早于 evening_peak_start"))
                for field in ("morning_peak_start", "morning_peak_end", "evening_peak_start", "evening_peak_end"):
                    parsed = _parse_time(row.get(field))
                    if parsed and parsed.year < 2020:
                        issues.append(issue(relative, "PLACEHOLDER_TIMESTAMP", f"row {index}: {field} 使用疑似占位年份"))
    elif path.name == "bus_stations.json" and isinstance(value, dict):
        rows = value.get("stations")
        if isinstance(rows, list):
            issues.extend(_duplicate_issues(rows, relative, "station_id"))
            issues.extend(_check_coordinates(rows, relative, "latitude", "longitude"))
    elif path.name == "taxi_operations.json" and isinstance(value, dict):
        rows = value.get("operations")
        if isinstance(rows, list):
            issues.extend(_duplicate_issues(rows, relative, "sample_no"))
            for index, row in enumerate(rows, start=1):
                if _is_number(row.get("drive_mile")) and row["drive_mile"] < 0:
                    issues.append(issue(relative, "NEGATIVE_VALUE", f"row {index}: drive_mile 为负数"))
                if _is_number(row.get("fact_price")) and row["fact_price"] < 0:
                    issues.append(issue(relative, "NEGATIVE_VALUE", f"row {index}: fact_price 为负数"))
                issues.extend(_check_coordinates([row], relative, "dep_latitude", "dep_longitude"))
                issues.extend(_check_coordinates([row], relative, "dest_latitude", "dest_longitude"))
    elif path.name == "bike_stations.json" and isinstance(value, dict):
        rows = value.get("stations")
        if isinstance(rows, list):
            issues.extend(_duplicate_issues(rows, relative, "station_no"))
            issues.extend(_check_coordinates(rows, relative, "latitude", "longitude"))
            for index, row in enumerate(rows, start=1):
                for field in ("station_range", "lock_num", "bike_num", "e_bike_num", "h_bike_num"):
                    if _is_number(row.get(field)) and row[field] < 0:
                        issues.append(issue(relative, "NEGATIVE_VALUE", f"row {index}: {field} 为负数"))
    elif path.name == "bike_vehicles.json" and isinstance(value, dict):
        rows = value.get("vehicles")
        if isinstance(rows, list):
            issues.extend(_duplicate_issues(rows, relative, "sample_no"))
            issues.extend(_check_coordinates(rows, relative, "latitude", "longitude"))
    elif path.name.startswith("doctors_h") and path.suffix == ".json" and isinstance(value, dict):
        rows = value.get("doctors")
        if isinstance(rows, list):
            declared = value.get("total_doctors")
            if declared is not None and declared != len(rows):
                issues.append(issue(relative, "COUNT_MISMATCH", f"total_doctors={declared}，实际 doctors={len(rows)}"))
            for index, row in enumerate(rows, start=1):
                if not isinstance(row, dict) or not str(row.get("name") or "").strip():
                    issues.append(issue(relative, "MISSING_REQUIRED_FIELD", f"row {index}: 缺少医生姓名"))
                if not isinstance(row, dict) or not str(row.get("department") or "").strip():
                    issues.append(issue(relative, "MISSING_REQUIRED_FIELD", f"row {index}: 缺少科室"))
    return issues


def _declared_dataset_paths(data_root: Path, region_code: str) -> list[tuple[str, Path]]:
    manifest_path = data_root / "regions" / region_code / "manifest.json"
    if not manifest_path.exists():
        return [(f"regions/{region_code}/manifest.json", manifest_path)]
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return [(f"regions/{region_code}/manifest.json", manifest_path)]
    pairs: list[tuple[str, Path]] = []
    for item in manifest.get("datasets", {}).get("doctors", []):
        if isinstance(item, dict) and item.get("path"):
            pairs.append((f"regions/{region_code}/manifest.json -> {item['path']}", (manifest_path.parent / item["path"]).resolve()))
    for name, item in (manifest.get("datasets", {}).get("transit", {}) or {}).items():
        if isinstance(item, dict) and item.get("path"):
            pairs.append((f"regions/{region_code}/manifest.json -> {name}", (manifest_path.parent / item["path"]).resolve()))
    return pairs


def validate_data_root(data_root: Path, region_code: str = "320400") -> dict[str, Any]:
    data_root = data_root.resolve()
    try:
        data_root_label = str(data_root.relative_to(ROOT))
    except ValueError:
        data_root_label = data_root.name
    datasets: list[dict[str, Any]] = []
    issues: list[dict[str, str]] = []
    for path in sorted(data_root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in {".json", ".csv"}:
            continue
        relative = str(path.relative_to(data_root))
        record: dict[str, Any] = {"path": relative, "sha256": sha256(path)}
        try:
            if path.suffix.lower() == ".json":
                value = json.loads(path.read_text(encoding="utf-8"))
                record["format"] = "json"
                if isinstance(value, list):
                    record["record_count"] = len(value)
                elif isinstance(value, dict):
                    record["top_level_keys"] = sorted(str(key) for key in value)
                    collection_counts = {
                        key: len(value[key]) for key in sorted(value) if isinstance(value[key], list)
                    }
                    if collection_counts:
                        record["collections"] = collection_counts
                issues.extend(_validate_known_json(path, value, data_root))
            else:
                with path.open(newline="", encoding="utf-8") as handle:
                    record["format"] = "csv"
                    record["record_count"] = sum(1 for _ in csv.DictReader(handle))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, csv.Error) as exc:
            record["parse_error"] = type(exc).__name__
            issues.append(issue(relative, "PARSE_ERROR", "文件无法按声明格式解析"))
        datasets.append(record)

    manifest_path = data_root / "regions" / region_code / "manifest.json"
    if not manifest_path.exists():
        issues.append(issue(str(manifest_path.relative_to(data_root)), "MANIFEST_MISSING", "active Region Pack manifest 不存在"))
    else:
        for label, declared_path in _declared_dataset_paths(data_root, region_code):
            try:
                declared_path.relative_to(data_root)
            except ValueError:
                issues.append(issue(label, "PATH_OUTSIDE_DATA_ROOT", "manifest 路径越出 data 根目录"))
                continue
            if not declared_path.exists():
                issues.append(issue(label, "DECLARED_FILE_MISSING", "manifest 声明的数据文件不存在"))

    return {
        "schema_version": "data-quality-report/v1",
        "data_root": data_root_label,
        "region_code": region_code,
        "dataset_count": len(datasets),
        "issue_count": len(issues),
        "datasets": datasets,
        "issues": issues,
        "policy": "只记录异常，不自动修复；报告不包含原始症状文本、身份信息或整行数据。",
    }


def report_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Data Quality Report",
        "",
        f"- Schema: `{report['schema_version']}`",
        f"- Region: `{report['region_code']}`",
        f"- Datasets scanned: `{report['dataset_count']}`",
        f"- Issues: `{report['issue_count']}`",
        "",
        "## Issues",
        "",
    ]
    if not report["issues"]:
        lines.append("No issues detected.")
    else:
        lines.extend(f"- `{item['dataset']}` · `{item['code']}` · {item['message']}" for item in report["issues"])
    lines.extend(["", "## Dataset inventory", "", "| Path | Format | SHA-256 | Records/collections |", "| --- | --- | --- | --- |"])
    for item in report["datasets"]:
        inventory = item.get("record_count", item.get("collections", "-"))
        lines.append(f"| `{item['path']}` | {item.get('format', '-')} | `{item['sha256']}` | `{inventory}` |")
    lines.extend(["", report["policy"], ""])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, default=DEFAULT_DATA_ROOT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--region", default="320400")
    parser.add_argument("--strict", action="store_true", help="发现异常时以非零状态退出")
    args = parser.parse_args(argv)
    report = validate_data_root(args.data_root, args.region)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "data_quality_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (args.output_dir / "data_quality_report.md").write_text(report_markdown(report), encoding="utf-8")
    print(f"scanned={report['dataset_count']} issues={report['issue_count']}")
    return 1 if args.strict and report["issue_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
