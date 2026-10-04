"""Explicit hypothetical-risk confirmation contract, not clinical risk validation."""
CASES = (
    ("如果我不否认呼吸困难", "INSUFFICIENT_INFORMATION"),
    ("假如我现在不否认呼吸困难", "INSUFFICIENT_INFORMATION"),
    ("我不否认呼吸困难", "EMERGENCY"),
    ("如果我现在呼吸困难", "INSUFFICIENT_INFORMATION"),
    ("如果我呼吸困难，但我现在持续胸痛喘不上气", "EMERGENCY"),
    ("以前我不否认呼吸困难，现在咳嗽", "ROUTINE"),
    ("我不否认没有胸痛", "ROUTINE"),
    ("我不否认咳嗽但未见胸痛", "ROUTINE"),
    ("我不否认呼吸困难但不确定是否咳嗽", "EMERGENCY"),
)


def run():
    import app
    rows = []
    for text, expected in CASES:
        data = app.app.test_client().post("/api/v1/triage", json={"condition": text}).get_json()["data"]
        passed = data["triage_status"] == expected
        if expected == "INSUFFICIENT_INFORMATION":
            passed = passed and data["matched_department"] is None and data["triage"].get("defer_resource_routing") is True
        if expected in ("INSUFFICIENT_INFORMATION", "EMERGENCY"):
            passed = passed and not data["disease_prediction"].get("predictions")
        rows.append({"text": text, "expected_status": expected, "triage_status": data["triage_status"],
                     "matched_department": data["matched_department"], "defer_resource_routing": data["triage"].get("defer_resource_routing"),
                     "pass": bool(passed)})
    return {"scope": "synthetic_explicit_hypothetical_risk_confirmation_not_clinical_validation",
            "total": len(rows), "failed": sum(not row["pass"] for row in rows), "rows": rows}
