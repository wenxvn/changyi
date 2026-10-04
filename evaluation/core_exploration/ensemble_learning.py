"""Finite learning-curve/ensemble controls, with calibration-only mixture weights."""
from __future__ import annotations
import json
import random
from collections import defaultdict

import numpy as np
from scipy.optimize import minimize
from scipy.special import softmax
from threadpoolctl import threadpool_limits

from .study import OUT, SEEDS, REPRESENTATIONS, atomic_json, labels, estimator, representation, model_logits, metrics, fit_temperature, split_calibration, selective_curves, study_lock
from .generalization import inner_selected
from .persistence import load_study_model
from .validation import expanded_metrics
from evaluation.care_routing.round3_split_audit import load_expanded, quota_split
from evaluation.model.evaluate_grouped import near_duplicate_components

TARGET = OUT.parent / "ensemble-learning-v1"


def learning(seed, train, cal, test):
    selected = inner_selected(seed)
    components, _ = near_duplicate_components(train, mode="global", threshold=.8)
    by_dept = defaultdict(list)
    for group in components:
        by_dept[labels([train[group[0]]])[0]].append(group)
    rng = random.Random(seed)
    for group_list in by_dept.values():
        rng.shuffle(group_list)
    records = []
    for fraction in (.2, .4, .6, .8, 1.):
        subset = []
        for dept in sorted(by_dept):
            groups = by_dept[dept]
            subset.extend(train[i] for group in groups[:max(1, round(len(groups) * fraction))] for i in group)
        model, vector = estimator(selected["winner"]["config"], seed), representation(selected["representation"])
        model.fit(vector.fit_transform(subset), labels(subset))
        temperature = fit_temperature(model_logits(model, vector.transform(cal)), labels(cal), model.classes_)
        probabilities = softmax(model_logits(model, vector.transform(test)) / temperature, axis=1)
        records.append({"fraction_of_train_groups": fraction, "actual_train_rows": len(subset), "temperature": temperature, "metrics": expanded_metrics(labels(test), probabilities, model.classes_)})
    return {"status": "complete", "seed": seed, "representation": selected["representation"], "config": selected["winner"]["config"], "records": records, "selection": "fixed full-train inner winner, never test-tuned for learning curve"}


def ensemble(seed, cal, test):
    jobs = [json.loads((OUT / f"{seed}-{rep}.json").read_text(encoding="utf-8")) for rep in REPRESENTATIONS]
    order = sorted(range(len(jobs)), key=lambda i: (jobs[i]["winner"]["macro_f1"], jobs[i]["winner"]["accuracy"]), reverse=True)
    fit_cal, threshold_cal = split_calibration(cal, seed)
    fit_probs, threshold_probs, test_probs = [], [], []
    classes = None
    for job in jobs:
        state = load_study_model(OUT / f"{seed}-{job['representation']}.joblib")
        model, vector, temperature = state["model"], state["vector"], state["temperature"]
        if classes is not None and not np.array_equal(classes, model.classes_):
            raise AssertionError("ensemble classes must align exactly")
        classes = model.classes_
        fit_probs.append(softmax(model_logits(model, vector.transform(fit_cal)) / temperature, axis=1))
        threshold_probs.append(softmax(model_logits(model, vector.transform(threshold_cal)) / temperature, axis=1))
        test_probs.append(softmax(model_logits(model, vector.transform(test)) / temperature, axis=1))
    fit_probs, threshold_probs, test_probs = map(np.asarray, (fit_probs, threshold_probs, test_probs))
    y_fit, y_test = labels(fit_cal), labels(test)
    target = np.array([{name: i for i, name in enumerate(classes)}[name] for name in y_fit])
    all_uniform = np.full(len(jobs), 1 / len(jobs))
    top_uniform = np.zeros(len(jobs))
    top_uniform[order[:3]] = 1 / 3
    def loss(weights):
        p = np.tensordot(weights, fit_probs, axes=1)
        return float(-np.log(np.clip(p[np.arange(len(target)), target], 1e-12, 1)).mean())
    optimized = minimize(loss, top_uniform, method="SLSQP", bounds=[(0, 1)] * len(jobs), constraints=[{"type": "eq", "fun": lambda weights: weights.sum() - 1}], options={"maxiter": 300, "ftol": 1e-9})
    results = []
    for name, weights in (("all8_uniform", all_uniform), ("top3_inner_uniform", top_uniform), ("cal_nll_weights", optimized.x)):
        if name == "cal_nll_weights" and not optimized.success:
            results.append({"method": name, "status": "failed", "error": optimized.message})
            continue
        p_test = np.tensordot(weights, test_probs, axes=1)
        p_threshold = np.tensordot(weights, threshold_probs, axes=1)
        evaluated = metrics(y_test, p_test, classes)
        curves = selective_curves(y_test, p_test, p_threshold, classes)
        if curves["max_probability"][0]["accuracy"] != evaluated["accuracy"]:
            raise AssertionError("full coverage must equal composite predictor accuracy")
        results.append({"method": name, "status": "complete", "weights": weights.tolist(), "metrics": evaluated, "selective": curves, "fit_cal_nll": loss(weights)})
    return {"status": "complete", "seed": seed, "representations": list(REPRESENTATIONS), "results": results, "cal_fit": len(fit_cal), "threshold_cal": len(threshold_cal), "policy": "train-inner chooses top3; cal_fit only optimizes weights; threshold_cal/test never fit weights"}


def main():
    TARGET.mkdir(parents=True, exist_ok=True)
    with study_lock(TARGET / "run.lock"), threadpool_limits(limits=2):
        rows = load_expanded().rows
        for seed in SEEDS:
            train, cal, test, _ = quota_split(rows, seed=seed)
            for name, call in (("learning", lambda: learning(seed, train, cal, test)), ("ensemble", lambda: ensemble(seed, cal, test))):
                path = TARGET / f"{seed}-{name}.json"
                if not path.exists():
                    atomic_json(path, call())
                print(f"DONE {name} {seed}", flush=True)
        atomic_json(TARGET / "state.json", {"status": "complete", "learning_points": 25, "ensemble_settings": 15})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
