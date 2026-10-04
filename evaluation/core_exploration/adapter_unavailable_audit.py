"""Full shared adapter failure seams, not website-wide outage simulation."""
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch
from .auxiliary_route_counterfactual import PROMPTS, signature

MODES = ("injected_loader_none", "missing_model_file")


def run():
    from backend.app import composition
    adapter = composition.SYMPTOM_DISEASE_MODEL_ADAPTER
    missing = Path("__synthetic_missing_model_for_dependency_audit__.json")
    if missing.exists():
        raise ValueError("Synthetic failure path unexpectedly exists")
    adapter._load_runtime()
    fields = ("_runtime", "_runtime_error", "_runtime_loader", "_runtime_loader_called", "model_path")
    original = {field: getattr(adapter, field) for field in fields}
    client = composition.app.test_client()
    baselines, rows = [], []
    for text in PROMPTS:
        baseline = client.post("/api/v1/triage", json={"condition": text}).get_json()["data"]
        reference = signature(baseline)
        baselines.append({"text": text, "signature": reference, "available": baseline["disease_prediction"]["available"]})
        for mode in MODES:
            overrides = {"_runtime": None, "_runtime_error": None, "_runtime_loader_called": False,
                         "_runtime_loader": (lambda: None) if mode == "injected_loader_none" else None}
            if mode == "missing_model_file":
                overrides["model_path"] = missing
            with ExitStack() as stack:
                for field, value in overrides.items():
                    stack.enter_context(patch.object(adapter, field, value))
                data = client.post("/api/v1/triage", json={"condition": text}).get_json()["data"]
                public = data["disease_prediction"]
                internal = data["htriage_analysis"]["model_disease_prediction"]
                reason = public.get("auxiliary_abstain_reason", public.get("abstain_reason"))
                passed = signature(data) == reference and baseline["disease_prediction"]["available"] is True
                passed = passed and public.get("available") is False and internal.get("available") is False
                passed = passed and not public.get("predictions") and not internal.get("predictions")
                passed = passed and public.get("abstained") is True and reason == "model_unavailable"
                rows.append({"text": text, "mode": mode, "baseline": reference, "observed": signature(data),
                             "public_available": public.get("available"), "internal_available": internal.get("available"),
                             "abstain_reason": public.get("abstain_reason"), "underlying_reason": reason, "pass": bool(passed)})
    restored = all(getattr(adapter, field) is value for field, value in original.items())
    return {"scope": "shared_adapter_two_failure_seams_not_full_website_outage_or_clinical_validation",
            "baseline_inputs": len(baselines), "modes": list(MODES), "total": len(rows),
            "failed": sum(not row["pass"] for row in rows) + int(not restored),
            "adapter_state_restored": restored, "baselines": baselines, "rows": rows}
