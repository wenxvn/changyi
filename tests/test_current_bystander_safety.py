import pytest
import app


@pytest.mark.parametrize("cue", app.TRIAGE_CRITICAL_SINGLE_KEYWORDS)
def test_current_bystander_is_not_downgraded_for_existing_critical_cue(cue):
    data = app.app.test_client().post("/api/v1/triage", json={"condition": f"我妈妈正在{cue}"}).get_json()["data"]
    assert data["triage_status"] == "EMERGENCY"


@pytest.mark.parametrize("condition", ["如果我妈妈正在呼吸困难会怎样", "科普：我妈妈正在呼吸困难是什么意思", "我妈妈以前呼吸困难，现在好了", "我妈妈现在没有呼吸困难"])
def test_noncurrent_or_denied_bystander_does_not_gain_emergency(condition):
    data = app.app.test_client().post("/api/v1/triage", json={"condition": condition}).get_json()["data"]
    assert data["triage_status"] != "EMERGENCY"
