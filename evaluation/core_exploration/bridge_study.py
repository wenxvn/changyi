"""Canonical vocabulary ablation plus synthetic Chinese input/Safety boundary."""
from __future__ import annotations
import json
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from scipy.special import softmax
from threadpoolctl import threadpool_limits

from .study import OUT, SEEDS, atomic_json, labels, representation, estimator, select_candidate, fit_temperature, model_logits, metrics, study_lock
from .generalization import global_split
from .data_audit import mask_row
from .semantic_bridge import extract_english, parse_chinese
from evaluation.care_routing.round3_split_audit import load_expanded, load_structured, quota_split, cross_split_leakage_audit

TARGET = OUT.parent / "bridge-v1"
CASES = [
    {"text": "咳嗽，没有胸痛", "present": ["cough"], "absent": ["chest_pain"]},
    {"text": "没有胸痛，但后来胸痛", "present": ["chest_pain"], "contradiction": True},
    {"text": "不是没有胸痛", "unknown": ["chest_pain"]},
    {"text": "不确定有没有胸痛", "unknown": ["chest_pain"]},
    {"text": "发热", "present": ["fever"], "forbidden_present": ["high_fever"]},
    {"text": "我妈妈以前有胸痛，我没有", "clarify": True},
    {"text": "问一下胸痛应该怎么看", "clarify": True},
    {"text": "没有咳嗽，没有发热", "present": [], "absent": ["cough", "fever"]},
    {"text": "持续胸痛喘不过气", "expected_safety": "EMERGENCY"},
    {"text": "最近头晕，说不清怎么回事", "present": ["dizziness"]},
    {"text": "我只是想随便看看", "clarify": True},
    {"text": "咳嗽三天，没有呼吸困难，无持续高烧", "expected_safety": "ROUTINE"},
]


def chinese_challenge():
    # Actual formal Safety/API path is checked separately; no classifier output
    # is allowed to replace that status in this experimental challenge.
    import app
    client = app.app.test_client()
    results = []
    for case in CASES:
        parsed = parse_chinese(case["text"])
        checks = []
        for state in ("present", "absent", "unknown"):
            if state in case:
                checks.append(set(case[state]) <= set(parsed[state]))
        if "forbidden_present" in case:
            checks.append(not (set(case["forbidden_present"]) & set(parsed["present"])))
        if case.get("contradiction"):
            checks.append(bool(parsed["contradiction"]))
        if case.get("clarify"):
            checks.append(parsed["needs_clarification"])
        response = client.post("/api/v1/triage", json={"condition": case["text"]}).get_json()
        safety = (response.get("data") or {}).get("triage_status")
        if case.get("expected_safety"):
            checks.append(safety == case["expected_safety"])
        results.append({"synthetic_text": case["text"], "parsed": parsed, "safety_status": safety, "pass": all(checks), "learning_route_permitted": safety in ("ROUTINE", "URGENT") and not parsed["needs_clarification"]})
    return {"status": "complete", "passed": sum(r["pass"] for r in results), "count": len(results), "cases": results, "claim_scope": "synthetic lexical and Safety boundary checks, not Chinese clinical department accuracy"}


def main():
    TARGET.mkdir(parents=True, exist_ok=True)
    with study_lock(TARGET / "run.lock"), threadpool_limits(limits=2):
        original = load_expanded().rows
        vocabulary = sorted({code for row in load_structured().rows for code in row["symptoms"]})
        mapped, excluded = [], Counter()
        for row in original:
            symptoms = extract_english(mask_row(row)["symptoms"], vocabulary)
            if symptoms:
                mapped.append({**row, "symptoms": symptoms})
            else:
                excluded[row["source"]] += 1
        fingerprints = defaultdict(Counter)
        for row in mapped:
            fingerprints[tuple(row["symptoms"])][labels([row])[0]] += 1
        inventory = {"original_rows": len(original), "retained_rows": len(mapped), "excluded_no_concept": dict(excluded), "vocabulary_size": len(vocabulary), "explicit_dictionary": "pre-existing structured code schema, uses no disease labels", "ambiguous_fingerprints": sum(len(c) > 1 for c in fingerprints.values()), "fingerprint_count": len(fingerprints), "observed_duplicate_label_majority_ceiling": sum(max(c.values()) for c in fingerprints.values()) / len(mapped), "scope": "lexical ontology experiment; free text paragraphs remain weak evidence, no expert annotations"}
        atomic_json(TARGET / "inventory.json", inventory)
        for seed in SEEDS:
            train, cal, test, meta = global_split(mapped, seed, .8)
            for rep in ("binary", "word", "segmented_char"):
                path = TARGET / f"{seed}-{rep}.json"
                if path.exists():
                    continue
                inner, _, validation, _ = quota_split(train, seed=seed + 1000, train_frac=.7, cal_frac=.1)
                if not cal or not test or not validation:
                    atomic_json(path, {"status": "unsupported", "sizes": [len(train), len(cal), len(test)], "reason": "insufficient grouped coverage"})
                    continue
                winner, candidates = select_candidate(inner, validation, rep, seed)
                vector, model = representation(rep), estimator(winner["config"], seed)
                model.fit(vector.fit_transform(train), labels(train))
                unseen = (set(labels(cal)) | set(labels(test))) - set(model.classes_)
                if unseen:
                    atomic_json(path, {"status": "unsupported", "reason": "unseen departments", "departments": sorted(unseen)})
                    continue
                temperature = fit_temperature(model_logits(model, vector.transform(cal)), labels(cal), model.classes_)
                p = softmax(model_logits(model, vector.transform(test)) / temperature, axis=1)
                result = {"status": "complete", "seed": seed, "representation": rep, "winner": winner, "candidate_records": candidates, "temperature": temperature, "metrics": metrics(labels(test), p, model.classes_), "split": meta, "sizes": [len(train), len(cal), len(test)], "leakage": cross_split_leakage_audit(train, test, .8)}
                atomic_json(path, result)
                print(f"DONE bridge {seed} {rep} acc={result['metrics']['accuracy']:.4f}", flush=True)
        challenge = chinese_challenge()
        atomic_json(TARGET / "chinese-challenge.json", challenge)
        print(f"CHINESE engineering cases {challenge['passed']}/{challenge['count']}", flush=True)
        atomic_json(TARGET / "state.json", {"status": "complete", "model_jobs": 15, "chinese_cases": challenge['count']})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
