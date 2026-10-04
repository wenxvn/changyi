"""Snapshot structural coverage and synthetic caller effects, not clinical truth."""
import argparse
import hashlib
import json
from pathlib import Path


def run():
    import app
    root = Path(__file__).resolve().parents[2]
    paths = [root / "data/symptom_disease_model" / name for name in ("symptom_alias_zh.json", "symptom_name_zh.json")]
    paths.append(Path(app.SYMPTOM_DISEASE_MODEL_PATH))
    aliases, names = [json.loads(path.read_text(encoding="utf-8")) for path in paths[:2]]
    model = json.loads(paths[2].read_text(encoding="utf-8"))
    vocabulary = set(model["vocabulary"])
    rows = [{"alias": alias, "code": code, "name": names.get(code), "in_model": code in vocabulary} for alias, code in sorted(aliases.items())]
    probes = []
    for text in ("抽搐", "抽搐和咳嗽", "肌肉痛", "没有抽搐但肌肉痛", "尿急和咳嗽", "口渴和咳嗽", "血压高和咳嗽", "发热", "高烧"):
        details = app.predict_disease_name(text, details=True)
        tags, _ = app._model_standard_symptom_tags(text)
        data = app.app.test_client().post("/api/v1/triage", json={"condition": text}).get_json()["data"]
        probes.append({"text": text, "codes": details.get("normalized_symptoms"), "disease": details.get("disease"), "mapping_review": details.get("mapping_review"), "tags": tags, "triage_status": data["triage_status"]})
    return {"scope": "structural_mapping_audit_and_synthetic_probe_not_clinical_validation", "hashes": {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}, "aliases": len(rows), "unsupported_codes": sorted(set(aliases.values()) - vocabulary), "missing_names": sorted(set(aliases.values()) - set(names)), "rows": rows, "probes": probes}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit("Refusing to overwrite evidence")
    result = run()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({key: result[key] for key in ("aliases", "unsupported_codes", "missing_names")}, ensure_ascii=False))
