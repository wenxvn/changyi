"""Deduplicated historical engineering evidence, never clinical accuracy."""
from __future__ import annotations
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCES = (
    ("assertion_contract", "results/assertion-scope-v1/final.json"),
    ("assertion_contract", "results/alias-scope-v1/after.json"),
    ("safety_contract", "results/critical-context-v1/verified-w15.json"),
    ("known_report_contract", "results/known-disease-v1/verified-w18.json"),
    ("known_report_contract", "results/disease-conflict-v1/verified-w21.json"),
    ("routing_topic_contract", "results/routing-topics-v1/after.json"),
)


def constraints(layer, row):
    if layer == "assertion_contract":
        return row["expected"]
    if layer == "safety_contract":
        return {"allowed_statuses": sorted(row["expected_statuses"])}
    if layer == "known_report_contract":
        expected = {"known": row["expected_known"]}
        if row["expected_known"] and row.get("expected_disease"):
            expected["disease"] = row["expected_disease"]
        return expected
    return {"known": False, "invented_topic_candidate": False, "direction": row["expected_direction"]}


def aggregate(sources):
    unique, counts = {}, Counter()
    total_rows = 0
    for source in sources:
        rows, layer = source["rows"], source["layer"]
        if source["total"] != len(rows):
            raise ValueError(f"Source total mismatch: {source['name']}")
        failed = sum(row["pass"] is False for row in rows)
        if any(type(row["pass"]) is not bool for row in rows) or source["failed"] != failed:
            raise ValueError(f"Source pass count mismatch: {source['name']}")
        if source.get("passed") is not None and source["passed"] != len(rows) - failed:
            raise ValueError(f"Source passed count mismatch: {source['name']}")
        for row in rows:
            total_rows += 1
            key = (layer, row["text"])
            expected = constraints(layer, row)
            if key in unique:
                old = unique[key]
                if any(name in old["constraints"] and old["constraints"][name] != value for name, value in expected.items()):
                    raise ValueError(f"Conflicting constraints: {key}")
                old["constraints"].update(expected)
                old["sources"].append(source["name"])
                old["all_snapshots_passed"] &= row["pass"]
            else:
                unique[key] = {"layer": layer, "text": row["text"], "constraints": dict(expected), "sources": [source["name"]], "all_snapshots_passed": row["pass"]}
            counts[layer] += 1
    records = list(unique.values())
    return {"raw_rows": total_rows, "unique_layer_texts": len(records), "duplicate_layer_text_rows": total_rows - len(records),
            "unique_raw_texts_across_layers": len({row["text"] for row in records}),
            "layers": {layer: {"raw_rows": count, "unique_texts": sum(row["layer"] == layer for row in records), "snapshot_failures": sum(row["layer"] == layer and not row["all_snapshots_passed"] for row in records)} for layer, count in counts.items()}, "records": records}


def run():
    sources, metadata = [], []
    base = Path(__file__).parent
    for layer, relative in SOURCES:
        path = base / relative
        raw = path.read_bytes()
        payload = json.loads(raw)
        sources.append({"name": relative, "layer": layer, "rows": payload["rows"], "total": payload["total"], "failed": payload["failed"], "passed": payload.get("passed")})
        metadata.append({"path": relative, "sha256": hashlib.sha256(raw).hexdigest(), "scope": payload["scope"], "execution_identity": "not_recorded_by_source_artifact", "verification": "historical_snapshot_not_replayed"})
    result = aggregate(sources)
    code_files = ("backend/app/domain/medical_input.py", "backend/app/domain/symptom_assertions.py", "backend/app/composition.py", "backend/app/infrastructure/models/symptom_disease.py")
    return {"scope": "historical_synthetic_engineering_inventory_not_clinical_accuracy", "aggregation_time_utc": datetime.now(timezone.utc).isoformat(), "sources": metadata,
            "code_hashes_at_aggregation_not_source_execution": {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in code_files},
            "limitations": ["No new model training or snapshot replay", "Unknown source execution code hashes cannot establish current-code verification", "Layers test different contracts and must not be pooled into clinical accuracy", "Synthetic templates are not independent patient or clinical labels"], **result}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit("Refusing to overwrite inventory")
    result = run()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({key: result[key] for key in ("scope", "raw_rows", "unique_layer_texts", "duplicate_layer_text_rows", "unique_raw_texts_across_layers", "layers")}, ensure_ascii=False))
