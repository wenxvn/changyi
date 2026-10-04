"""Bounded language evidence audit, with no clinical routing oracle."""
CASES = (
    ("没有胸痛，现在咳嗽", True),
    ("去年没有严重胸痛，现在咳嗽", True),
    ("没有发烧，目前咳嗽", True),
    ("没有胸痛，但咳嗽", True),
    ("去年没有胸痛。现在咳嗽", True),
    ("没有胸痛和咳嗽", False),
    ("没有胸痛，现在也没有咳嗽", False),
)


def run():
    import app
    from backend.app.domain.medical_input import contains_positive
    rows = []
    client = app.app.test_client()
    for text, expected in CASES:
        response = client.post("/api/v1/triage", json={"condition": text})
        data = response.get_json()["data"]
        observed = contains_positive(text, ["咳嗽"])
        rows.append({"text": text, "expected_cough_evidence": expected,
                     "observed_cough_evidence": observed,
                     "pass": observed == expected,
                     "execution_valid": response.status_code == 200,
                     "triage_status": data["triage_status"],
                     "matched_department": data["matched_department"],
                     "clinical_label_verified": False})
    return {"scope": "explicit_current_clause_language_evidence_no_clinical_oracle",
            "total": len(rows), "failed": sum(not r["pass"] for r in rows),
            "execution_failures": sum(not r["execution_valid"] for r in rows),
            "clinical_accuracy": None, "rows": rows}
