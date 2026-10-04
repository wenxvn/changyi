import pytest
import app
from evaluation.core_exploration.routing_topic_audit import TOPICS


@pytest.mark.parametrize("topic", TOPICS)
def test_non_disease_topic_keeps_direction_without_inventing_disease(topic):
    data = app.app.test_client().post("/api/v1/triage", json={"condition": topic}).get_json()["data"]
    htriage = data["htriage_analysis"]
    assert not htriage["known_disease"]["has_known_disease"]
    assert not any(row["name"] == topic for row in htriage["disease_candidates"])
    assert data["matched_department"] == app.DISEASE_DEPT_MAP[topic]
    assert not any(q["id"] == "known_disease_status" for q in data["triage"]["followup"]["questions"])


@pytest.mark.parametrize("topic", ["中医", "产科"])
def test_confirmation_cannot_turn_a_topic_into_a_disease(topic):
    data = app.app.test_client().post("/api/v1/triage", json={"condition": topic, "followup_answers": [{"question_id": "known_disease_status", "value": "confirmed"}]}).get_json()["data"]
    assert not data["htriage_analysis"]["known_disease"]["has_known_disease"]


def test_real_disease_and_pregnancy_emergency_are_preserved():
    assert app.detect_known_disease("糖尿病已确诊，想看中医")["disease"] == "糖尿病"
    data = app.app.test_client().post("/api/v1/triage", json={"condition": "分娩，羊水破了"}).get_json()["data"]
    assert data["triage_status"] == "EMERGENCY"
