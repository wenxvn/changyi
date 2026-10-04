"""Frozen inner-selected pipelines under stricter groups, source transfer, stress."""
from __future__ import annotations
import json
import random
from collections import defaultdict
from pathlib import Path

import joblib
import numpy as np
from scipy.special import softmax
from threadpoolctl import threadpool_limits

from evaluation.model.evaluate_grouped import near_duplicate_components, jaccard
from evaluation.care_routing.round3_split_audit import load_expanded, quota_split, cross_split_leakage_audit
from .study import OUT, SEEDS, REPRESENTATIONS, atomic_json, labels, representation, estimator, model_logits, metrics, fit_temperature, study_lock
from .persistence import load_study_model

TARGET = OUT.parent / "generalization-v1"


def inner_selected(seed):
    jobs = [json.loads((OUT / f"{seed}-{rep}.json").read_text(encoding="utf-8")) for rep in REPRESENTATIONS]
    return max(jobs, key=lambda r: (r["winner"]["macro_f1"], r["winner"]["accuracy"]))


def global_split(rows, seed, threshold):
    groups, group_stats = near_duplicate_components(list(rows), mode="global", threshold=threshold)
    by_dept = defaultdict(list)
    for group in groups:
        by_dept[labels([rows[group[0]]])[0]].append(group)
    rng = random.Random(seed)
    train, cal, test = [], [], []
    for dept in sorted(by_dept):
        comps = by_dept[dept]
        rng.shuffle(comps)
        if len(comps) < 3:
            train.extend(rows[i] for g in comps for i in g)
            continue
        n_cal, n_test = max(1, round(len(comps) * .2)), max(1, round(len(comps) * .2))
        n_train = max(1, len(comps) - n_cal - n_test)
        train.extend(rows[i] for g in comps[:n_train] for i in g)
        cal.extend(rows[i] for g in comps[n_train:n_train+n_cal] for i in g)
        test.extend(rows[i] for g in comps[n_train+n_cal:] for i in g)
    return train, cal, test, {"threshold": threshold, "mode": "global", "component_stats": group_stats}


def frozen_refit(train, cal, test, selected):
    if not cal or not test:
        return {"status": "unsupported", "reason": "empty cal/test after leakage guard"}
    model, vector = estimator(selected["winner"]["config"], selected["seed"]), representation(selected["representation"])
    model.fit(vector.fit_transform(train), labels(train))
    unknown_labels = sorted((set(labels(cal)) | set(labels(test))) - set(model.classes_))
    if unknown_labels:
        return {"status": "unsupported", "reason": "labels absent from training", "unseen_departments": unknown_labels}
    temperature = fit_temperature(model_logits(model, vector.transform(cal)), labels(cal), model.classes_)
    p = softmax(model_logits(model, vector.transform(test)) / temperature, axis=1)
    return {"status": "complete", "frozen_config": selected["winner"]["config"], "representation": selected["representation"], "temperature": temperature, "metrics": metrics(labels(test), p, model.classes_)}


def source_split(rows, train_source, seed):
    train = [r for r in rows if r["source"] == train_source]
    other = [r for r in rows if r["source"] != train_source]
    # Global guard against the source-training set before any split/model fit.
    sets = [set(r["symptoms"]) for r in train]
    clean = [r for r in other if all(jaccard(set(r["symptoms"]), s) < .8 for s in sets)]
    cal, _, test, meta = quota_split(clean, seed=seed, train_frac=.4, cal_frac=.1)
    return train, cal, test, {"train_source": train_source, "other_rows": len(other), "removed_near_duplicate": len(other) - len(clean), "source_holdout_meta": meta}


def stress(seed, selected, test):
    state = load_study_model(OUT / f"{seed}-{selected['representation']}.joblib")
    model, vector, temperature = state["model"], state["vector"], state["temperature"]
    clean_logits = model_logits(model, vector.transform(test))
    clean = metrics(labels(test), softmax(clean_logits / temperature, axis=1), model.classes_)
    rng = random.Random(seed)
    results = {}
    for kind in ("identity", "shuffle", "duplicate", "drop_one", "add_unknown", "empty", "fully_unknown"):
        perturbed = []
        for row in test:
            symptoms = row["symptoms"][:]
            if kind == "shuffle":
                rng.shuffle(symptoms)
            elif kind == "duplicate":
                symptoms += symptoms[:1]
            elif kind == "drop_one" and len(symptoms) > 1:
                symptoms.pop(rng.randrange(len(symptoms)))
            elif kind == "add_unknown":
                symptoms += ["qzxv_unsupported_input_9"]
            elif kind == "empty":
                symptoms = []
            elif kind == "fully_unknown":
                symptoms = ["qzxv_9", "zxqv_8"]
            perturbed.append({**row, "symptoms": symptoms})
        features = vector.transform(perturbed)
        logits = model_logits(model, features)
        p = softmax(logits / temperature, axis=1)
        empty = np.asarray(features.getnnz(axis=1) == 0).ravel()
        if kind in ("empty", "fully_unknown"):
            # True department undefined after removing all symptom information.
            results[kind] = {"label_valid": False, "feature_empty_rate": float(empty.mean()), "mean_model_confidence": float(p.max(axis=1).mean()), "max_model_confidence": float(p.max()), "zero_feature_abstention_policy_rate": float(empty.mean())}
        else:
            evaluated = metrics(labels(test), p, model.classes_)
            results[kind] = {"metrics": evaluated, "accuracy_delta": evaluated["accuracy"] - clean["accuracy"], "max_logit_delta": float(np.abs(logits - clean_logits).max()), "label_valid": kind in ("identity", "shuffle", "duplicate"), "scope": "symptom deletion/addition not guaranteed medically label-preserving"}
    return {"status": "complete", "selection": "inner validation only", "representation": selected["representation"], "clean": clean, "stress": results}


def main():
    TARGET.mkdir(parents=True, exist_ok=True)
    with study_lock(TARGET / "run.lock"), threadpool_limits(limits=2):
        rows = load_expanded().rows
        for seed in SEEDS:
            selected = inner_selected(seed)
            _, _, test, _ = quota_split(rows, seed=seed)
            stress_path = TARGET / f"{seed}-stress.json"
            if not stress_path.exists():
                atomic_json(stress_path, stress(seed, selected, test))
            for threshold in (.7, .75, .8, .85):
                path = TARGET / f"{seed}-global-{threshold}.json"
                if path.exists():
                    continue
                train, cal, test, meta = global_split(rows, seed, threshold)
                evaluated = frozen_refit(train, cal, test, selected)
                evaluated.update({"seed": seed, "split": meta, "sizes": {"train": len(train), "cal": len(cal), "test": len(test)}, "leakage": cross_split_leakage_audit(train, test, threshold), "comparison_limit": "changed groups/test coverage; not head-to-head accuracy gain"})
                atomic_json(path, evaluated)
                print(f"DONE global {seed} {threshold} {evaluated['status']}", flush=True)
            for source in ("structured_41", "training_long_extra"):
                path = TARGET / f"{seed}-source-{source}.json"
                if path.exists():
                    continue
                train, cal, test, meta = source_split(rows, source, seed)
                evaluated = frozen_refit(train, cal, test, selected)
                evaluated.update({"seed": seed, "split": meta, "sizes": {"train": len(train), "cal": len(cal), "test": len(test)}, "leakage": cross_split_leakage_audit(train, test, .8)})
                atomic_json(path, evaluated)
                print(f"DONE source {seed} {source} {evaluated['status']}", flush=True)
        atomic_json(TARGET / "state.json", {"status": "complete", "global_jobs": 20, "source_jobs": 10, "stress_jobs": 5})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
