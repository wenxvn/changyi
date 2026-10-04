"""New controls against saved W54 observations; never replay old inputs."""
import hashlib
import json
from pathlib import Path

SOURCE_RUN = "w54-current-clause-uncertainty"
CONTROLS = ("现在是否咳嗽", "现在不确定是否咳嗽", "现在可能咳嗽")


def run():
    import app
    from evaluation.core_exploration.versioned_challenge import ROOT, identity
    directory = ROOT / "evaluation/core_exploration/results/versioned-challenges" / SOURCE_RUN
    source_bytes = (directory / "result.json").read_bytes()
    source = json.loads(source_bytes)
    old = json.loads((directory / "prepared.json").read_text(encoding="utf-8"))["identity"]
    current = identity()
    selected = {key: value for key, value in old["code"].items()
                if key.startswith("backend/app/") or key in ("app.py", "data/symptom_disease_model/inference.py")}
    if not selected or any(current["code"].get(key) != value for key, value in selected.items()):
        raise ValueError("Declared runtime source changed; old comparison requires a new protocol")
    for key in ("json_csv_inputs", "serving_model_inputs", "configuration_overrides", "software"):
        if old[key] != current[key]:
            raise ValueError("Declared runtime inputs changed")
    saved = {row["text"]: row for row in source["rows"]}
    rows = []
    client = app.app.test_client()
    for text in CONTROLS:
        previous = saved["没有胸痛，" + text]
        response = client.post("/api/v1/triage", json={"condition": text})
        data = response.get_json()["data"]
        snapshot = {"text": text, "triage_status": data["triage_status"],
                    "matched_department": data["matched_department"],
                    "direct_department_match": app.match_department(text),
                    "abstained": data["disease_prediction"]["abstained"],
                    "abstain_reason": data["disease_prediction"].get("abstain_reason")}
        same = all(snapshot[key] == previous[key] for key in
                   ("triage_status", "matched_department", "abstained", "abstain_reason"))
        rows.append({"new_control": snapshot, "saved_comparison": previous,
                     "saved_comparison_replayed": False, "observed_policy_same": same,
                     "pass": response.status_code == 200 and data["original_condition"] == text,
                     "clinical_label_verified": False})
    return {"scope": "paired_nonclinical_route_observation_not_causal_or_clinical_validation",
            "source_run": SOURCE_RUN, "source_result_sha256": hashlib.sha256(source_bytes).hexdigest(),
            "declared_runtime_subset_verified": True, "new_api_inputs": len(rows),
            "total": len(rows), "failed": sum(not row["pass"] for row in rows),
            "same_policy_pairs": sum(row["observed_policy_same"] for row in rows),
            "clinical_accuracy": None, "rows": rows}
