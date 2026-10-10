"""Frozen clinician-authored fictional vignettes; no patient records or fitting."""
from __future__ import annotations
import argparse
import csv
import hashlib
import io
import json
import re
from pathlib import Path
from urllib.request import urlopen

COMMIT = "217352f4a5144390f2af30042e208167b14b9268"
BASE = f"https://raw.githubusercontent.com/ashwinra-code/gpt-health-eval/{COMMIT}/"
ROOT = Path(__file__).resolve().parent / "results/public-vignettes-v1"


def download_frozen_source():
    ROOT.mkdir(parents=True, exist_ok=True)
    target = ROOT / "source.json"
    if target.exists():
        raise ValueError("Frozen source exists; do not overwrite")
    license_text = urlopen(BASE + "data/LICENSE", timeout=30).read().decode("utf-8")
    if not license_text.startswith("CC0 1.0 Universal"):
        raise ValueError("Dataset license changed")
    raw = urlopen(BASE + "data/DataOriginal_FINAL.csv", timeout=30).read()
    records = list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))))
    selected = [r for r in records if r["case_id"].startswith("F") and r["variant_code"] == "WM"]
    expected = {f"F{i}" for i in range(1, 28)}
    if len(records) != 960 or len(selected) != 27 or {r["case_id"] for r in selected} != expected:
        raise ValueError("Incomplete original F reference cohort")
    cases = []
    for r in sorted(selected, key=lambda r: int(r["case_id"][1:])):
        text = r["prompt_text"]
        if "About me:" not in text or "Please answer in exactly this format:" not in text:
            raise ValueError("Unexpected source prompt boundaries")
        core = text.split("About me:", 1)[1].split("Please answer in exactly this format:", 1)[0].strip()
        cases.append({"case_id": r["case_id"], "base_case_id": r["case_pair"], "domain": r["domain"],
                      "condition_en": core, "source_gold": r["gold_triage"]})
    result = {"source_commit": COMMIT, "source_url": BASE + "data/DataOriginal_FINAL.csv",
              "source_csv_sha256": hashlib.sha256(raw).hexdigest(), "source_license": "CC0-1.0",
              "source_paper": "https://doi.org/10.1038/s41591-026-04297-7",
              "selection": "all_actual_original_F1_to_F27_WM_no_anchor_no_barrier_before_predictions",
              "origin": "published_clinician_authored_fictional_vignettes", "patient_records": False,
              "raw_source_rows": len(records), "selected_base_case_count": len(cases),
              "source_vignette_id_count": len({r["case_id"] for r in records}),
              "source_base_case_id_count": len({r["case_pair"] for r in records}), "cases": cases}
    with target.open("x", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    with (ROOT / "LICENSE.source.txt").open("x", encoding="utf-8") as f:
        f.write(license_text)
    print(f"FROZEN_SOURCE {len(cases)} cases; no API calls or model fitting")


def freeze_translation():
    from .public_vignette_zh import TRANSLATIONS
    raw = (ROOT / "source.json").read_bytes()
    source = json.loads(raw)
    if set(TRANSLATIONS) != {r["case_id"] for r in source["cases"]}:
        raise ValueError("Every source case needs exactly one translation")
    cases = [{**r, "condition_zh": TRANSLATIONS[r["case_id"]]} for r in source["cases"]]
    result = {"source_sha256": hashlib.sha256(raw).hexdigest(), "source_commit": COMMIT,
              "scope": "agent_translated_clinician_authored_fictional_vignettes_not_native_chinese_validation",
              "translation_medically_reviewed": False, "label_input_allowed": False,
              "model_fitting": False, "cases": cases}
    with (ROOT / "translations.json").open("x", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"FROZEN_TRANSLATION {len(cases)} cases; no predictions")


def evaluate_frozen(*, development_recheck=False, run_id=None):
    # Freeze all wording before the serving API or labels can affect a change.
    from .versioned_challenge import identity, write_new
    import app
    raw = (ROOT / "translations.json").read_bytes()
    dataset = json.loads(raw)
    source_raw = (ROOT / "source.json").read_bytes()
    if hashlib.sha256(source_raw).hexdigest() != dataset["source_sha256"]:
        raise ValueError("Translation source changed")
    if run_id is not None and (not development_recheck or not re.fullmatch(r"development-[a-z0-9_-]{1,48}", run_id)):
        raise ValueError("Only a new explicitly named development recheck may use run-id")
    filename = (run_id or "development-after-v6.9") + ".json" if development_recheck else "before-v6.8.json"
    path = ROOT / filename
    if path.exists():
        raise ValueError("Never overwrite an external baseline")
    before = identity()
    client = app.app.test_client()
    rows = []
    grade_map = {"ROUTINE": "B", "URGENT": "C", "EMERGENCY": "D"}
    for r in dataset["cases"]:
        response = client.post("/api/v1/triage", json={"condition": r["condition_zh"]})
        payload = response.get_json(silent=True)
        data = payload.get("data") if response.status_code == 200 and isinstance(payload, dict) else None
        status = data.get("triage_status") if isinstance(data, dict) else None
        actual = grade_map.get(status)
        gold = r["source_gold"].split("/")
        rows.append({"case_id": r["case_id"], "base_case_id": r["base_case_id"], "domain": r["domain"],
                     "source_gold": r["source_gold"], "api_status": status, "proxy_grade": actual,
                     "source_grade_compatible": actual in gold, "has_unrepresentable_home_grade": "A" in gold,
                     "department": data.get("matched_department") if isinstance(data, dict) else None,
                     "aux_abstained": data.get("disease_prediction", {}).get("abstained") if isinstance(data, dict) else None})
    after = identity()
    if before != after:
        raise ValueError("Execution identity changed")
    strict_er = [r for r in rows if r["source_gold"] == "D"]
    er_edge = [r for r in rows if r["source_gold"] == "C/D"]
    result = {"identity": before, "translations_sha256": hashlib.sha256(raw).hexdigest(),
              "scope": dataset["scope"], "clinical_validation": False, "new_fits": 0,
              "development_exposure": "used_for_development" if development_recheck else "first_frozen_external_evaluation",
              "status_mapping_is_ordinal_proxy_not_time_or_medical_certification": True,
              "total_source_cases": len(rows), "base_case_count": len({r["base_case_id"] for r in rows}),
              "source_grade_compatible_count": sum(r["source_grade_compatible"] for r in rows),
              "unrepresentable_home_grade_cases": sum(r["has_unrepresentable_home_grade"] for r in rows),
              "strict_source_emergency_cases": len(strict_er),
              "strict_source_emergency_not_er": sum(r["api_status"] != "EMERGENCY" for r in strict_er),
              "source_emergency_edge_cases": len(er_edge),
              "edge_urgency_not_in_source_range": sum(not r["source_grade_compatible"] for r in er_edge),
              "abstained_status_cases": sum(r["api_status"] == "INSUFFICIENT_INFORMATION" for r in rows),
              "api_errors": sum(r["api_status"] is None for r in rows), "rows": rows}
    write_new(path, result)
    print(json.dumps({k: v for k, v in result.items() if k not in {"identity", "rows"}}, ensure_ascii=True))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["fetch", "translate", "evaluate", "recheck-development"])
    parser.add_argument("--run-id")
    args = parser.parse_args()
    if args.mode == "recheck-development":
        evaluate_frozen(development_recheck=True, run_id=args.run_id)
    else:
        if args.run_id is not None:
            parser.error("run-id is only for explicitly declared development rechecks")
        {"fetch": download_frozen_source, "translate": freeze_translation, "evaluate": evaluate_frozen}[args.mode]()
