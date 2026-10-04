import pytest
import app
from backend.app.domain.medical_input import known_disease_mention_state
from evaluation.core_exploration.qualified_unresolved_exclusion_audit import CASES


@pytest.mark.parametrize("text,status", CASES)
def test_qualified_exclusion_failure_retains_existing_priority(text, status):
    data = app.app.test_client().post("/api/v1/triage", json={"condition": text}).get_json()["data"]
    if status == "NOT_EMERGENCY":
        assert data["triage_status"] != "EMERGENCY"
    else:
        assert data["triage_status"] == status


@pytest.mark.parametrize("prefix", ["未能够明确排除", "无法完全排除", "不能明确排除"])
def test_failure_to_exclude_is_not_a_completed_or_known_fact(prefix):
    assert known_disease_mention_state(prefix + "糖尿病", "糖尿病") == "uncertain"


def test_completed_exclusion_fact_remains_distinct():
    assert known_disease_mention_state("医生明确排除糖尿病", "糖尿病") == "absent"
