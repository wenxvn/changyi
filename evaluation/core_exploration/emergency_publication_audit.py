"""Cross-endpoint Safety publication counts, never catalog identity records."""
CASES = (
    ("我现在喘不上气", "EMERGENCY"),
    ("我现在是否喘不上气，我喘不上气", "EMERGENCY"),
    ("现在咳嗽是不是，我喘不上气", "EMERGENCY"),
    ("我现在是否喘不上气", "INSUFFICIENT_INFORMATION"),
)


def run():
    import app
    from backend.app.domain.triage.safety_gate import triage_status_from_legacy
    rows = []
    client = app.app.test_client()
    for text, expected in CASES:
        first = client.post("/api/v1/triage", json={"condition": text})
        second = client.post("/api/v1/recommendations", json={"condition": text})
        triage, recommendation = first.get_json()["data"], second.get_json()["data"]
        status = recommendation.get("triage_status") or triage_status_from_legacy(recommendation["triage"]).value
        hospitals = len(recommendation.get("recommended_hospitals", []))
        doctors = len(recommendation.get("recommended_doctors", []))
        passed = first.status_code == second.status_code == 200 and triage["triage_status"] == status == expected
        passed = passed and not triage["disease_prediction"].get("predictions") and not recommendation["disease_prediction"].get("predictions")
        if expected == "INSUFFICIENT_INFORMATION":
            passed = passed and triage["matched_department"] is None and hospitals == doctors == 0
        rows.append({"text": text, "expected_existing_policy_status": expected,
                     "triage_status": triage["triage_status"], "recommendation_status": status,
                     "triage_department": triage["matched_department"],
                     "recommendation_department": recommendation["matched_department"],
                     "hospital_count": hospitals, "doctor_count": doctors,
                     "emergency_general_department": expected == "EMERGENCY" and triage["matched_department"] == "全科医学科",
                     "emergency_doctors_published": expected == "EMERGENCY" and doctors > 0,
                     "clinical_label_verified": False, "pass": bool(passed)})
    return {"scope": "website_safety_publication_observation_not_clinical_department_labels",
            "total": len(rows), "failed": sum(not r["pass"] for r in rows),
            "emergency_general_department_rows": sum(r["emergency_general_department"] for r in rows),
            "emergency_doctors_published_rows": sum(r["emergency_doctors_published"] for r in rows),
            "clinical_accuracy": None, "rows": rows}
