"""Controlled htriage-helper dependency test, not full model-failure simulation."""
from unittest.mock import patch

PROMPTS = ("低烧", "cough", "头昏", "鼻塞", "已确诊糖尿病", "假如咳嗽",
           "持续胸痛喘不上气", "抽搐")
MODES = ("unavailable", "unrelated_high", "unrelated_low")


def substitute(mode):
    def predict(condition, details=False):
        unavailable = mode == "unavailable"
        first_probability, second_probability = (0.9999, 0.0001) if mode == "unrelated_high" else (0.03, 0.025)
        # Names belong to the existing prototype vocabulary. Values are test
        # intervention parameters, never patient disease probabilities.
        predictions = [] if unavailable else [
            {"disease": "普通感冒", "probability": first_probability},
            {"disease": "糖尿病", "probability": second_probability},
        ]
        return {"available": not unavailable, "disease": "" if unavailable else "普通感冒",
                "abstained": unavailable, "abstain_reason": "model_unavailable" if unavailable else None,
                "predictions": predictions, "normalized_symptoms": [], "known_symptoms": [],
                "unknown_symptoms": [], "aliases": {}, "notice": "synthetic_dependency_intervention"}
    return predict


def signature(data):
    return {"triage_status": data["triage_status"], "matched_department": data["matched_department"],
            "defer_resource_routing": bool(data["triage"].get("defer_resource_routing", False))}


def run():
    from backend.app import composition
    original = composition.predict_disease_name
    client = composition.app.test_client()
    baselines, rows = [], []
    for text in PROMPTS:
        baseline = signature(client.post("/api/v1/triage", json={"condition": text}).get_json()["data"])
        baselines.append({"text": text, "signature": baseline})
        for mode in MODES:
            with patch.object(composition, "predict_disease_name", substitute(mode)):
                observed = signature(client.post("/api/v1/triage", json={"condition": text}).get_json()["data"])
            rows.append({"text": text, "mode": mode, "baseline": baseline, "observed": observed,
                         "pass": observed == baseline})
    restored = composition.predict_disease_name is original
    return {"scope": "controlled_htriage_helper_counterfactual_not_full_adapter_failure_or_clinical_validation",
            "baseline_inputs": len(baselines), "modes": list(MODES), "total": len(rows),
            "failed": sum(not row["pass"] for row in rows) + int(not restored),
            "dependency_restored": restored, "baselines": baselines, "rows": rows}
