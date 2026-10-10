import pytest
import app
from backend.app.domain.triage.metabolic_risk import metabolic_emergency_assessment


POSITIVE = (
    "我有1型糖尿病，今天很口渴、排尿很多，还有恶心，但没有意识混乱",
    "我患一型糖尿病。现在恶心口渴尿多",
    "妈妈有1型糖尿病，今天口渴尿频恶心",
    "我有1型糖尿病，今天口渴尿多，胃部轻微不适",
)
NEGATIVE = (
    "我没有1型糖尿病，今天口渴尿多恶心",
    "医生考虑1型糖尿病，今天口渴尿多恶心",
    "不确定是不是1型糖尿病，口渴尿多恶心",
    "如果我有1型糖尿病并口渴尿多恶心怎么办",
    "科普：1型糖尿病口渴尿多恶心是什么",
    "我有1型糖尿病，没有口渴，但尿多恶心",
    "我有1型糖尿病，口渴尿多，没有恶心或呕吐",
    "我有1型糖尿病，口渴恶心，没有尿多",
    "我有1型糖尿病，去年口渴尿多恶心，现在好了",
    "我有1型糖尿病，今天口渴尿多恶心。现在都好了",
    "我有1型糖尿病，今天只是口渴",
    "我妈有1型糖尿病，我今天口渴尿多恶心",
    "我有1型糖尿病，妈妈今天口渴尿多恶心",
    "我有1型糖尿病。今天尿多口渴。恶心已经好了",
    "我有1型糖尿病，不确定是否口渴，但有尿多恶心",
)


@pytest.mark.parametrize("text", POSITIVE)
def test_metabolic_cluster_precedes_ordinary_chronic_followup(text):
    assert metabolic_emergency_assessment(text)
    d = app.app.test_client().post("/api/v1/triage", json={"condition": text}).get_json()["data"]
    assert d["triage_status"] == "EMERGENCY"
    assert d["matched_department"] == "急诊医学科"
    assert not d["disease_prediction"]["predictions"]


@pytest.mark.parametrize("text", NEGATIVE)
def test_absent_noncurrent_uncertain_or_mixed_subject_cluster_is_not_invented(text):
    assert metabolic_emergency_assessment(text) is None


def test_unknown_generic_risk_answer_does_not_override_an_actual_cluster():
    text = POSITIVE[0]
    d = app.app.test_client().post("/api/v1/triage", json={"condition": text,
        "followup_answers": [{"question_id": "red_flag_check", "value": "unknown"}]}).get_json()["data"]
    assert d["triage_status"] == "EMERGENCY"
