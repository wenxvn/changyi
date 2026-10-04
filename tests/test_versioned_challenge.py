import json
import pytest
from evaluation.core_exploration.versioned_challenge import prepare, execute


def test_success_is_exclusive_and_prepared_is_not_execution(tmp_path):
    capture = lambda: {"code": "fixed", "data": "fixed"}
    directory = prepare(tmp_path, "one", "known_disease_audit", capture)
    assert not (directory / "started.json").exists()
    execute(directory, capture, lambda: {"scope": "test_only", "failed": 1})
    assert json.loads((directory / "completed.json").read_text())["status"] == "EXECUTED_IDENTITY_STABLE"
    assert json.loads((directory / "result.json").read_text())["failed"] == 1
    with pytest.raises(FileExistsError):
        execute(directory, capture, lambda: {})
    with pytest.raises(FileExistsError):
        prepare(tmp_path, "one", "known_disease_audit", capture)


def test_pre_execution_drift_cannot_call_runner(tmp_path):
    directory = prepare(tmp_path, "drift", "known_disease_audit", lambda: {"code": "old"})
    calls = []
    with pytest.raises(RuntimeError, match="not executed"):
        execute(directory, lambda: {"code": "new"}, lambda: calls.append(True))
    assert not calls
    assert (directory / "rejected.json").exists()


def test_during_execution_drift_retains_but_invalidates_result(tmp_path):
    snapshots = iter([{"code": "old"}, {"code": "new"}])
    directory = prepare(tmp_path, "during", "known_disease_audit", lambda: {"code": "old"})
    with pytest.raises(RuntimeError, match="diagnostic result retained"):
        execute(directory, lambda: next(snapshots), lambda: {"failed": 0})
    assert (directory / "result.json").exists()
    assert json.loads((directory / "completed.json").read_text())["status"] == "INVALIDATED_IDENTITY_DRIFT"


def test_failure_records_type_without_uncontrolled_message(tmp_path):
    capture = lambda: {}
    directory = prepare(tmp_path, "failure", "known_disease_audit", capture)
    def fail():
        raise ValueError("sensitive-looking message should not be archived")
    with pytest.raises(ValueError):
        execute(directory, capture, fail)
    record = json.loads((directory / "failed.json").read_text())
    assert record["exception_type"] == "ValueError"
    assert "message" not in record
    assert record["identity_after_failure"] == {}


@pytest.mark.parametrize("run_id", ["../escape", "CON"])
def test_invalid_run_path_is_rejected(tmp_path, run_id):
    with pytest.raises(ValueError):
        prepare(tmp_path, run_id, "known_disease_audit", lambda: {})
