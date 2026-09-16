"""Three-state adaptive inquiry protocol (simulation).

Layer A keeps the previous positive-only oracle.
Layer B uses present/absent/unknown updates and is always labeled simulation.
"""

from __future__ import annotations

import math
import random
from collections import Counter
from typing import Any, Callable, Mapping, Sequence

from .disease_department import department_for
from .symptom_state import binary_symptom_likelihood
from .uncertainty import (
    distribution_entropy,
    predict_distribution,
    should_clarify,
    top1_confidence,
    top_margin,
)


StrategyFn = Callable[..., dict[str, Any]]


def predict_with_states(
    model: Mapping[str, Any],
    present: Sequence[str],
    absent: Sequence[str],
    temperature: float = 1.0,
) -> list[tuple[str, float]]:
    """Multiclass posterior under tri-state NB likelihood + class prior."""

    classes = list(model.get("classes") or [])
    vocabulary = list(model.get("vocabulary") or [])
    class_counts = model.get("class_counts") or {}
    symptom_counts = model.get("symptom_counts") or {}
    total_symptom_counts = model.get("total_symptom_counts") or {}
    alpha = float(model.get("alpha", 1.0))
    total_rows = sum(class_counts.values()) or 1
    t = max(float(temperature), 1e-6)

    present_in_vocab = [s for s in present if s in set(vocabulary)]
    absent_in_vocab = [s for s in absent if s in set(vocabulary) and s not in set(present_in_vocab)]

    scores: dict[str, float] = {}
    for disease in classes:
        prior = (class_counts.get(disease, 0) + alpha) / (total_rows + alpha * len(classes))
        ll = binary_symptom_likelihood(
            present_codes=present_in_vocab,
            absent_codes=absent_in_vocab,
            disease=disease,
            symptom_counts=symptom_counts,
            total_symptom_counts=total_symptom_counts,
            vocabulary=vocabulary,
            alpha=alpha,
        )
        scores[disease] = math.log(prior) + ll

    if not scores:
        return []
    # Temperature on log-scores then softmax.
    scaled = {label: score / t for label, score in scores.items()}
    max_score = max(scaled.values())
    exp_scores = {label: math.exp(score - max_score) for label, score in scaled.items()}
    total = sum(exp_scores.values()) or 1.0
    return sorted(
        ((label, value / total) for label, value in exp_scores.items()),
        key=lambda item: item[1],
        reverse=True,
    )


def expected_information_gain_states(
    posterior: Sequence[tuple[str, float]],
    model: Mapping[str, Any],
    candidate: str,
    present: Sequence[str],
    absent: Sequence[str],
) -> dict[str, float]:
    """IG for a binary yes/no question under tri-state features."""

    vocabulary = set(model.get("vocabulary") or [])
    if candidate not in vocabulary or candidate in set(present) or candidate in set(absent):
        return {"information_gain": -1.0, "current_entropy": 0.0, "expected_posterior_entropy": 0.0}

    current_h = distribution_entropy(posterior)

    def post(answer_present: bool) -> tuple[list[tuple[str, float]], float]:
        new_present = list(present) + ([candidate] if answer_present else [])
        new_absent = list(absent) + ([] if answer_present else [candidate])
        ranked = predict_with_states(model, new_present, new_absent)
        # P(answer | x) = sum_y P(y|x) P(answer|y)
        symptom_counts = model.get("symptom_counts") or {}
        total_symptom_counts = model.get("total_symptom_counts") or {}
        vocabulary_list = list(model.get("vocabulary") or [])
        alpha = float(model.get("alpha", 1.0))
        p_answer = 0.0
        for label, p_y in posterior:
            denom = float(total_symptom_counts.get(label, 0)) + alpha * max(len(vocabulary_list), 1)
            count = float((symptom_counts.get(label) or {}).get(candidate, 0))
            p_yes = (count + alpha) / denom
            p_yes = min(max(p_yes, 1e-12), 1.0 - 1e-12)
            likelihood = p_yes if answer_present else (1.0 - p_yes)
            p_answer += p_y * likelihood
        return ranked, p_answer

    ranked_yes, p_yes = post(True)
    ranked_no, p_no = post(False)
    h_yes = distribution_entropy(ranked_yes)
    h_no = distribution_entropy(ranked_no)
    mass = p_yes + p_no
    expected_h = ((p_yes * h_yes) + (p_no * h_no)) / mass if mass > 0 else current_h
    return {
        "information_gain": current_h - expected_h,
        "current_entropy": current_h,
        "expected_posterior_entropy": expected_h,
        "p_yes": p_yes,
        "p_no": p_no,
    }


def select_ig_question_states(
    model: Mapping[str, Any],
    present: Sequence[str],
    absent: Sequence[str],
    temperature: float = 1.0,
    top_k: int = 10,
) -> dict[str, Any] | None:
    posterior = predict_with_states(model, present, absent, temperature=temperature)
    if not posterior:
        return None
    known = set(present) | set(absent)
    scored = []
    for symptom in model.get("vocabulary") or []:
        if symptom in known:
            continue
        metrics = expected_information_gain_states(
            posterior, model, symptom, present, absent
        )
        scored.append((symptom, metrics))
    if not scored:
        return None
    scored.sort(key=lambda item: item[1]["information_gain"], reverse=True)
    symptom, metrics = scored[0]
    return {
        "symptom": symptom,
        "information_gain": round(metrics["information_gain"], 6),
        "p_yes": round(metrics.get("p_yes", 0.0), 6),
        "current_entropy": round(metrics["current_entropy"], 6),
        "top_candidates": [
            {"symptom": name, "information_gain": round(m["information_gain"], 6)}
            for name, m in scored[:top_k]
        ],
    }


def select_margin_question(
    model: Mapping[str, Any],
    present: Sequence[str],
    absent: Sequence[str],
    temperature: float = 1.0,
) -> dict[str, Any] | None:
    """Pick the question that most reduces top1-top2 margin in expectation (greedy proxy)."""

    posterior = predict_with_states(model, present, absent, temperature=temperature)
    if not posterior:
        return None
    known = set(present) | set(absent)
    best = None
    best_gain = -1.0
    for symptom in model.get("vocabulary") or []:
        if symptom in known:
            continue
        gains = []
        for answer in (True, False):
            new_present = list(present) + ([symptom] if answer else [])
            new_absent = list(absent) + ([] if answer else [symptom])
            ranked = predict_with_states(model, new_present, new_absent, temperature=temperature)
            gains.append(top_margin(ranked))
        # Higher remaining margin is worse for discrimination; prefer lower expected margin.
        expected_margin = sum(gains) / 2.0
        score = -expected_margin
        if score > best_gain:
            best_gain = score
            best = {"symptom": symptom, "information_gain": round(-expected_margin, 6)}
    return best


def select_most_frequent_question(
    model: Mapping[str, Any],
    present: Sequence[str],
    absent: Sequence[str],
) -> str | None:
    known = set(present) | set(absent)
    counter: Counter[str] = Counter()
    for counts in (model.get("symptom_counts") or {}).values():
        for symptom, count in counts.items():
            if symptom not in known:
                counter[symptom] += int(count)
    return counter.most_common(1)[0][0] if counter else None


def select_random_question(
    model: Mapping[str, Any],
    present: Sequence[str],
    absent: Sequence[str],
    rng: random.Random,
) -> str | None:
    known = set(present) | set(absent)
    candidates = [s for s in (model.get("vocabulary") or []) if s not in known]
    return rng.choice(candidates) if candidates else None


def fixed_question_order(model: Mapping[str, Any]) -> list[str]:
    """Document-frequency order derived from training counts only (not medical rules)."""

    counter: Counter[str] = Counter()
    for counts in (model.get("symptom_counts") or {}).values():
        for symptom, count in counts.items():
            counter[symptom] += int(count)
    return [symptom for symptom, _ in counter.most_common()]


def oracle_answer(true_symptoms: Sequence[str], question: str) -> bool:
    """Simulation oracle: present iff the held-out row contains the symptom.

    This is NOT a real patient. Label results as simulation.
    """

    return question in set(true_symptoms)


def run_three_state_inquiry(
    model: Mapping[str, Any],
    row: Mapping[str, Any],
    *,
    strategy: str = "information_gain",
    initial_symptom_count: int = 1,
    max_questions: int = 5,
    temperature: float = 1.0,
    seed: int = 42,
    stopping_fn: Callable[..., bool] | None = None,
    force_questions: bool = False,
) -> dict[str, Any]:
    true_symptoms = list(row.get("symptoms") or [])
    true_disease = row["disease"]
    if not true_symptoms:
        return {"skipped": True, "reason": "empty_symptom_set"}

    rng = random.Random(f"{seed}:{true_disease}:{','.join(sorted(true_symptoms))}")
    ordered = true_symptoms[:]
    rng.shuffle(ordered)
    present = ordered[: max(1, min(initial_symptom_count, len(ordered)))]
    absent: list[str] = []
    asked: set[str] = set(present)
    fixed_order = fixed_question_order(model) if strategy == "fixed_order" else []
    fixed_cursor = 0

    initial_ranked = predict_with_states(model, present, absent, temperature=temperature)
    initial_entropy = distribution_entropy(initial_ranked)
    initial_conf = top1_confidence(initial_ranked)
    initial_correct = bool(initial_ranked) and initial_ranked[0][0] == true_disease

    history: list[dict[str, Any]] = []
    stop_reason = "max_questions"
    questions_asked = 0

    while questions_asked < max_questions:
        ranked = predict_with_states(model, present, absent, temperature=temperature)
        entropy = distribution_entropy(ranked)
        confidence = top1_confidence(ranked)
        margin = top_margin(ranked)
        set_size = min(3, len(ranked))

        if not force_questions:
            if stopping_fn is not None:
                should_stop = stopping_fn(
                    entropy=entropy,
                    confidence=confidence,
                    margin=margin,
                    set_size=set_size,
                    questions_asked=questions_asked,
                    max_questions=max_questions,
                    max_entropy=math.log2(max(len(ranked), 2)),
                )
            else:
                should_stop = not should_clarify(
                    entropy=entropy,
                    confidence=confidence,
                    set_size=set_size,
                    max_entropy=math.log2(max(len(ranked), 2)),
                )
            if should_stop:
                stop_reason = "stopping_policy"
                break

        question = None
        ig = None
        if strategy == "information_gain":
            choice = select_ig_question_states(model, present, absent, temperature=temperature)
            if not choice:
                stop_reason = "no_candidates"
                break
            question = choice["symptom"]
            ig = choice["information_gain"]
        elif strategy == "margin":
            choice = select_margin_question(model, present, absent, temperature=temperature)
            if not choice:
                stop_reason = "no_candidates"
                break
            question = choice["symptom"]
            ig = choice["information_gain"]
        elif strategy == "random":
            question = select_random_question(model, present, absent, rng)
            if question is None:
                stop_reason = "no_candidates"
                break
        elif strategy == "most_frequent":
            question = select_most_frequent_question(model, present, absent)
            if question is None:
                stop_reason = "no_candidates"
                break
        elif strategy == "fixed_order":
            while fixed_cursor < len(fixed_order) and fixed_order[fixed_cursor] in asked:
                fixed_cursor += 1
            if fixed_cursor >= len(fixed_order):
                stop_reason = "no_candidates"
                break
            question = fixed_order[fixed_cursor]
            fixed_cursor += 1
        else:
            raise ValueError(f"unknown strategy: {strategy}")

        answer_present = oracle_answer(true_symptoms, question)
        asked.add(question)
        questions_asked += 1
        before_entropy = entropy
        before_top = ranked[0][0] if ranked else None
        before_set = set_size
        if answer_present:
            present.append(question)
        else:
            absent.append(question)
        after_ranked = predict_with_states(model, present, absent, temperature=temperature)
        after_entropy = distribution_entropy(after_ranked)
        history.append(
            {
                "question_symptom": question,
                "information_gain": ig,
                "answer": "present" if answer_present else "absent",
                "entropy_before": round(before_entropy, 6),
                "entropy_after": round(after_entropy, 6),
                "entropy_reduction": round(before_entropy - after_entropy, 6),
                "top1_before": before_top,
                "top1_after": after_ranked[0][0] if after_ranked else None,
                "set_size_before": before_set,
                "set_size_after": min(3, len(after_ranked)),
            }
        )

    final_ranked = predict_with_states(model, present, absent, temperature=temperature)
    final_entropy = distribution_entropy(final_ranked)
    final_conf = top1_confidence(final_ranked)
    final_correct = bool(final_ranked) and final_ranked[0][0] == true_disease
    wrong_but_confident = final_correct is False and final_conf >= 0.7

    return {
        "skipped": False,
        "protocol": "three_state_simulation",
        "is_synthetic_oracle": True,
        "true_disease": true_disease,
        "true_department": department_for(true_disease),
        "predicted_department": department_for(final_ranked[0][0]) if final_ranked else None,
        "initial_present": ordered[: max(1, min(initial_symptom_count, len(ordered)))],
        "present_after": list(present),
        "absent_after": list(absent),
        "initial": {
            "top1": initial_ranked[0][0] if initial_ranked else None,
            "confidence": round(initial_conf, 6),
            "entropy": round(initial_entropy, 6),
            "correct": initial_correct,
            "set_size": min(3, len(initial_ranked)),
        },
        "questions": history,
        "questions_asked": questions_asked,
        "final": {
            "top1": final_ranked[0][0] if final_ranked else None,
            "confidence": round(final_conf, 6),
            "entropy": round(final_entropy, 6),
            "correct": final_correct,
            "set_size": min(3, len(final_ranked)),
            "entropy_reduction_total": round(initial_entropy - final_entropy, 6),
            "wrong_but_confident": wrong_but_confident,
        },
        "stop_reason": stop_reason,
    }


def summarize_three_state_runs(runs: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    completed = [run for run in runs if not run.get("skipped")]
    if not completed:
        return {
            "cases": 0,
            "initial_accuracy": None,
            "final_accuracy": None,
            "accuracy_delta": None,
            "macro_f1_final": None,
            "avg_questions": None,
            "median_questions": None,
            "mean_entropy_reduction": None,
            "accuracy_gain_per_question": None,
            "stop_rate": None,
            "wrong_but_confident_rate": None,
            "mean_set_size_before": None,
            "mean_set_size_after": None,
            "department_accuracy_initial": None,
            "department_accuracy_final": None,
            "department_accuracy_delta": None,
        }

    def acc(flags: Sequence[bool]) -> float:
        return round(sum(flags) / len(flags), 6) if flags else 0.0

    initial_correct = [bool(run["initial"]["correct"]) for run in completed]
    final_correct = [bool(run["final"]["correct"]) for run in completed]
    questions = sorted(int(run["questions_asked"]) for run in completed)
    reductions = [float(run["final"]["entropy_reduction_total"]) for run in completed]
    stop_reasons = Counter(run.get("stop_reason", "unknown") for run in completed)
    wrong_conf = [bool(run["final"]["wrong_but_confident"]) for run in completed]
    set_before = [int(run["initial"]["set_size"]) for run in completed]
    set_after = [int(run["final"]["set_size"]) for run in completed]
    dept_init = [
        department_for(run["true_disease"])
        == (department_for(run["initial"]["top1"]) if run["initial"]["top1"] else None)
        for run in completed
    ]
    dept_final = [
        department_for(run["true_disease"]) == run.get("predicted_department")
        for run in completed
    ]

    # Macro-F1 on final disease labels.
    y_true = [run["true_disease"] for run in completed]
    y_pred = [run["final"]["top1"] for run in completed]
    labels = sorted(set(y_true) | {y for y in y_pred if y})
    f1s = []
    for label in labels:
        tp = sum(1 for t, p in zip(y_true, y_pred) if t == label and p == label)
        fp = sum(1 for t, p in zip(y_true, y_pred) if t != label and p == label)
        fn = sum(1 for t, p in zip(y_true, y_pred) if t == label and p != label)
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1s.append(2 * precision * recall / (precision + recall) if precision + recall else 0.0)
    macro_f1 = round(sum(f1s) / len(f1s), 6) if f1s else 0.0

    avg_q = sum(questions) / len(questions)
    delta = acc(final_correct) - acc(initial_correct)
    return {
        "cases": len(completed),
        "initial_accuracy": acc(initial_correct),
        "final_accuracy": acc(final_correct),
        "accuracy_delta": round(delta, 6),
        "macro_f1_final": macro_f1,
        "avg_questions": round(avg_q, 6),
        "median_questions": questions[len(questions) // 2],
        "questions_distribution": dict(Counter(questions)),
        "mean_entropy_reduction": round(sum(reductions) / len(reductions), 6),
        "accuracy_gain_per_question": round(delta / avg_q, 6) if avg_q else 0.0,
        "stop_rate": round(
            sum(count for reason, count in stop_reasons.items() if reason == "stopping_policy")
            / len(completed),
            6,
        ),
        "stop_reasons": dict(stop_reasons),
        "wrong_but_confident_rate": acc(wrong_conf),
        "mean_set_size_before": round(sum(set_before) / len(set_before), 6),
        "mean_set_size_after": round(sum(set_after) / len(set_after), 6),
        "department_accuracy_initial": acc(dept_init),
        "department_accuracy_final": acc(dept_final),
        "department_accuracy_delta": round(acc(dept_final) - acc(dept_init), 6),
    }
