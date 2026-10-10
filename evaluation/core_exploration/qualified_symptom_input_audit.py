"""Auxiliary input semantics, engineering policy rather than clinical labels."""
CASES = (
    ("没有严重咳嗽", [], ["cough"], True),
    ("没有严重头痛", [], ["headache"], True),
    ("没有剧烈腹痛", [], ["abdominal_pain"], True),
    ("没有明显咳嗽", [], ["cough"], True),
    ("没有持续咳嗽", [], ["cough"], True),
    ("没有严重头痛，但我确实头痛", ["headache"], [], True),
    ("没有明显咳嗽，但我有头痛", ["headache"], ["cough"], True),
    ("没有咳嗽", [], [], False),
    ("咳嗽不严重", ["cough"], [], False),
)


def run():
    import app
    rows = []
    for text, present, unknown, review in CASES:
        p = app.predict_disease_name(text, details=True)
        a = p["input_assertions"]
        passed = (a["present"] == present and a["unknown"] == unknown
                  and p["input_scope_review"]["required"] is review)
        if review:
            passed = passed and p["abstained"] and p["abstain_reason"] == "qualified_negation_scope_unverified"
        rows.append({"text": text, "assertions": a, "review": p["input_scope_review"],
                     "abstained": p["abstained"], "clinical_label_verified": False, "pass": bool(passed)})
    return {"scope": "auxiliary_qualified_negation_input_not_clinical_validation", "total": len(rows),
            "failed": sum(not row["pass"] for row in rows), "rows": rows}
