"""Observe qualifier scope across layers; deliberately no clinical oracle."""
from collections import Counter

CASES = (
    ("没有持续抽搐", "抽搐", "muscle_pain", "qualified_duration"),
    ("没有严重胸痛", "胸痛", "chest_pain", "qualified_severity"),
    ("我没有严重胸痛但有轻微胸痛", "胸痛", "chest_pain", "qualified_then_parent_report"),
    ("没有明显呼吸困难", "呼吸困难", "breathlessness", "qualified_prominence"),
    ("没有持续咳嗽但偶尔咳嗽", "咳嗽", "cough", "qualified_then_parent_report"),
    ("没有胸痛", "胸痛", "chest_pain", "clear_denial"),
    ("我有持续胸痛喘不上气", "胸痛", "chest_pain", "reported_emergency"),
    ("没有咳嗽", "咳嗽", "cough", "clear_denial"),
    ("没有高烧但有低烧", "高烧", "high_fever", "grade_control"),
)


def summarize(rows):
    for row in rows:
        for field in ("rule_positive", "aux_code_present", "layer_disagreement", "execution_valid", "clinical_label_verified"):
            if type(row[field]) is not bool:
                raise ValueError("Explicit observation boolean required")
        if row["layer_disagreement"] != (row["rule_positive"] != row["aux_code_present"]):
            raise ValueError("Inconsistent layer comparison")
    return {"total": len(rows), "failed": sum(not row["execution_valid"] for row in rows),
            "layer_disagreements": sum(row["layer_disagreement"] for row in rows),
            "clinical_verified_rows": sum(row["clinical_label_verified"] for row in rows),
            "groups": dict(Counter(row["group"] for row in rows)),
            "clinical_accuracy": None}


def run():
    import app
    rows = []
    for text, word, code, group in CASES:
        prediction = app.predict_disease_name(text, details=True)
        assertions = prediction.get("input_assertions", {})
        data = app.app.test_client().post("/api/v1/triage", json={"condition": text}).get_json()["data"]
        rule_positive = app.contains_current_safety_signal(text, [word])
        aux_present = code in assertions.get("present", [])
        valid = data["triage_status"] in {"ROUTINE", "URGENT", "EMERGENCY", "INSUFFICIENT_INFORMATION"}
        rows.append({"text": text, "target_word": word, "legacy_code": code, "group": group,
                     "rule_positive": rule_positive, "aux_code_present": aux_present,
                     "layer_disagreement": rule_positive != aux_present, "execution_valid": valid,
                     "clinical_label_verified": False, "assertions": assertions,
                     "abstained": prediction["abstained"], "abstain_reason": prediction.get("abstain_reason"),
                     "mapping_review": prediction.get("mapping_review"),
                     "triage_status": data["triage_status"], "matched_department": data["matched_department"]})
    return {"scope": "qualified_denial_layer_observation_no_clinical_oracle_no_runtime_change",
            **summarize(rows), "rows": rows}
