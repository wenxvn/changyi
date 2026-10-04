"""Cal-only empirical selective policy on saved synthetic models, no fitting."""
import hashlib
import json
import numpy as np
from scipy.special import softmax
from sklearn.feature_extraction import DictVectorizer
from backend.app.domain.symptom_assertions import parse_asserted_symptoms
from .canonical_name_bridge_audit import build_bridge
from .chinese_adaptation import texts_and_labels
from .semantic_bridge import NAMES, ALIASES
from .versioned_challenge import ROOT
from .saved_bridge_calibration_audit import run as verify_saved_models
from evaluation.care_routing.round3_split_audit import load_structured


def choose_cal_threshold(confidence, correct, groups):
    confidence, correct, groups = np.asarray(confidence), np.asarray(correct), np.asarray(groups)
    if not (len(confidence) == len(correct) == len(groups)):
        raise ValueError("Calibration denominators differ")
    candidates = []
    for threshold in np.linspace(0, 1, 21):
        retained = confidence >= threshold
        count = int(retained.sum())
        group_count = len(set(groups[retained].tolist()))
        accuracy = float(correct[retained].mean()) if count else None
        candidates.append({"threshold": float(threshold), "retained_cases": count,
                           "retained_groups": group_count, "accuracy": accuracy,
                           "eligible": count >= 10 and group_count >= 5 and accuracy >= .8})
    eligible = [c for c in candidates if c["eligible"]]
    chosen = max(eligible, key=lambda c: (c["retained_cases"], -c["threshold"])) if eligible else None
    return {"threshold": chosen["threshold"] if chosen else None,
            "status": "CAL_EMPIRICAL_TARGET_MET" if chosen else "NO_ADMISSIBLE_CAL_THRESHOLD",
            "candidates": candidates}


def case_predictions(record, indices, templates, offset, rows, aliases):
    texts, labels = texts_and_labels([rows[i] for i in indices], templates, record["seed"]+offset)
    state = record["learned_state"]
    vector = DictVectorizer()
    vector.feature_names_ = state["features"]
    vector.vocabulary_ = {name: i for i, name in enumerate(state["features"])}
    features = [{code: 1. for code in parse_asserted_symptoms(text, aliases)["present"]} for text in texts]
    logits = np.asarray(vector.transform(features) @ np.asarray(state["coef"]).T) + np.asarray(state["intercept"])
    if logits.shape[1] == 1:
        logits = np.column_stack((-logits[:, 0], logits[:, 0]))
    probability = softmax(logits/record["temperature"], axis=1)
    probability = probability.reshape(len(indices), len(templates), -1).mean(axis=1)
    labels = labels.reshape(len(indices), len(templates))
    if not np.all(labels == labels[:, :1]):
        raise ValueError("Renderer labels disagree")
    classes = np.asarray(state["classes"])
    return probability.max(axis=1), classes[probability.argmax(axis=1)] == labels[:, 0], ~np.isin(labels[:, 0], classes)


def run():
    directory = ROOT / "evaluation/core_exploration/results/versioned-challenges/w64-paired-name-bridge"
    blob = (directory / "result.json").read_bytes()
    source = json.loads(blob)
    rows = load_structured().rows
    bridge, _, conflicts = build_bridge(NAMES, ALIASES)
    if conflicts:
        raise ValueError("Bridge conflict")
    policies = []
    for record in source["records"]:
        aliases = ALIASES if record["method"] == "current_alias" else bridge
        indices = record["splits"]["cal"]
        confidence, correct, unseen = case_predictions(record, indices, source["train_templates"], 2, rows, aliases)
        policy = choose_cal_threshold(confidence, correct, [source["group_ids"][i] for i in indices])
        policies.append({**policy, "cal_cases": len(indices), "cal_unseen_cases": int(unseen.sum())})
    # Lock all thresholds before accessing test inference; verify old states and
    # source identities rather than refitting the original research models.
    verification = verify_saved_models()
    records = []
    for record, policy in zip(source["records"], policies):
        aliases = ALIASES if record["method"] == "current_alias" else bridge
        confidence, correct, unseen = case_predictions(record, record["splits"]["test"], source["test_templates"], 3, rows, aliases)
        retained = confidence >= policy["threshold"] if policy["threshold"] is not None else np.zeros(len(correct), dtype=bool)
        n, accepted = len(correct), int(retained.sum())
        records.append({"seed": record["seed"], "fold": record["fold"], "method": record["method"],
                        "model_identity_sha256": record["model_identity_sha256"], "policy": policy,
                        "test_cases": n, "accepted": accepted, "abstained": n-accepted,
                        "accepted_correct": int(correct[retained].sum()),
                        "retained_accuracy": float(correct[retained].mean()) if accepted else None,
                        "unseen_cases": int(unseen.sum()), "unseen_accepted": int((unseen&retained).sum()),
                        "test_empirical_target_met": bool(accepted and correct[retained].mean() >= .8)})
    summary = {}
    for method in ("current_alias", "declared_name_bridge"):
        selected = [r for r in records if r["method"] == method]
        total, accepted = sum(r["test_cases"] for r in selected), sum(r["accepted"] for r in selected)
        summary[method] = {"test_cases": total, "accepted": accepted, "abstained": total-accepted,
                          "coverage": accepted/total,
                          "retained_accuracy": sum(r["accepted_correct"] for r in selected)/accepted if accepted else None,
                          "no_admissible_cal_jobs": sum(r["policy"]["threshold"] is None for r in selected),
                          "nonempty_test_jobs": sum(bool(r["accepted"]) for r in selected),
                          "test_target_met_jobs": sum(r["test_empirical_target_met"] for r in selected),
                          "unseen_cases": sum(r["unseen_cases"] for r in selected),
                          "unseen_accepted": sum(r["unseen_accepted"] for r in selected)}
    return {"scope": "research_only_cal_selected_case_renderer_ensemble_not_clinical_or_single_input_policy",
            "total": len(records), "failed": 0, "source_result_sha256": hashlib.sha256(blob).hexdigest(),
            "saved_models_verified": verification["total"], "new_fits": 0, "temperature_changed": False,
            "clinical_accuracy": None, "selection_inputs": "cal_cases_only_before_test", "summary": summary, "records": records}
