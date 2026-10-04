"""Website publication policy; no ranking identities or clinical new labels."""
from .emergency_publication_audit import CASES


def run():
    import app
    from backend.app.domain.triage.safety_gate import triage_status_from_legacy
    rows = []
    client = app.app.test_client()
    for text, expected in (*CASES, ("咳嗽", "ROUTINE"), ("我确诊糖尿病", "URGENT")):
        response = client.post("/api/v1/recommendations", json={"condition": text})
        data = response.get_json()["data"]
        status = triage_status_from_legacy(data["triage"]).value
        doctors, hospitals = len(data["recommended_doctors"]), len(data["recommended_hospitals"])
        passed = response.status_code == 200 and status == expected
        if expected == "EMERGENCY":
            passed = passed and doctors == 0 and hospitals > 0 and data["weights_used"] == {}
        elif expected == "INSUFFICIENT_INFORMATION":
            passed = passed and doctors == hospitals == 0
        else:
            passed = passed and doctors > 0 and hospitals > 0
        rows.append({"text": text, "expected_status": expected, "status": status,
                     "doctor_count": doctors, "hospital_count": hospitals,
                     "doctor_weights_empty": data["weights_used"] == {},
                     "clinical_label_verified": False, "pass": bool(passed)})
    return {"scope": "emergency_regular_doctor_publication_boundary_not_clinical_capability",
            "total": len(rows), "failed": sum(not r["pass"] for r in rows), "rows": rows}
