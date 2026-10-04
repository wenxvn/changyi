"""Full symptom-only grouped CV, permutation controls, portable research models."""
from __future__ import annotations
import json
from collections import defaultdict

import joblib
import numpy as np
from scipy.special import softmax
from sklearn.model_selection import GroupKFold
from threadpoolctl import threadpool_limits

from .study import OUT, SEEDS, atomic_json, labels, representation, estimator, model_logits, metrics, fit_temperature, study_lock
from .generalization import inner_selected
from .persistence import load_study_model
from evaluation.model.evaluate_grouped import near_duplicate_components
from evaluation.care_routing.round3_split_audit import load_structured, load_expanded, quota_split

TARGET = OUT.parent / "validation-v1"


def expanded_metrics(y, probabilities, classes):
    """Unseen training labels stay in the denominator, rather than disappear."""
    all_classes = sorted(set(classes) | set(y))
    full = np.full((len(y), len(all_classes)), 1e-12)
    lookup = {name: i for i, name in enumerate(all_classes)}
    for i, name in enumerate(classes):
        full[:, lookup[name]] = probabilities[:, i]
    full /= full.sum(axis=1, keepdims=True)
    result = metrics(y, full, np.asarray(all_classes))
    result["unseen_department_rows"] = sum(name not in set(classes) for name in y)
    return result


def symptom_cv():
    rows = load_structured().rows
    components, meta = near_duplicate_components(rows, mode="global", threshold=.8)
    group_ids = np.zeros(len(rows), dtype=int)
    for group, indices in enumerate(components):
        group_ids[indices] = group
    records = []
    for fold, (train_idx, test_idx) in enumerate(GroupKFold(n_splits=5).split(rows, groups=group_ids)):
        train, test = [rows[i] for i in train_idx], [rows[i] for i in test_idx]
        for rep in ("binary", "word", "segmented_char"):
            # This all-row coverage stress uses fixed config, not its test fold
            # to tune. No cal slice is manufactured from the evaluation fold.
            config = {"family": "lr", "C": 10., "balanced": True}
            vector, model = representation(rep), estimator(config, 42)
            model.fit(vector.fit_transform(train), labels(train))
            p = softmax(model_logits(model, vector.transform(test)), axis=1)
            records.append({"fold": fold, "representation": rep, "train": len(train), "test": len(test), "metrics": expanded_metrics(labels(test), p, model.classes_), "scope": "all structured rows evaluated once; no test tuning/calibration; unsupported class errors retained"})
    return {"status": "complete", "rows": len(rows), "component_stats": meta, "records": records}


def negative_control(seed):
    selected = inner_selected(seed)
    train, cal, test, _ = quota_split(load_expanded().rows, seed=seed)
    y = labels(train)
    y = np.random.default_rng(seed + 8000).permutation(y)
    vector, model = representation(selected["representation"]), estimator(selected["winner"]["config"], seed)
    model.fit(vector.fit_transform(train), y)
    temperature = fit_temperature(model_logits(model, vector.transform(cal)), labels(cal), model.classes_)
    p = softmax(model_logits(model, vector.transform(test)) / temperature, axis=1)
    return {"status": "complete", "seed": seed, "metrics": metrics(labels(test), p, model.classes_), "scope": "train labels shuffled, true cal/test unchanged; no test fitting", "expected": "performance should collapse toward class-prior baseline, not retain main headline"}


def main():
    TARGET.mkdir(parents=True, exist_ok=True)
    with study_lock(TARGET / "run.lock"), threadpool_limits(limits=2):
        if not (TARGET / "structured-full-cv.json").exists():
            atomic_json(TARGET / "structured-full-cv.json", symptom_cv())
        for seed in SEEDS:
            path = TARGET / f"{seed}-permuted.json"
            if not path.exists():
                atomic_json(path, negative_control(seed))
            selected = inner_selected(seed)
            original = load_study_model(OUT / f"{seed}-{selected['representation']}.joblib")
            portable = TARGET / f"{seed}-portable.joblib"
            joblib.dump(original, portable)
            replay = joblib.load(portable)
            _, _, test, _ = quota_split(load_expanded().rows, seed=seed)
            before = model_logits(original["model"], original["vector"].transform(test))
            after = model_logits(replay["model"], replay["vector"].transform(test))
            if not np.array_equal(before, after):
                raise AssertionError("serialization changed predictions")
            atomic_json(TARGET / f"{seed}-portable.json", {"status": "complete", "model_file": str(portable), "identity": original["identity"], "representation": selected["representation"], "exact_prediction_replay": True, "selection": "inner validation only"})
            print(f"DONE validation {seed}", flush=True)
        atomic_json(TARGET / "state.json", {"status": "complete", "structured_cv_fits": 15, "permutation_fits": 5, "portable_models": 5})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
