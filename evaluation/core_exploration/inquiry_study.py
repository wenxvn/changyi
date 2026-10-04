"""Matched token-vs-record likelihood and inquiry policy simulation.

Missing symptoms in public text are NOT clinical negatives. Closed-world oracle
answers and response noise here are explicit simulation conditions only.
"""
from __future__ import annotations
from collections import Counter
import random
import numpy as np
from .study import OUT, SEEDS, atomic_json, study_lock
from evaluation.care_routing.round3_split_audit import load_expanded, quota_split
from evaluation.care_routing.disease_department import department_for

TARGET = OUT.parent / "inquiry-v1"


def fit_answer_model(rows, task, denominator):
    label = (lambda r: r["disease"]) if task == "disease" else (lambda r: department_for(r["disease"]))
    classes = sorted(set(label(r) for r in rows))
    df = Counter(code for row in rows for code in set(row["symptoms"]))
    vocabulary = sorted(code for code, count in df.items() if count >= 2)
    class_index, code_index = {name: i for i, name in enumerate(classes)}, {name: i for i, name in enumerate(vocabulary)}
    counts = np.zeros((len(classes), len(vocabulary)))
    class_n = np.zeros(len(classes))
    for row in rows:
        c = class_index[label(row)]
        class_n[c] += 1
        for code in set(row["symptoms"]):
            if code in code_index:
                counts[c, code_index[code]] += 1
    denom = class_n[:, None] + 2 if denominator == "record" else counts.sum(axis=1)[:, None] + len(vocabulary)
    likelihood = np.clip((counts + 1) / denom, 1e-9, 1 - 1e-9)
    prior = (class_n + 1) / (class_n.sum() + len(classes))
    return {"classes": classes, "vocabulary": vocabulary, "index": code_index, "likelihood": likelihood, "prior": prior, "frequency": counts.sum(axis=0)}


def utility(posterior, likelihood):
    p_yes = posterior @ likelihood
    yes = posterior[:, None] * likelihood / p_yes
    no = posterior[:, None] * (1 - likelihood) / (1 - p_yes)
    entropy = -(posterior * np.log(posterior)).sum()
    expected = p_yes * (-(yes * np.log(np.clip(yes, 1e-12, 1))).sum(axis=0)) + (1 - p_yes) * (-(no * np.log(np.clip(no, 1e-12, 1))).sum(axis=0))
    return entropy - expected


def simulate(model, row, task, strategy, budget, seed, noise=0., unknown=0.):
    rng = random.Random(seed)
    true_set = set(row["symptoms"])
    initial = sorted(true_set)
    rng.shuffle(initial)
    initial = initial[:1]
    p = model["prior"].copy()
    answered = set()
    for code in initial:
        if code in model["index"]:
            index = model["index"][code]
            p *= model["likelihood"][:, index]
            p /= p.sum()
            answered.add(index)
    target = row["disease"] if task == "disease" else department_for(row["disease"])
    initial_pred = model["classes"][int(p.argmax())]
    unknown_answers = 0
    for _ in range(budget):
        if len(answered) >= len(model["vocabulary"]):
            break
        candidates = [i for i in range(len(model["vocabulary"])) if i not in answered]
        if strategy == "ig":
            scores = utility(p, model["likelihood"])
            question = max(candidates, key=lambda i: scores[i])
        elif strategy == "frequency":
            question = max(candidates, key=lambda i: model["frequency"][i])
        else:
            question = rng.choice(candidates)
        answered.add(question)
        if rng.random() < unknown:
            unknown_answers += 1
            continue
        yes = model["vocabulary"][question] in true_set
        if rng.random() < noise:
            yes = not yes
        p *= model["likelihood"][:, question] if yes else (1 - model["likelihood"][:, question])
        p /= p.sum()
    predicted = model["classes"][int(p.argmax())]
    return {"initial_correct": initial_pred == target, "correct": predicted == target, "department_correct": (department_for(predicted) == department_for(target)) if task == "disease" else predicted == target, "questions": max(0, len(answered) - len([c for c in initial if c in model['index']])), "unknown_answers": unknown_answers, "wrong_confident": predicted != target and p.max() >= .7}


def main():
    TARGET.mkdir(parents=True, exist_ok=True)
    with study_lock(TARGET / "run.lock"):
        bundle = load_expanded()
        for seed in SEEDS:
            path = TARGET / f"{seed}.json"
            if path.exists():
                continue
            train, _, test, meta = quota_split(bundle.rows, seed=seed)
            records = []
            for task in ("disease", "department"):
                for denominator in ("token", "record"):
                    model = fit_answer_model(train, task, denominator)
                    for strategy in ("ig", "random", "frequency"):
                        for budget in (1, 3, 5):
                            # Clean and two deliberately imperfect-answer settings.
                            for noise, unknown in ((0., 0.), (.1, 0.), (0., .3)):
                                runs = [simulate(model, row, task, strategy, budget, seed + i, noise, unknown) for i, row in enumerate(test)]
                                means = {key: float(np.mean([run[key] for run in runs])) for key in runs[0]}
                                records.append({"task": task, "likelihood": denominator, "strategy": strategy, "budget": budget, "flip_probability": noise, "unknown_probability": unknown, "n": len(runs), **means})
            atomic_json(path, {"status": "complete", "seed": seed, "split": meta, "records": records, "oracle": "closed-world public symptom set; absent-in-text treated absent ONLY for simulation", "clinical_negatives_observed": False})
            print(f"DONE inquiry {seed} ({len(records)} matched settings)", flush=True)
        atomic_json(TARGET / "state.json", {"status": "complete", "settings_per_seed": 108, "seeds": list(SEEDS)})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
