"""Guarded research inference for frozen public-text models, never a clinical API."""
from scipy.special import softmax
from .study import model_logits


def guarded_prediction(state, row, *, safety_status, threshold, input_scope="public_text_research"):
    def abstain(reason):
        return {"department": None, "routing_score": None, "abstained": True, "reason": reason, "safety_status": safety_status, "not_medical_confidence": True}
    if safety_status not in ("ROUTINE", "URGENT"):
        return abstain("safety_exit_precedes_learning")
    if input_scope != "public_text_research":
        return abstain("input_domain_not_validated")
    if not 0 <= threshold <= 1:
        raise ValueError("threshold must be a calibration-derived probability cutoff")
    if not row.get("symptoms"):
        return abstain("empty_symptom_input")
    # Training CSV parsing uses a sorted set; inference must use that same
    # contract, including legacy concat-char winners.
    row = {**row, "symptoms": sorted(set(row["symptoms"]))}
    features = state["vector"].transform([row])
    if features.getnnz() == 0:
        return abstain("no_supported_features")
    p = softmax(model_logits(state["model"], features) / state["temperature"], axis=1)[0]
    if p.max() < threshold:
        return abstain("below_calibration_threshold")
    return {"department": str(state["model"].classes_[p.argmax()]), "routing_score": float(p.max()), "abstained": False, "safety_status": safety_status, "not_medical_confidence": True, "scope": "research_only"}
