import pytest
import app


@pytest.mark.parametrize("cue", ["呼吸困难", "喘不上气", "意识不清", "呼之不应"])
@pytest.mark.parametrize("ending", ["仍未恢复", "一直没有好"])
def test_explicit_unresolved_strong_signal_is_not_lost_as_history(cue, ending):
    data = app.app.test_client().post("/api/v1/triage", json={"condition": f"以前{cue}{ending}"}).get_json()["data"]
    assert data["triage_status"] == "EMERGENCY"


@pytest.mark.parametrize("condition", ["科普：以前呼吸困难仍未恢复是什么意思", "以前呼吸困难，现在没有呼吸困难", "以前意识不清，已经好了", "以前没有呼吸困难，只是咳嗽"])
def test_educational_resolved_or_denied_report_does_not_gain_current_override(condition):
    data = app.app.test_client().post("/api/v1/triage", json={"condition": condition}).get_json()["data"]
    assert data["triage_status"] != "EMERGENCY"


@pytest.mark.parametrize("condition", ["我刚刚突然说话不清，现在好了", "我刚刚一侧无力，现在消失了"])
def test_recent_stroke_like_signal_is_not_downgraded_because_it_disappeared(condition):
    data = app.app.test_client().post("/api/v1/triage", json={"condition": condition}).get_json()["data"]
    assert data["triage_status"] == "EMERGENCY"
