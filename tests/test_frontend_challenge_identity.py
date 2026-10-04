from functools import partial
import json
import pytest
from evaluation.core_exploration.versioned_challenge import identity, prepare, execute


@pytest.mark.parametrize("relative", ["frontend/src/page.tsx", "frontend/package-lock.json", "frontend/dist/index.html"])
def test_frontend_drift_rejects_execution_before_runner(tmp_path, relative):
    path = tmp_path / relative
    path.parent.mkdir(parents=True)
    path.write_text("old", encoding="utf-8")
    capture = partial(identity, tmp_path)
    directory = prepare(tmp_path / "runs", "frontend-drift", "known_disease_audit", capture)
    path.write_text("new", encoding="utf-8")
    calls = []
    with pytest.raises(RuntimeError, match="not executed"):
        execute(directory, capture, lambda: calls.append(True))
    assert not calls and not (directory / "started.json").exists()


def test_dist_drift_invalidates_completed_diagnostic_result(tmp_path):
    path = tmp_path / "frontend/dist/index.html"
    path.parent.mkdir(parents=True)
    path.write_text("old", encoding="utf-8")
    capture = partial(identity, tmp_path)
    directory = prepare(tmp_path / "runs", "dist-during", "known_disease_audit", capture)
    def runner():
        path.write_text("new", encoding="utf-8")
        return {"scope": "test_only", "failed": 0}
    with pytest.raises(RuntimeError, match="diagnostic result retained"):
        execute(directory, capture, runner)
    assert json.loads((directory / "completed.json").read_text())["status"] == "INVALIDATED_IDENTITY_DRIFT"


def test_unrelated_cache_and_environment_files_are_not_captured(tmp_path):
    before = identity(tmp_path)
    for relative in ("frontend/.env", "frontend/node_modules/cache/ignored.js", "frontend/test-results/ignored.json"):
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("synthetic-excluded-data", encoding="utf-8")
    assert identity(tmp_path) == before
