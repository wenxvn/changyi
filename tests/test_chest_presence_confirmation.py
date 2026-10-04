from unittest.mock import patch
from backend.app import composition
from evaluation.core_exploration.chest_presence_confirmation_audit import run


def test_qualified_denial_requires_current_presence_confirmation():
    result = run()
    assert result["failed"] == 0, [row for row in result["rows"] if not row["pass"]]


def test_presence_gate_does_not_depend_on_available_model():
    client = composition.app.test_client()
    with patch.object(composition.SYMPTOM_DISEASE_MODEL_ADAPTER, "_runtime_or_injected", return_value=None):
        data = client.post("/api/v1/triage", json={"condition": "没有严重胸痛"}).get_json()["data"]
    assert data["triage_status"] == "INSUFFICIENT_INFORMATION"
    assert data["matched_department"] is None
