from functools import partial
import json
import pytest
from evaluation.core_exploration.versioned_challenge import ROOT, CONFIGURATION_KEYS, SERVING_MODEL_INPUTS, identity, prepare, execute


def test_configuration_drift_is_detected_before_runner(tmp_path, monkeypatch):
    monkeypatch.delenv("CHANGYI_REGION_CODE", raising=False)
    capture = partial(identity, tmp_path)
    before = capture()
    directory = prepare(tmp_path / "runs", "configuration-before", "known_disease_audit", capture)
    monkeypatch.setenv("CHANGYI_REGION_CODE", "320401")
    assert capture() != before
    calls = []
    with pytest.raises(RuntimeError, match="not executed"):
        execute(directory, capture, lambda: calls.append(True))
    assert not calls and not (directory / "started.json").exists()


def test_configuration_drift_during_runner_invalidates_result(tmp_path, monkeypatch):
    monkeypatch.delenv("CHANGYI_MODEL_VERSION", raising=False)
    capture = partial(identity, tmp_path)
    directory = prepare(tmp_path / "runs", "configuration-during", "known_disease_audit", capture)
    def runner():
        monkeypatch.setenv("CHANGYI_MODEL_VERSION", "synthetic-test-version")
        return {"scope": "test_only", "failed": 0}
    with pytest.raises(RuntimeError, match="diagnostic result retained"):
        execute(directory, capture, runner)
    assert json.loads((directory / "completed.json").read_text())["status"] == "INVALIDATED_IDENTITY_DRIFT"


def test_model_file_is_already_in_declared_json_input_hashes():
    import app
    from pathlib import Path
    model = Path(app.SYMPTOM_DISEASE_MODEL_PATH).relative_to(ROOT).as_posix()
    snapshot = identity()
    assert model in snapshot["json_csv_inputs"]
    assert snapshot["serving_model_inputs"]["model_weights"]["path"] == model
    assert all(item["state"] == "present" for item in snapshot["serving_model_inputs"].values())


def test_configuration_capture_is_allowlisted_and_hash_only(tmp_path, monkeypatch):
    value = "synthetic-config-value-not-a-secret"
    monkeypatch.setenv("CHANGYI_MODEL_VERSION", value)
    monkeypatch.setenv("UNRELATED_TEST_CREDENTIAL", "synthetic-excluded-value")
    snapshot = identity(tmp_path)
    configuration = snapshot["configuration_overrides"]
    assert set(configuration) == set(CONFIGURATION_KEYS)
    assert configuration["CHANGYI_MODEL_VERSION"]["state"] == "set"
    assert len(configuration["CHANGYI_MODEL_VERSION"]["sha256"]) == 64
    assert value not in json.dumps(snapshot)
    assert "UNRELATED_TEST_CREDENTIAL" not in json.dumps(snapshot)
    monkeypatch.setenv("CHANGYI_MODEL_VERSION", "")
    empty = identity(tmp_path)
    monkeypatch.delenv("CHANGYI_MODEL_VERSION")
    assert empty != identity(tmp_path)


def test_declared_weight_content_change_updates_both_hash_records(tmp_path):
    weight = tmp_path / SERVING_MODEL_INPUTS["model_weights"]
    weight.parent.mkdir(parents=True)
    weight.write_text('{"weight":1}', encoding="utf-8")
    before = identity(tmp_path)
    weight.write_text('{"weight":2}', encoding="utf-8")
    after = identity(tmp_path)
    assert before["serving_model_inputs"]["model_weights"]["sha256"] != after["serving_model_inputs"]["model_weights"]["sha256"]
    assert after["serving_model_inputs"]["model_weights"]["sha256"] == after["json_csv_inputs"][SERVING_MODEL_INPUTS["model_weights"]]


def test_missing_declared_inputs_are_explicit(tmp_path):
    snapshot = identity(tmp_path)
    assert all(item["state"] == "missing" for item in snapshot["serving_model_inputs"].values())
    assert snapshot["schema_version"] == 3
