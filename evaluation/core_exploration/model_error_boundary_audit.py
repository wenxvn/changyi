"""Synthetic marker-only public error boundary, no real secrets or paths."""
from contextlib import ExitStack
from unittest.mock import patch
from .auxiliary_route_counterfactual import signature

PROMPTS = ("咳嗽", "抽搐", "持续胸痛喘不上气")
MARKER = "synthetic_private_diagnostic_marker"


def fail_loader():
    raise ValueError(MARKER)


def run():
    from backend.app import composition
    adapter = composition.SYMPTOM_DISEASE_MODEL_ADAPTER
    adapter._load_runtime()
    fields = ("_runtime", "_runtime_error", "_runtime_loader", "_runtime_loader_called")
    original = {field: getattr(adapter, field) for field in fields}
    client = composition.app.test_client()
    rows = []
    for text in PROMPTS:
        baseline = signature(client.post("/api/v1/triage", json={"condition": text}).get_json()["data"])
        overrides = {"_runtime": None, "_runtime_error": None, "_runtime_loader": fail_loader, "_runtime_loader_called": False}
        with ExitStack() as stack:
            for field, value in overrides.items():
                stack.enter_context(patch.object(adapter, field, value))
            response = client.post("/api/v1/triage", json={"condition": text})
            data = response.get_json()["data"]
            public = data["disease_prediction"]
            internal_public = data["htriage_analysis"]["model_disease_prediction"]
            absent = MARKER not in response.get_data(as_text=True)
            diagnostic_retained = adapter.runtime_error == MARKER
            generic_codes = public.get("error") == internal_public.get("error") == "model_unavailable"
            passed = absent and diagnostic_retained and generic_codes and signature(data) == baseline
            passed = passed and public["available"] is False and public["abstained"] is True and bool(public.get("notice"))
            rows.append({"text": text, "marker_absent_from_response": absent, "internal_diagnostic_retained": diagnostic_retained,
                         "public_error_codes_generic": generic_codes, "signature": signature(data), "baseline": baseline,
                         "abstain_reason": public["abstain_reason"], "pass": bool(passed)})
    restored = all(getattr(adapter, field) is value for field, value in original.items())
    return {"scope": "synthetic_model_exception_publication_boundary_not_complete_security_audit",
            "total": len(rows), "failed": sum(not row["pass"] for row in rows) + int(not restored),
            "adapter_state_restored": restored, "rows": rows}
