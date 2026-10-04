"""Is-it/negative existence queries under the existing confirmation policy."""
CASES = (
    ("我现在是不是喘不上气", "INSUFFICIENT_INFORMATION"),
    ("我现在是不是有呼吸困难", "INSUFFICIENT_INFORMATION"),
    ("我现在是不是没有呼吸困难", "INSUFFICIENT_INFORMATION"),
    ("我现在是不是没有意识不清", "INSUFFICIENT_INFORMATION"),
    ("我现在是不是持续抽搐", "INSUFFICIENT_INFORMATION"),
    ("我现在持续抽搐", "EMERGENCY"),
    ("我现在是不是呼吸困难，我喘不上气", "EMERGENCY"),
    ("我现在不是呼吸困难", "ROUTINE"),
)


def run():
    import app
    rows = []
    client = app.app.test_client()
    for text, expected in CASES:
        data = client.post("/api/v1/triage", json={"condition": text}).get_json()["data"]
        passed = data["triage_status"] == expected and data["original_condition"] == text
        if expected == "INSUFFICIENT_INFORMATION":
            passed = passed and data["matched_department"] is None and data["triage"].get("defer_resource_routing") is True
            passed = passed and any(q["id"] == "red_flag_check" for q in data["triage"]["followup"]["questions"])
        rows.append({"text": text, "expected_policy_status": expected, "status": data["triage_status"],
                     "matched_department": data["matched_department"], "clinical_label_verified": False, "pass": bool(passed)})
    return {"scope": "bounded_copula_existence_safety_policy_not_clinical_accuracy",
            "total": len(rows), "failed": sum(not r["pass"] for r in rows), "rows": rows}
