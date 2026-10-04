import app


def test_relative_history_is_background_for_explicit_current_self():
    data = app.app.test_client().post("/api/v1/triage", json={"condition": "我妈妈确诊糖尿病，现在我咳嗽"}).get_json()["data"]
    assert not data["htriage_analysis"]["known_disease"]["has_known_disease"]
    assert data["matched_department"] != "内分泌代谢科"
    assert "糖尿病" in data["htriage_analysis"]["known_disease"]["background_mentions"]
    assert data["original_condition"] == "我妈妈确诊糖尿病，现在我咳嗽"


def test_proxy_consultation_keeps_relative_report():
    assert app.detect_known_disease("我现在帮我妈妈咨询，她确诊糖尿病")["has_known_disease"]


def test_own_report_is_not_erased_by_relative_context():
    known = app.detect_known_disease("我确诊乙肝，我妈妈确诊糖尿病，现在我自己来复诊")
    assert known["has_known_disease"]
    assert known["disease"] == "乙肝"


def test_current_relative_emergency_is_not_hidden_by_self_route_scope():
    data = app.app.test_client().post("/api/v1/triage", json={"condition": "我妈妈正在呼吸困难，现在我咳嗽"}).get_json()["data"]
    assert data["triage_status"] == "EMERGENCY"
