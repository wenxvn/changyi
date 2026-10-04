"""Disease-name shortcut audit, label masking, text-template group sensitivity."""
from __future__ import annotations
import json
import random
import re
from collections import Counter, defaultdict

import numpy as np
from scipy.special import softmax
from sklearn.feature_extraction.text import TfidfVectorizer
from threadpoolctl import threadpool_limits

from evaluation.care_routing.round3_split_audit import load_expanded, quota_split, load_structured, cross_split_leakage_audit
from evaluation.care_routing.disease_department import DISEASE_TO_DEPARTMENT
from .study import OUT, SEEDS, atomic_json, labels, metrics, model_logits, study_lock
from .generalization import inner_selected, frozen_refit
from .persistence import load_study_model

TARGET = OUT.parent / "data-audit-v1"
NAMES = sorted(DISEASE_TO_DEPARTMENT, key=len, reverse=True)
PATTERNS = [(name, re.compile(r"(?<!\w)" + re.escape(name.lower().replace("_", " ")) + r"(?!\w)")) for name in NAMES]


def normal_text(row):
    return " ; ".join(row["symptoms"]).replace("_", " ").lower()


def mention_names(row):
    text = normal_text(row)
    return [name for name, pattern in PATTERNS if pattern.search(text)]


def mask_row(row):
    changed = []
    for code in row["symptoms"]:
        text = code.replace("_", " ").lower()
        for _, pattern in PATTERNS:
            text = pattern.sub("diagnosis redacted", text)
        changed.append(text.replace(" ", "_"))
    return {**row, "symptoms": changed}


def text_components(rows, threshold):
    # This vectorizer defines grouping only. Every predictive representation is
    # fitted independently on its training rows; grouping is label blind.
    text = [normal_text(row) for row in rows]
    vector = TfidfVectorizer(analyzer="char", ngram_range=(3, 5), sublinear_tf=True)
    x = vector.fit_transform(text)
    similarities = (x @ x.T).tocoo()
    parent = list(range(len(rows)))
    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    for left, right, value in zip(similarities.row, similarities.col, similarities.data):
        if left < right and value >= threshold:
            a, b = find(int(left)), find(int(right))
            if a != b:
                parent[b] = a
    groups = defaultdict(list)
    for i in range(len(rows)):
        groups[find(i)].append(i)
    return list(groups.values()), x


def component_split(rows, groups, seed):
    by_dept = defaultdict(list)
    for group in groups:
        dominant = Counter(labels([rows[i] for i in group])).most_common(1)[0][0]
        by_dept[dominant].append(group)
    rng = random.Random(seed)
    train_idx, cal_idx, test_idx = [], [], []
    for dept in sorted(by_dept):
        group_list = by_dept[dept][:]
        rng.shuffle(group_list)
        n = len(group_list)
        if n < 3:
            train_idx.extend(i for group in group_list for i in group)
            continue
        n_test, n_cal = max(1, round(.2 * n)), max(1, round(.2 * n))
        n_train = max(1, n - n_test - n_cal)
        train_idx.extend(i for group in group_list[:n_train] for i in group)
        cal_idx.extend(i for group in group_list[n_train:n_train+n_cal] for i in group)
        test_idx.extend(i for group in group_list[n_train+n_cal:] for i in group)
    return ([rows[i] for i in train_idx], [rows[i] for i in cal_idx], [rows[i] for i in test_idx]), (train_idx, cal_idx, test_idx)


def original_split_ablation(rows, seed):
    selected = inner_selected(seed)
    state = load_study_model(OUT / f"{seed}-{selected['representation']}.joblib")
    train, cal, test, _ = quota_split(rows, seed=seed)
    model, vector, temperature = state["model"], state["vector"], state["temperature"]
    p = softmax(model_logits(model, vector.transform(test)) / temperature, axis=1)
    p_mask = softmax(model_logits(model, vector.transform([mask_row(r) for r in test])) / temperature, axis=1)
    mention = np.array([bool(mention_names(r)) for r in test])
    result = {"seed": seed, "representation": selected["representation"], "original": metrics(labels(test), p, model.classes_), "mask_test_only": metrics(labels(test), p_mask, model.classes_), "named_disease_test_rows": int(mention.sum()), "interpretation": "test-only intervention measures diagnostic-name reliance; not an independent clinical benchmark"}
    for name, mask in (("diagnosis_mentioned", mention), ("no_exact_disease_name", ~mention)):
        if mask.any():
            result[name] = metrics(labels(test)[mask], p[mask], model.classes_)
    masked_train, masked_cal, masked_test = [list(map(mask_row, part)) for part in (train, cal, test)]
    result["mask_train_cal_test_refit"] = frozen_refit(masked_train, masked_cal, masked_test, selected)
    result["mask_refit_leakage"] = cross_split_leakage_audit(masked_train, masked_test, .8)
    result["mask_refit_limit"] = "original partition retained for intervention comparison; masking can create new duplicates, audit reported"
    return result


def main():
    TARGET.mkdir(parents=True, exist_ok=True)
    with study_lock(TARGET / "run.lock"), threadpool_limits(limits=2):
        rows = load_expanded().rows
        atomic_json(TARGET / "inventory.json", {"rows": len(rows), "by_source": {source: {"rows": sum(r["source"] == source for r in rows), "disease_name_present": sum(bool(mention_names(r)) for r in rows if r["source"] == source), "own_label_present": sum(r["disease"] in mention_names(r) for r in rows if r["source"] == source), "has_code_longer_than_80chars": sum(any(len(code) > 80 for code in r["symptoms"]) for r in rows if r["source"] == source)} for source in ("structured_41", "training_long_extra")}, "mapping_limit": "exact dictionary names only; synonyms, spelling variants and implicit diagnosis not counted"})
        for seed in SEEDS:
            path = TARGET / f"{seed}-mask.json"
            if not path.exists():
                atomic_json(path, original_split_ablation(rows, seed))
        # Text cosine sensitivity on label-masked rows, not on disease names.
        masked = [mask_row(r) for r in rows]
        for threshold in (.7, .8, .9):
            groups, features = text_components(masked, threshold)
            for seed in SEEDS:
                path = TARGET / f"{seed}-textcos-{threshold}.json"
                if path.exists():
                    continue
                (train, cal, test), (train_idx, _, test_idx) = component_split(masked, groups, seed)
                result = frozen_refit(train, cal, test, inner_selected(seed))
                cross = features[train_idx] @ features[test_idx].T
                max_cos = float(cross.max()) if train_idx and test_idx else None
                result.update({"seed": seed, "threshold": threshold, "sizes": {"train": len(train), "cal": len(cal), "test": len(test)}, "component_count": len(groups), "largest_component": max(map(len, groups)), "max_cross_split_cosine": max_cos, "guard_pass": max_cos is None or max_cos < threshold + 1e-9, "scope": "label-masked text-template sensitivity; no clinical semantics guarantee"})
                atomic_json(path, result)
                print(f"DONE cosine {threshold} {seed} {result['status']} n_test={len(test)}", flush=True)
        structured = load_structured().rows
        for seed in SEEDS:
            path = TARGET / f"{seed}-structured-only.json"
            if path.exists():
                continue
            train, cal, test, meta = quota_split(structured, seed=seed)
            result = frozen_refit(train, cal, test, inner_selected(seed))
            result.update({"split": meta, "limitation": "frozen mixed-cohort config, small symptom-only test; not tuned to improve this test"})
            atomic_json(path, result)
        atomic_json(TARGET / "state.json", {"status": "complete", "mask_jobs": 5, "text_group_jobs": 15, "structured_only_jobs": 5})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
