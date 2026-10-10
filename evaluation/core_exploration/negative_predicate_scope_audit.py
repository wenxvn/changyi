"""Denial grammar policy controls, not new medical urgency labels."""
CASES = (
    ("我不伴胸痛", False, False),
    ("我不伴呼吸困难", False, False),
    ("我未出现呼吸困难", False, False),
    ("我没有出现呼吸困难", False, False),
    ("我不伴有呼吸困难", False, False),
    ("我不是没有咳嗽，但没有呼吸困难", False, False),
    ("我没有意识混乱或抽搐", False, False),
    ("我没有意识混乱和抽搐", False, False),
    ("我不伴胸痛，但呼吸困难", True, False),
    ("我没有意识混乱，但持续抽搐", True, True),
    ("我不是没有呼吸困难", True, False),
    ("我没有严重抽搐", None, True),
)


def run():
    import app
    from backend.app.domain.medical_input import seizure_review_mentions
    rows = []
    for text, emergency, seizure in CASES:
        data = app.app.test_client().post("/api/v1/triage", json={"condition": text}).get_json()["data"]
        signals = seizure_review_mentions(text)
        passed = bool(signals) is seizure
        if emergency is not None:
            passed = passed and (data["triage_status"] == "EMERGENCY") is emergency
        rows.append({"text": text, "status": data["triage_status"], "seizure_review": signals,
                     "expected_emergency": emergency, "clinical_label_verified": False, "pass": bool(passed)})
    return {"scope": "negative_predicate_grammar_controls_not_clinical_validation",
            "total": len(rows), "failed": sum(not r["pass"] for r in rows), "rows": rows}
