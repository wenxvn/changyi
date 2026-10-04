import app
from evaluation.core_exploration.conditional_disease_audit import run


def test_fixed_conditional_report_contract():
    result = run()
    assert result["failed"] == 0, [row for row in result["rows"] if not row["pass"]]


def test_current_emergency_precedes_another_conditional_disease():
    data = app.app.test_client().post("/api/v1/triage", json={"condition": "目前我呼吸困难，假如糖尿病怎么办"}).get_json()["data"]
    assert data["triage_status"] == "EMERGENCY"
