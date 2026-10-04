"""Replay saved research states with fixed temperatures; never fit or select."""
import hashlib
import json
import numpy as np
from scipy.special import softmax
from sklearn.feature_extraction import DictVectorizer
from backend.app.domain.symptom_assertions import parse_asserted_symptoms
from .canonical_name_bridge_audit import build_bridge
from .chinese_adaptation import texts_and_labels
from .semantic_bridge import NAMES, ALIASES
from .validation import expanded_metrics
from .versioned_challenge import ROOT, identity
from evaluation.care_routing.round3_split_audit import load_structured


def pooled_metrics(correct, confidence):
    correct, confidence = np.asarray(correct, dtype=bool), np.asarray(confidence, dtype=float)
    if len(correct) != len(confidence) or not np.isfinite(confidence).all():
        raise ValueError("Invalid confidence denominator")
    if not len(correct):
        return {"n": 0, "accuracy": None, "pooled_ece": None, "mean_confidence": None, "wrong_confident_07_count": 0}
    ece = 0.
    for i in range(10):
        mask = (confidence >= i/10) & (confidence <= 1 if i == 9 else confidence < (i+1)/10)
        if mask.any():
            ece += mask.mean()*abs(confidence[mask].mean()-correct[mask].mean())
    return {"n": len(correct), "accuracy": float(correct.mean()), "pooled_ece": float(ece),
            "mean_confidence": float(confidence.mean()), "wrong_confident_07_count": int(((~correct)&(confidence>=.7)).sum())}


def run():
    directory = ROOT / "evaluation/core_exploration/results/versioned-challenges/w64-paired-name-bridge"
    blob = (directory / "result.json").read_bytes()
    source = json.loads(blob)
    old = json.loads((directory / "prepared.json").read_text(encoding="utf-8"))["identity"]
    current = identity()
    specific = {"app.py", "evaluation/core_exploration/semantic_bridge.py", "evaluation/core_exploration/chinese_adaptation.py",
                "evaluation/core_exploration/paired_name_bridge_study.py", "evaluation/core_exploration/canonical_name_bridge_audit.py",
                "evaluation/core_exploration/study.py", "evaluation/core_exploration/validation.py",
                "evaluation/care_routing/disease_department.py", "evaluation/care_routing/round3_split_audit.py"}
    for key, value in old["code"].items():
        if (key.startswith("backend/app/") or key in specific) and current["code"].get(key) != value:
            raise ValueError("Declared saved-model source changed")
    for key in ("json_csv_inputs", "serving_model_inputs", "configuration_overrides", "software"):
        if old[key] != current[key]:
            raise ValueError("Declared saved-model input changed")
    rows = load_structured().rows
    bridge, _, conflicts = build_bridge(NAMES, ALIASES)
    if conflicts:
        raise ValueError("Unresolved saved dictionary conflict")
    pools = {method: {stratum: ([], []) for stratum in ("all", "supported", "unseen")}
             for method in ("current_alias", "declared_name_bridge")}
    records = []
    for record in source["records"]:
        state = record["learned_state"]
        if hashlib.sha256(json.dumps(state, sort_keys=True).encode()).hexdigest() != record["model_identity_sha256"]:
            raise ValueError("Saved fitted-state hash mismatch")
        aliases = ALIASES if record["method"] == "current_alias" else bridge
        texts, y = texts_and_labels([rows[i] for i in record["splits"]["test"]], source["test_templates"], record["seed"]+3)
        vector = DictVectorizer()
        vector.feature_names_ = state["features"]
        vector.vocabulary_ = {name: i for i, name in enumerate(state["features"])}
        features = [{code: 1. for code in parse_asserted_symptoms(text, aliases)["present"]} for text in texts]
        logits = np.asarray(vector.transform(features) @ np.asarray(state["coef"]).T) + np.asarray(state["intercept"])
        if logits.shape[1] == 1:
            logits = np.column_stack((-logits[:, 0], logits[:, 0]))
        probabilities = softmax(logits/record["temperature"], axis=1)
        classes = np.asarray(state["classes"])
        metrics = expanded_metrics(y, probabilities, classes)
        if any(abs(metrics[key]-record["metrics"][key]) > 1e-9 for key in ("accuracy", "ece", "nll")):
            raise ValueError("Saved metric replay mismatch")
        correct = classes[probabilities.argmax(axis=1)] == y
        confidence = probabilities.max(axis=1)
        supported = np.isin(y, classes)
        for stratum, mask in (("all", np.ones(len(y), dtype=bool)), ("supported", supported), ("unseen", ~supported)):
            pooled_correct, pooled_confidence = pools[record["method"]][stratum]
            pooled_correct.extend(correct[mask].tolist())
            pooled_confidence.extend(confidence[mask].tolist())
        records.append({"seed": record["seed"], "fold": record["fold"], "method": record["method"],
                        "model_identity_sha256": record["model_identity_sha256"], "metric_replay_pass": True,
                        "rows": len(y), "supported": int(supported.sum()), "unseen": int((~supported).sum())})
    return {"scope": "saved_research_calibration_strata_not_clinical_validation", "total": len(records), "failed": 0,
            "source_result_sha256": hashlib.sha256(blob).hexdigest(), "new_model_fits": 0, "temperature_changed": False,
            "clinical_accuracy": None, "summary": {method: {stratum: pooled_metrics(*values) for stratum, values in strata.items()}
                for method, strata in pools.items()}, "records": records}
