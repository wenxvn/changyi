import pytest
import app


@pytest.mark.parametrize("cue", app.TRIAGE_CRITICAL_SINGLE_KEYWORDS)
def test_past_cue_cannot_be_reactivated_by_unrelated_current_symptom(cue):
    data = app.app.test_client().post("/api/v1/triage", json={"condition": f"以前{cue}，现在我咳嗽"}).get_json()["data"]
    assert data["triage_status"] != "EMERGENCY"


@pytest.mark.parametrize("cue", app.TRIAGE_CRITICAL_SINGLE_KEYWORDS)
@pytest.mark.parametrize("current", ["现在我又", "现在又"])
def test_same_cue_recurrence_keeps_existing_emergency_priority(cue, current):
    data = app.app.test_client().post("/api/v1/triage", json={"condition": f"以前{cue}，{current}{cue}"}).get_json()["data"]
    assert data["triage_status"] == "EMERGENCY"


def test_another_current_critical_signal_is_not_erased_by_history():
    data = app.app.test_client().post("/api/v1/triage", json={"condition": "以前心梗，现在我呼吸困难"}).get_json()["data"]
    assert data["triage_status"] == "EMERGENCY"


def test_explicit_current_denial_does_not_reuse_old_positive_occurrence():
    data = app.app.test_client().post("/api/v1/triage", json={"condition": "以前呼吸困难，现在我没有呼吸困难，只是咳嗽"}).get_json()["data"]
    assert data["triage_status"] != "EMERGENCY"


def test_explicit_unresolved_tail_keeps_signal_available():
    data = app.app.test_client().post("/api/v1/triage", json={"condition": "以前呼吸困难仍未恢复，现在我还在呼吸困难"}).get_json()["data"]
    assert data["triage_status"] == "EMERGENCY"
