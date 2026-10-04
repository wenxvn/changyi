"""Full legacy-alias denominator, not Chinese clinical coverage or accuracy."""
from collections import Counter
import json
from pathlib import Path


def summarize(rows):
    for row in rows:
        for key in ("accepted", "public_model_visible", "high_posterior", "safety_gated", "pass"):
            if type(row[key]) is not bool:
                raise ValueError("Explicit boolean status required")
        if row["accepted"] == bool(row["abstain_reason"]):
            raise ValueError("Acceptance and abstention reason disagree")
        if (row["public_model_visible"] or row["high_posterior"]) and not row["accepted"]:
            raise ValueError("An abstention cannot carry accepted predictions")
    total = len(rows)
    accepted = sum(row["accepted"] for row in rows)
    return {
        "total": total, "accepted": accepted, "abstained": total - accepted,
        "public_model_visible": sum(row["public_model_visible"] for row in rows),
        "accepted_hidden_by_safety": sum(row["accepted"] and row["safety_gated"] and not row["public_model_visible"] for row in rows),
        "accepted_unexpectedly_hidden": sum(row["accepted"] and not row["safety_gated"] and not row["public_model_visible"] for row in rows),
        "high_posterior_among_accepted": sum(row["high_posterior"] for row in rows),
        "high_posterior_threshold": 0.90,
        "abstention_reasons": dict(Counter(row["abstain_reason"] for row in rows if not row["accepted"])),
        "unique_texts": len({row["text"] for row in rows}),
        "unique_aliases": len({row["alias"] for row in rows}),
        "unique_legacy_codes": len({row["legacy_code"] for row in rows}),
        "failed": sum(not row["pass"] for row in rows),
    }


def run():
    import app
    root = Path(__file__).resolve().parents[2]
    aliases = json.loads((root / "data/symptom_disease_model/symptom_alias_zh.json").read_text(encoding="utf-8"))
    rows = []
    client = app.app.test_client()
    for alias, code in sorted(aliases.items()):
        for template, text in (("single_alias", alias), ("alias_plus_cough", alias + "和咳嗽")):
            prediction = app.predict_disease_name(text, details=True)
            data = client.post("/api/v1/triage", json={"condition": text}).get_json()["data"]
            public = data["disease_prediction"]
            accepted = prediction["abstained"] is False
            raw_predictions = prediction.get("predictions", [])
            visible = bool(public.get("predictions"))
            gated = data["triage_status"] in ("EMERGENCY", "INSUFFICIENT_INFORMATION")
            passed = accepted == bool(raw_predictions) and (not gated or not visible)
            passed = passed and (gated or visible == accepted)
            rows.append({"alias": alias, "legacy_code": code, "template": template, "text": text,
                         "accepted": accepted, "abstain_reason": prediction.get("abstain_reason") if not accepted else None,
                         "public_model_visible": visible, "public_abstain_reason": public.get("abstain_reason"),
                         "safety_gated": gated,
                         "triage_status": data["triage_status"],
                         "high_posterior": accepted and max((p["probability"] for p in raw_predictions), default=0) >= 0.90,
                         "mapping_review": prediction.get("mapping_review"),
                         "clinical_semantics_verified": False, "pass": passed})
    summary = summarize(rows)
    return {"scope": "legacy_alias_two_template_serving_denominator_not_clinical_coverage_or_calibration",
            **summary, "by_template": {template: summarize([row for row in rows if row["template"] == template])
                                      for template in ("single_alias", "alias_plus_cough")}, "rows": rows}
