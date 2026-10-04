"""Pre-registered nested model/representation/calibration study.

Run: python -m evaluation.core_exploration.study
One completed outer job per representation/seed, atomic files and a process lock.
Outer test is never an argument to select_candidate or fit_calibration.
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import math
import os
import random
import time
import warnings
from collections import defaultdict
from pathlib import Path

import joblib
import numpy as np
import scipy
import sklearn
from scipy.optimize import minimize_scalar
from scipy.special import softmax
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.feature_extraction import DictVectorizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import accuracy_score, f1_score, log_loss
from sklearn.naive_bayes import ComplementNB, MultinomialNB
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.preprocessing import FunctionTransformer, Normalizer
from sklearn.svm import LinearSVC
from threadpoolctl import threadpool_limits

from evaluation.care_routing.disease_department import department_for
from evaluation.care_routing.round3_split_audit import load_expanded, quota_split, cross_split_leakage_audit
from evaluation.model.evaluate_grouped import near_duplicate_components, symptom_fingerprint

OUT = Path(__file__).parent / "results" / "study-v2"
SEEDS = (42, 123, 2026, 3407, 7777)
REPRESENTATIONS = ("binary", "word", "concat_char", "canonical_char", "segmented_char", "fusion_25", "fusion_50", "fusion_75")


def atomic_json(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + f".{os.getpid()}.tmp")
    temporary.write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def digest(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


@contextlib.contextmanager
def study_lock(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+b") as handle:
        handle.seek(0)
        if handle.read(1) == b"":
            handle.write(b"0")
            handle.flush()
        handle.seek(0)
        if os.name == "nt":
            import msvcrt
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            yield
        finally:
            handle.seek(0)
            if os.name == "nt":
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle, fcntl.LOCK_UN)


def binary_docs(rows):
    return [{code: 1.0 for code in set(row["symptoms"])} for row in rows]


def word_docs(rows):
    return [" ".join(sorted(set(row["symptoms"]))) for row in rows]


def concat_docs(rows):
    return ["".join(code.replace("_", "") for code in row["symptoms"]) for row in rows]


def canonical_docs(rows):
    return [" | ".join(sorted(set(row["symptoms"]))) for row in rows]


def segmented_tokens(row):
    tokens = []
    for code in sorted(set(row["symptoms"])):
        dense = code.replace("_", "")
        for n in (2, 3, 4):
            tokens.extend(f"c{n}:{dense[i:i+n]}" for i in range(max(0, len(dense) - n + 1)))
    return tokens


def representation(name):
    word = Pipeline([("text", FunctionTransformer(word_docs)), ("tfidf", TfidfVectorizer(token_pattern=r"(?u)\b\w+\b", sublinear_tf=True))])
    segmented = TfidfVectorizer(analyzer=segmented_tokens, sublinear_tf=True)
    if name == "binary":
        return Pipeline([("text", FunctionTransformer(binary_docs)), ("vector", DictVectorizer()), ("norm", Normalizer())])
    if name == "word":
        return word
    if name in ("concat_char", "canonical_char"):
        return Pipeline([("text", FunctionTransformer(concat_docs if name == "concat_char" else canonical_docs)), ("tfidf", TfidfVectorizer(analyzer="char", ngram_range=(2, 4), sublinear_tf=True))])
    if name == "segmented_char":
        return segmented
    if name.startswith("fusion_"):
        char_weight = int(name.split("_")[1]) / 100
        return Pipeline([("fusion", FeatureUnion([("word", word), ("char", segmented)], transformer_weights={"word": 1 - char_weight, "char": char_weight})), ("norm", Normalizer())])
    raise ValueError(name)


def candidate_grid():
    candidates = []
    for family in ("lr", "svm"):
        for c in (0.1, 1.0, 10.0, 100.0):
            for balance in (False, True):
                candidates.append({"family": family, "C": c, "balanced": balance})
    candidates += [{"family": "complement_nb", "alpha": a} for a in (0.1, 1.0)]
    candidates += [{"family": "multinomial_nb", "alpha": a} for a in (0.1, 1.0)]
    candidates += [{"family": "extra_trees", "balanced": True, "max_depth": depth} for depth in (8, None)]
    return candidates


def estimator(config, seed):
    family = config["family"]
    weight = "balanced" if config.get("balanced") else None
    if family == "lr":
        return LogisticRegression(C=config["C"], class_weight=weight, max_iter=1500, random_state=seed)
    if family == "svm":
        return LinearSVC(C=config["C"], class_weight=weight, max_iter=4000, random_state=seed)
    if family == "extra_trees":
        return ExtraTreesClassifier(n_estimators=96, max_depth=config["max_depth"], class_weight=weight, n_jobs=1, random_state=seed)
    return (ComplementNB if family == "complement_nb" else MultinomialNB)(alpha=config["alpha"])


def labels(rows):
    return np.array([department_for(r["disease"]) for r in rows])


def select_candidate(inner_train, validation, rep, seed):
    vector = representation(rep)
    x_train = vector.fit_transform(inner_train)
    x_val = vector.transform(validation)
    y_train, y_val = labels(inner_train), labels(validation)
    records = []
    for config in candidate_grid():
        started = time.monotonic()
        try:
            model = estimator(config, seed)
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                model.fit(x_train, y_train)
            predicted = model.predict(x_val)
            records.append({"config": config, "status": "complete", "macro_f1": float(f1_score(y_val, predicted, average="macro", zero_division=0)), "accuracy": float(accuracy_score(y_val, predicted)), "seconds": time.monotonic() - started, "warnings": [str(w.message) for w in caught]})
        except Exception as error:
            records.append({"config": config, "status": "failed", "error": repr(error), "seconds": time.monotonic() - started})
    completed = [r for r in records if r["status"] == "complete"]
    if not completed:
        raise RuntimeError("all candidates failed")
    # Selection uses validation only. Outer test has never been supplied here.
    winner = max(completed, key=lambda r: (r["macro_f1"], r["accuracy"]))
    return winner, records


def split_calibration(cal, seed):
    components, _ = near_duplicate_components(list(cal), mode="global", threshold=0.8)
    by_dept = defaultdict(list)
    for group in components:
        by_dept[department_for(cal[group[0]]["disease"])].append(group)
    rng = random.Random(seed)
    fit_indices, threshold_indices = [], []
    for dept in sorted(by_dept):
        groups = by_dept[dept]
        rng.shuffle(groups)
        cut = max(1, len(groups) // 2)
        fit_indices.extend(i for g in groups[:cut] for i in g)
        threshold_indices.extend(i for g in groups[cut:] for i in g)
    return [cal[i] for i in fit_indices], [cal[i] for i in threshold_indices]


def model_logits(model, features):
    if hasattr(model, "decision_function"):
        logits = model.decision_function(features)
        if logits.ndim == 1:
            logits = np.stack([-logits, logits], axis=1)
        return np.asarray(logits)
    return np.log(np.clip(model.predict_proba(features), 1e-12, 1))


def target_indices(y, classes):
    lookup = {label: index for index, label in enumerate(classes)}
    return np.array([lookup[label] for label in y], dtype=int)


def fit_temperature(logits, y, classes):
    target = target_indices(y, classes)
    def loss(log_t):
        probabilities = softmax(logits / math.exp(log_t), axis=1)
        return -np.log(np.clip(probabilities[np.arange(len(y)), target], 1e-12, 1)).mean()
    opt = minimize_scalar(loss, bounds=(-3, 3), method="bounded")
    return math.exp(float(opt.x))


def metrics(y, probabilities, classes):
    predicted = np.asarray(classes)[probabilities.argmax(axis=1)]
    confidence = probabilities.max(axis=1)
    correctness = predicted == y
    ece = 0.0
    bins = []
    for i in range(10):
        mask = (confidence >= i / 10) & (confidence <= 1 if i == 9 else confidence < (i + 1) / 10)
        if mask.any():
            bins.append({"bin": i, "n": int(mask.sum()), "confidence": float(confidence[mask].mean()), "accuracy": float(correctness[mask].mean())})
            ece += mask.mean() * abs(confidence[mask].mean() - correctness[mask].mean())
    target = target_indices(y, classes)
    one_hot = np.eye(len(classes))[target]
    per_dept = {}
    for dept in classes:
        mask = y == dept
        per_dept[str(dept)] = {"support": int(mask.sum()), "recall": float((predicted[mask] == dept).mean()) if mask.any() else None}
    rng = np.random.default_rng(1907)
    sampled = correctness[rng.integers(0, len(y), size=(400, len(y)))].mean(axis=1)
    return {"n": len(y), "accuracy": float(correctness.mean()), "macro_f1": float(f1_score(y, predicted, average="macro", zero_division=0)), "nll": float(-np.log(np.clip(probabilities[np.arange(len(y)), target], 1e-12, 1)).mean()), "brier": float(np.square(probabilities - one_hot).sum(axis=1).mean()), "ece": float(ece), "wrong_confident_07": float(((~correctness) & (confidence >= .7)).mean()), "per_department": per_dept, "reliability": bins, "accuracy_row_bootstrap_95ci": np.quantile(sampled, [.025, .975]).tolist(), "ci_limitation": "row bootstrap, dependent template rows may narrow interval"}


def signal_scores(p, signal):
    if signal == "max_probability":
        return p.max(axis=1)
    if signal == "margin":
        ordered = np.sort(p, axis=1)
        return ordered[:, -1] - ordered[:, -2]
    return (p * np.log(np.clip(p, 1e-12, 1))).sum(axis=1)


def selective_curves(y, p_test, p_threshold, classes):
    curves = {}
    predicted = np.asarray(classes)[p_test.argmax(axis=1)]
    for signal in ("max_probability", "margin", "neg_entropy"):
        cal_scores, scores = signal_scores(p_threshold, signal), signal_scores(p_test, signal)
        points = []
        for coverage in (1., .9, .8, .7, .6, .5):
            threshold = float(np.quantile(cal_scores, 1 - coverage)) if coverage < 1 else None
            keep = scores >= threshold if threshold is not None else np.ones(len(y), dtype=bool)
            per_dept = {str(d): {"support": int((y == d).sum()), "retained": int(((y == d) & keep).sum()), "coverage": float(keep[y == d].mean()) if (y == d).any() else None} for d in classes}
            points.append({"target_coverage": coverage, "threshold": threshold, "coverage": float(keep.mean()), "retained": int(keep.sum()), "accuracy": float((predicted[keep] == y[keep]).mean()) if keep.any() else None, "error_rate": float((predicted[keep] != y[keep]).mean()) if keep.any() else None, "per_department": per_dept})
        curves[signal] = points
    return curves


def conformal_sets(y, p_test, y_threshold, p_threshold, classes):
    target = target_indices(y_threshold, classes)
    scores = 1 - p_threshold[np.arange(len(target)), target]
    output = []
    for alpha in (.05, .1, .2):
        quantile = min(1., math.ceil((len(scores) + 1) * (1 - alpha)) / len(scores))
        threshold = np.quantile(scores, quantile, method="higher")
        sets = (1 - p_test) <= threshold
        truth = target_indices(y, classes)
        output.append({"alpha": alpha, "quantile": float(threshold), "label_coverage": float(sets[np.arange(len(y)), truth].mean()), "mean_set_size": float(sets.sum(axis=1).mean()), "singleton_rate": float((sets.sum(axis=1) == 1).mean()), "limitation": "exchangeability not established for clinical/source shift"})
    return output


def evaluate_job(train, cal, test, rep, seed, meta, identity):
    started = time.monotonic()
    inner_train, _, validation, inner_meta = quota_split(train, seed=seed + 1000, train_frac=.7, cal_frac=.1)
    if not validation:
        raise RuntimeError("no leakage-aware inner validation")
    winner, candidates = select_candidate(inner_train, validation, rep, seed)
    vector, model = representation(rep), estimator(winner["config"], seed)
    x_train = vector.fit_transform(train)
    model.fit(x_train, labels(train))
    classes = model.classes_
    fit_cal, threshold_cal = split_calibration(cal, seed)
    if not fit_cal or not threshold_cal:
        raise RuntimeError("calibration partition insufficient")
    fit_logits = model_logits(model, vector.transform(fit_cal))
    threshold_logits = model_logits(model, vector.transform(threshold_cal))
    test_logits = model_logits(model, vector.transform(test))
    temperature = fit_temperature(fit_logits, labels(fit_cal), classes)
    calibrations = {"raw": (softmax(test_logits, axis=1), softmax(threshold_logits, axis=1)), "temperature": (softmax(test_logits / temperature, axis=1), softmax(threshold_logits / temperature, axis=1))}
    sigmoid_models = []
    isotonic_models = []
    cal_labels = labels(fit_cal)
    for index, label in enumerate(classes):
        binary_y = (cal_labels == label).astype(int)
        if len(set(binary_y)) < 2:
            sigmoid_models.append(None)
            isotonic_models.append(None)
            continue
        sigmoid_models.append(LogisticRegression(C=1., max_iter=1000).fit(fit_logits[:, index:index+1], binary_y))
        isotonic_models.append(IsotonicRegression(out_of_bounds="clip").fit(fit_logits[:, index], binary_y) if min(binary_y.sum(), (1 - binary_y).sum()) >= 20 else None)
    def ovr_prob(logits, calibrators, isotonic=False):
        base = softmax(logits, axis=1)
        for index, calibrator in enumerate(calibrators):
            if calibrator is not None:
                base[:, index] = calibrator.predict(logits[:, index]) if isotonic else calibrator.predict_proba(logits[:, index:index+1])[:, 1]
        base = np.clip(base, 1e-12, 1.)
        return base / base.sum(axis=1, keepdims=True)
    calibrations["ovr_sigmoid"] = (ovr_prob(test_logits, sigmoid_models), ovr_prob(threshold_logits, sigmoid_models))
    if any(calibrator is not None for calibrator in isotonic_models):
        calibrations["ovr_isotonic_partial"] = (ovr_prob(test_logits, isotonic_models, True), ovr_prob(threshold_logits, isotonic_models, True))
    sigmoid = None
    if len(set(labels(fit_cal))) > 1:
        sigmoid = LogisticRegression(C=1., max_iter=1000, random_state=seed)
        sigmoid.fit(fit_logits, labels(fit_cal))
        def sigmoid_prob(logits):
            partial = sigmoid.predict_proba(logits)
            full = np.full((len(logits), len(classes)), 1e-12)
            lookup = {label: i for i, label in enumerate(classes)}
            for i, label in enumerate(sigmoid.classes_):
                full[:, lookup[label]] = partial[:, i]
            return full / full.sum(axis=1, keepdims=True)
        calibrations["regularized_logit_calibrator"] = (sigmoid_prob(test_logits), sigmoid_prob(threshold_logits))
    y_test = labels(test)
    evaluations = {name: {"metrics": metrics(y_test, p_test, classes), "selective": selective_curves(y_test, p_test, p_threshold, classes), "conformal": conformal_sets(y_test, p_test, labels(threshold_cal), p_threshold, classes)} for name, (p_test, p_threshold) in calibrations.items()}
    rng = random.Random(seed)
    shuffled = [{**row, "symptoms": rng.sample(row["symptoms"], len(row["symptoms"]))} for row in test]
    shuffled_logits = model_logits(model, vector.transform(shuffled))
    identity_replay = model_logits(model, vector.transform(test))
    result = {"schema": "core-nested-study/v1", "status": "complete", "identity": identity, "seed": seed, "representation": rep, "split": meta, "inner_split": inner_meta, "selection_policy": "inner validation macro_f1 then accuracy; test never chooses config", "winner": winner, "candidate_records": candidates, "classes": classes.tolist(), "calibration_fit_rows": len(fit_cal), "threshold_cal_rows": len(threshold_cal), "temperature": temperature, "calibration_policy": "temperature primary preset; alternatives descriptive, not selected by test", "evaluations": evaluations, "identity_replay_equal": bool(np.array_equal(identity_replay, test_logits)), "shuffle_max_logit_delta": float(np.abs(shuffled_logits - test_logits).max()), "shuffle_accuracy": float(accuracy_score(y_test, classes[shuffled_logits.argmax(axis=1)])), "test_row_fingerprints": [symptom_fingerprint(row) for row in test], "test_labels": y_test.tolist(), "test_temperature_probabilities": calibrations["temperature"][0].tolist(), "seconds": time.monotonic() - started, "scope": "public text internal research; not clinical validation"}
    result["isotonic_class_count"] = sum(item is not None for item in isotonic_models)
    result["isotonic_policy"] = ">=20 positive and >=20 negative calibration rows per class; unfit classes keep raw probabilities; partial only"
    joblib.dump({"vector": vector, "model": model, "temperature": temperature, "sigmoid": sigmoid, "ovr_sigmoid": sigmoid_models, "ovr_isotonic": isotonic_models, "threshold_logits": threshold_logits, "threshold_labels": labels(threshold_cal), "identity": identity}, OUT / f"{seed}-{rep}.joblib")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", nargs="+", type=int, default=SEEDS)
    parser.add_argument("--representations", nargs="+", choices=REPRESENTATIONS, default=REPRESENTATIONS)
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    with study_lock(OUT / "study.lock"), threadpool_limits(limits=2):
        bundle = load_expanded()
        protocol = {"version": 1, "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), "dataset": bundle.sources, "grid": candidate_grid(), "versions": {"python": os.sys.version, "sklearn": sklearn.__version__, "numpy": np.__version__, "scipy": scipy.__version__}}
        atomic_json(OUT / "protocol.json", protocol)
        for seed in args.seeds:
            train, cal, test, meta = quota_split(bundle.rows, seed=seed)
            meta["train_test_leakage_08"] = cross_split_leakage_audit(train, test, .8)
            meta["train_test_boundary_075"] = cross_split_leakage_audit(train, test, .75)
            for rep in args.representations:
                job = f"{seed}-{rep}"
                identity = digest({"protocol": protocol, "seed": seed, "rep": rep})
                path = OUT / f"{job}.json"
                if path.exists():
                    previous = json.loads(path.read_text(encoding="utf-8"))
                    if previous.get("identity") != identity:
                        raise RuntimeError(f"{job}: completed evidence uses a different code/protocol; choose a new versioned output directory")
                    if previous.get("status") == "complete":
                        print(f"SKIP completed {job}", flush=True)
                        continue
                atomic_json(OUT / "state.json", {"status": "running", "pid": os.getpid(), "job": job, "identity": identity})
                print(f"START {job} ({len(candidate_grid())} inner candidates)", flush=True)
                try:
                    result = evaluate_job(train, cal, test, rep, seed, meta, identity)
                except Exception as error:
                    result = {"status": "failed", "identity": identity, "job": job, "error": repr(error)}
                    atomic_json(path, result)
                    raise
                atomic_json(path, result)
                print(f"DONE {job} winner={result['winner']['config']} acc={result['evaluations']['temperature']['metrics']['accuracy']:.4f} ece={result['evaluations']['temperature']['metrics']['ece']:.4f} ({result['seconds']:.1f}s)", flush=True)
        atomic_json(OUT / "state.json", {"status": "complete", "pid": os.getpid(), "seeds": args.seeds, "representations": args.representations})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
