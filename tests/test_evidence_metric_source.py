import hashlib
import pytest
from backend.app.application.evidence import _model_metric_label


def fixture(tmp_path):
    path = tmp_path / "synthetic-model.json"
    path.write_bytes(b"synthetic fitted state")
    report = {"model": {"sha256": hashlib.sha256(path.read_bytes()).hexdigest()},
              "random_baseline": {"accuracy": .972973, "test_rows": 74}}
    return path, report


def test_matching_fitted_state_and_rounded_metrics_identify_random_reference(tmp_path):
    path, report = fixture(tmp_path)
    assert "随机切分基线" in _model_metric_label(path, {"accuracy": 72/74, "test_rows": 74}, report)


def test_equal_numbers_do_not_override_a_wrong_model_identity(tmp_path):
    path, report = fixture(tmp_path)
    report["model"]["sha256"] = "different"
    assert "待核对" in _model_metric_label(path, {"accuracy": .972973, "test_rows": 74}, report)


def test_metric_drift_prevents_a_provenance_claim(tmp_path):
    path, report = fixture(tmp_path)
    assert "待核对" in _model_metric_label(path, {"accuracy": .9, "test_rows": 74}, report)


def test_missing_file_does_not_fabricate_a_split_label(tmp_path):
    path, report = fixture(tmp_path)
    assert "待核对" in _model_metric_label(tmp_path / "missing.json", {"accuracy": .972973, "test_rows": 74}, report)


@pytest.mark.parametrize("value", [float("nan"), True])
def test_invalid_numeric_metric_does_not_claim_verified_provenance(tmp_path, value):
    path, report = fixture(tmp_path)
    assert "待核对" in _model_metric_label(path, {"accuracy": value, "test_rows": 74}, report)
