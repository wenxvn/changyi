import pytest
import app
from backend.app.domain.medical_input import known_disease_mention_state
from evaluation.core_exploration.completed_exclusion_fact_audit import CASES


@pytest.mark.parametrize("text,known,disease", CASES)
def test_completed_exclusion_does_not_create_a_known_disease(text, known, disease):
    fact = app.detect_known_disease(text)
    assert fact["has_known_disease"] is known and fact["disease"] == disease


@pytest.mark.parametrize("prefix", ["医生未能明确排除", "医生将明确排除"])
def test_blocked_or_future_exclusion_is_not_reported_as_completed(prefix):
    assert known_disease_mention_state(prefix + "糖尿病", "糖尿病") == "uncertain"


def test_exclusion_fact_does_not_disable_independent_current_danger():
    data = app.app.test_client().post("/api/v1/triage", json={"condition": "医生已经排除糖尿病，我喘不上气"}).get_json()["data"]
    assert data["triage_status"] == "EMERGENCY"
