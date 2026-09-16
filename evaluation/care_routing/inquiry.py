"""Information-gain adaptive inquiry over the prototype NB symptom model.

Offline protocol only: held-out labeled symptom sets act as oracles for
yes/no answers. No patient dialogues are invented or written into production.
"""

from __future__ import annotations

import math
import random
from collections import Counter
from typing import Any, Mapping, Sequence

from .uncertainty import (
    distribution_entropy,
    predict_distribution,
    should_clarify,
    top1_confidence,
)


def class_conditional_symptom_probs(
    model: Mapping[str, Any],
    alpha: float | None = None,
) -> dict[str, dict[str, float]]:
    """P(symptom|disease) with Laplace smoothing from stored counts."""

    alpha_value = float(model.get("alpha", 1.0) if alpha is None else alpha)
    vocab_size = len(model.get("vocabulary") or [])
    table: dict[str, dict[str, float]] = {}
    for disease, counts in (model.get("symptom_counts") or {}).items():
        total = float(model.get("total_symptom_counts", {}).get(disease, 0))
        denom = total + alpha_value * max(vocab_size, 1)
        disease_probs = {}
        for symptom in model.get("vocabulary") or []:
            count = float(counts.get(symptom, 0))
            disease_probs[symptom] = (count + alpha_value) / denom
        table[disease] = disease_probs
    return table


def expected_information_gain(
    posterior: Sequence[tuple[str, float]],
    symptom_probs: Mapping[str, Mapping[str, float]],
    candidate_symptom: str,
) -> dict[str, float]:
    """IG = H(Y|x) - E_q[H(Y|x,q)] with binary presence model.

    P(q=1|Y=y) comes from training counts; answer likelihood is independent
    of other observed symptoms given Y (Naive Bayes consistency).
    """

    current_h = distribution_entropy(posterior)
    p_yes = 0.0
    p_no = 0.0
    weighted_h = 0.0
    for label, p_y in posterior:
        p_q1 = float(symptom_probs.get(label, {}).get(candidate_symptom, 0.0))
        p_q1 = min(max(p_q1, 1e-9), 1.0 - 1e-9)
        p_q0 = 1.0 - p_q1
        p_yes += p_y * p_q1
        p_no += p_y * p_q0

    def posterior_entropy_for_answer(answer_yes: bool) -> float:
        unnorm = []
        for label, p_y in posterior:
            p_q1 = float(symptom_probs.get(label, {}).get(candidate_symptom, 0.0))
            p_q1 = min(max(p_q1, 1e-9), 1.0 - 1e-9)
            likelihood = p_q1 if answer_yes else (1.0 - p_q1)
            unnorm.append((label, p_y * likelihood))
        total = sum(p for _, p in unnorm)
        if total <= 0:
            return current_h
        normalized = [(label, p / total) for label, p in unnorm]
        return distribution_entropy(normalized)

    if p_yes + p_no > 0:
        weighted_h = (p_yes * posterior_entropy_for_answer(True)) + (p_no * posterior_entropy_for_answer(False))
    ig = current_h - weighted_h
    return {
        "information_gain": ig,
        "current_entropy": current_h,
        "expected_posterior_entropy": weighted_h,
        "p_yes": p_yes,
        "p_no": p_no,
    }


def select_information_gain_question(
    model: Mapping[str, Any],
    known_symptoms: Sequence[str],
    symptom_probs: Mapping[str, Mapping[str, float]],
    temperature: float = 1.0,
    top_k_candidates: int = 12,
    exclude: set[str] | None = None,
) -> dict[str, Any] | None:
    known = set(known_symptoms)
    skip = known | set(exclude or ())
    posterior = predict_distribution(model, known, temperature=temperature)
    if not posterior:
        return None
    scores = []
    for symptom in model.get("vocabulary") or []:
        if symptom in skip:
            continue
        metrics = expected_information_gain(posterior, symptom_probs, symptom)
        scores.append((symptom, metrics))
    if not scores:
        return None
    scores.sort(key=lambda item: item[1]["information_gain"], reverse=True)
    symptom, metrics = scores[0]
    return {
        "symptom": symptom,
        "information_gain": round(metrics["information_gain"], 6),
        "p_yes": round(metrics["p_yes"], 6),
        "p_no": round(metrics["p_no"], 6),
        "expected_posterior_entropy": round(metrics["expected_posterior_entropy"], 6),
        "current_entropy": round(metrics["current_entropy"], 6),
        "top_candidates": [
            {
                "symptom": name,
                "information_gain": round(item["information_gain"], 6),
            }
            for name, item in scores[:top_k_candidates]
        ],
    }


def random_question(
    model: Mapping[str, Any],
    known_symptoms: Sequence[str],
    rng: random.Random,
) -> str | None:
    candidates = [s for s in (model.get("vocabulary") or []) if s not in set(known_symptoms)]
    if not candidates:
        return None
    return rng.choice(candidates)


def most_frequent_unknown_symptom(
    model: Mapping[str, Any],
    known_symptoms: Sequence[str],
) -> str | None:
    known = set(known_symptoms)
    counter: Counter[str] = Counter()
    for counts in (model.get("symptom_counts") or {}).values():
        for symptom, count in counts.items():
            if symptom not in known:
                counter[symptom] += int(count)
    if not counter:
        return None
    return counter.most_common(1)[0][0]


def run_adaptive_inquiry(
    model: Mapping[str, Any],
    row: Mapping[str, Any],
    *,
    strategy: str = "information_gain",
    initial_symptom_count: int = 2,
    max_questions: int = 5,
    temperature: float = 1.0,
    confidence_threshold: float = 0.55,
    entropy_ratio_threshold: float = 0.55,
    seed: int = 42,
    symptom_probs: Mapping[str, Mapping[str, float]] | None = None,
    force_questions: bool = False,
) -> dict[str, Any]:
    """Simulate inquiry on one held-out labeled sample.

    Answers come from the sample's ground-truth symptom set (oracle), never
    from synthetic patient text.
    """

    true_symptoms = list(row.get("symptoms") or [])
    true_disease = row["disease"]
    if not true_symptoms:
        return {"skipped": True, "reason": "empty_symptom_set"}

    rng = random.Random(f"{seed}:{true_disease}:{','.join(sorted(true_symptoms))}")
    ordered = true_symptoms[:]
    rng.shuffle(ordered)
    known = ordered[: max(1, min(initial_symptom_count, len(ordered)))]
    remaining_oracle = set(true_symptoms) - set(known)
    asked: set[str] = set()

    if symptom_probs is None:
        symptom_probs = class_conditional_symptom_probs(model)

    history: list[dict[str, Any]] = []
    initial_ranked = predict_distribution(model, known, temperature=temperature)
    initial_entropy = distribution_entropy(initial_ranked)
    initial_correct = bool(initial_ranked) and initial_ranked[0][0] == true_disease
    initial_confidence = top1_confidence(initial_ranked)

    questions_asked = 0
    stop_reason = "max_questions"
    while questions_asked < max_questions:
        ranked = predict_distribution(model, known, temperature=temperature)
        # Only search unasked symptoms; asked-negatives stay out of features.
        available = [s for s in (model.get("vocabulary") or []) if s not in set(known) and s not in asked]
        if not available:
            stop_reason = "no_candidates"
            break
        entropy = distribution_entropy(ranked)
        confidence = top1_confidence(ranked)
        max_entropy = math.log2(max(len(ranked), 2))
        if not force_questions and should_clarify(
            entropy=entropy,
            confidence=confidence,
            set_size=3 if len(ranked) > 1 else 1,
            max_entropy=max_entropy,
            confidence_threshold=confidence_threshold,
            entropy_ratio_threshold=entropy_ratio_threshold,
        ) is False:
            stop_reason = "confident_enough"
            break

        if strategy == "information_gain":
            choice = select_information_gain_question(
                model,
                known,
                symptom_probs,
                temperature=temperature,
                exclude=asked,
            )
            if not choice:
                stop_reason = "no_candidates"
                break
            question = choice["symptom"]
            ig = choice["information_gain"]
        elif strategy == "random":
            question = random_question(model, list(known) + list(asked), rng)
            ig = None
            if question is None:
                stop_reason = "no_candidates"
                break
        elif strategy == "most_frequent":
            question = most_frequent_unknown_symptom(model, list(known) + list(asked))
            ig = None
            if question is None:
                stop_reason = "no_candidates"
                break
        else:
            raise ValueError(f"unknown strategy: {strategy}")

        answer_yes = question in set(true_symptoms)
        questions_asked += 1
        asked.add(question)
        before_entropy = entropy
        before_top = ranked[0][0] if ranked else None
        if answer_yes:
            known.append(question)
            asked.discard(question)
        # A "no" answer is informative too; production would update the
        # posterior with an explicit negative feature. Offline we only add
        # confirmed positives so we do not invent negative symptom labels
        # that the bag-of-tags model never represented.
        after_ranked = predict_distribution(model, known, temperature=temperature)
        after_entropy = distribution_entropy(after_ranked)
        history.append(
            {
                "question_symptom": question,
                "information_gain": ig,
                "answer": "yes" if answer_yes else "no",
                "entropy_before": round(before_entropy, 6),
                "entropy_after": round(after_entropy, 6),
                "entropy_reduction": round(before_entropy - after_entropy, 6),
                "top1_before": before_top,
                "top1_after": after_ranked[0][0] if after_ranked else None,
            }
        )
    else:
        stop_reason = "max_questions"

    final_ranked = predict_distribution(model, known, temperature=temperature)
    final_entropy = distribution_entropy(final_ranked)
    final_correct = bool(final_ranked) and final_ranked[0][0] == true_disease
    final_confidence = top1_confidence(final_ranked)
    return {
        "skipped": False,
        "true_disease": true_disease,
        "initial_symptoms": ordered[: max(1, min(initial_symptom_count, len(ordered)))],
        "known_after": known,
        "initial": {
            "top1": initial_ranked[0][0] if initial_ranked else None,
            "confidence": round(initial_confidence, 6),
            "entropy": round(initial_entropy, 6),
            "correct": initial_correct,
        },
        "questions": history,
        "questions_asked": questions_asked,
        "final": {
            "top1": final_ranked[0][0] if final_ranked else None,
            "confidence": round(final_confidence, 6),
            "entropy": round(final_entropy, 6),
            "correct": final_correct,
            "entropy_reduction_total": round(initial_entropy - final_entropy, 6),
        },
        "stop_reason": stop_reason,
        "protocol": "held-out labeled symptom set as oracle; negatives not written into model features",
    }
