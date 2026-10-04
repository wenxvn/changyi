"""Exclusive provenance records for future synthetic challenge runs."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
from importlib import import_module, metadata
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
CONFIGURATION_KEYS = (
    "CHANGYI_ENV", "CHANGYI_REGION_CODE", "CHANGYI_APP_VERSION",
    "CHANGYI_RANKING_VERSION", "CHANGYI_TRIAGE_RULES_VERSION", "CHANGYI_MODEL_VERSION",
    "CHANGYI_DATASET_VERSION", "CHANGYI_REGION_PACK_VERSION", "CHANGYI_CORS_ORIGINS",
)
SERVING_MODEL_INPUTS = {
    "model_weights": "data/symptom_disease_model/models/symptom_disease_41_nb.json",
    "symptom_aliases": "data/symptom_disease_model/symptom_alias_zh.json",
    "symptom_names": "data/symptom_disease_model/symptom_name_zh.json",
    "disease_names": "data/symptom_disease_model/disease_name_zh.json",
}
FRONTEND_CONFIGS = (
    "package.json", "package-lock.json", "index.html", "tsconfig.json",
    "vite.config.ts", "vite.config.js", "playwright.config.mjs", "playwright.hooks.config.mjs",
)
FRONTEND_SUFFIXES = {".ts", ".tsx", ".js", ".jsx", ".mjs", ".css", ".json", ".html", ".svg"}


def frontend_software(root):
    try:
        command = subprocess.run(["node", "--version"], capture_output=True, text=True, timeout=5)
        value = command.stdout.strip()
        node = value if command.returncode == 0 and re.fullmatch(r"v\d+\.\d+\.\d+", value) else "unavailable"
    except (OSError, subprocess.SubprocessError):
        node = "unavailable"
    dependencies = {}
    for name in ("react", "react-dom", "vite", "typescript", "@playwright/test"):
        try:
            value = json.loads((root / "frontend/node_modules" / name / "package.json").read_text(encoding="utf-8"))["version"]
            dependencies[name] = value if isinstance(value, str) and re.fullmatch(r"\d+\.\d+\.\d+(?:[-+][A-Za-z0-9.-]+)?", value) else "invalid_version"
        except (OSError, ValueError, KeyError, TypeError):
            dependencies[name] = "unavailable"
    return {"node": node, "selected_dependency_versions": dependencies}
CHALLENGES = {name: f"evaluation.core_exploration.{name}" for name in (
    "assertion_challenge", "alias_scope_challenge", "critical_context_audit",
    "known_disease_audit", "disease_conflict_audit", "routing_topic_audit", "conditional_disease_audit",
    "postposed_disease_audit",
    "candidate_evidence_audit",
    "hypothetical_symptom_audit",
    "score_semantics_audit",
    "serving_coverage_audit",
    "input_scope_audit",
    "chest_alias_audit",
    "fever_parent_audit",
    "auxiliary_route_counterfactual",
    "adapter_unavailable_audit",
    "model_error_boundary_audit",
    "uncertainty_overlap_audit",
    "cause_uncertainty_audit",
    "temporal_uncertainty_audit",
    "copula_assertion_audit",
    "negated_denial_audit",
    "hypothetical_risk_audit",
    "qualified_denial_observation",
    "qualified_chest_auxiliary_audit",
    "red_flag_question_priority_audit",
    "risk_reconfirmation_audit",
    "chest_presence_confirmation_audit",
    "current_clause_negation_audit",
    "current_clause_uncertainty_audit",
    "uncertain_route_control_audit",
    "asserted_cough_route_audit",
    "postposed_cough_route_audit",
    "independent_self_safety_audit",
    "current_existence_safety_audit",
    "chinese_render_coverage_audit",
    "canonical_name_bridge_audit",
    "paired_name_bridge_study",
    "saved_bridge_calibration_audit",
    "saved_selective_bridge_audit",
    "emergency_publication_audit",
    "emergency_doctor_boundary_audit",
    "emergency_default_direction_audit",
    "gated_department_publication_audit",
    "copula_existence_safety_audit",
    "considered_disease_fact_audit",
    "provisional_report_fact_audit",
    "exclusion_scope_fact_audit",
    "unresolved_exclusion_risk_audit",
    "completed_exclusion_fact_audit",
    "qualified_unresolved_exclusion_audit",
    "inability_exclusion_token_audit",
)}


def utc():
    return datetime.now(timezone.utc).isoformat()


def identity(root=ROOT):
    code = set()
    for relative in ("backend/app", "evaluation/core_exploration", "data/symptom_disease_model", "data_validation"):
        code.update((root / relative).rglob("*.py"))
    code.update(path for path in (root / "app.py", root / "requirements.txt", root / "requirements-research.txt") if path.exists())
    inputs = {path for path in (root / "data").rglob("*") if path.is_file() and path.suffix.lower() in {".json", ".csv"}}
    hashes = lambda paths: {path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(paths)}
    frontend_sources = set()
    for relative in ("src", "scripts", "e2e", "test", "test-browser"):
        frontend_sources.update(path for path in (root / "frontend" / relative).rglob("*") if path.is_file() and path.suffix.lower() in FRONTEND_SUFFIXES)
    frontend_sources.update(path for path in (root / "frontend" / name for name in FRONTEND_CONFIGS) if path.is_file())
    frontend_build = {path for path in (root / "frontend/dist").rglob("*") if path.is_file() and path.suffix.lower() in FRONTEND_SUFFIXES}
    versions = {}
    for package in ("Flask", "numpy", "scipy", "scikit-learn"):
        try:
            versions[package] = metadata.version(package)
        except metadata.PackageNotFoundError:
            versions[package] = "not_installed"
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True)
    input_hashes = hashes(inputs)
    configuration = {
        key: {"state": "set", "sha256": hashlib.sha256(os.environ[key].encode("utf-8")).hexdigest()}
        if key in os.environ else {"state": "unset"}
        for key in CONFIGURATION_KEYS
    }
    serving_inputs = {
        role: {"path": path, "state": "present", "sha256": input_hashes[path]}
        if path in input_hashes else {"path": path, "state": "missing"}
        for role, path in SERVING_MODEL_INPUTS.items()
    }
    return {"schema_version": 3, "code": hashes(code), "json_csv_inputs": input_hashes,
            "frontend_sources": hashes(frontend_sources), "frontend_build": hashes(frontend_build),
            "frontend_software": frontend_software(root),
            "serving_model_inputs": serving_inputs, "configuration_overrides": configuration,
            "software": {"python": sys.version, "platform": platform.platform(), **versions},
            "git_head": head.stdout.strip() if head.returncode == 0 else "unavailable",
            "scope": "declared_backend_frontend_source_build_and_configuration_roots_not_build_derivation_or_exhaustive_dependencies"}


def write_new(path, value):
    with path.open("x", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)


def prepare(base, run_id, challenge, capture=identity):
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,63}", run_id) or run_id.upper() in {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}:
        raise ValueError("Invalid run id")
    if challenge not in CHALLENGES:
        raise ValueError("Unknown challenge")
    base.mkdir(parents=True, exist_ok=True)
    directory = base / run_id
    directory.mkdir(exist_ok=False)
    write_new(directory / "prepared.json", {"status": "PREPARED_NOT_EXECUTED", "time_utc": utc(), "challenge": challenge, "identity": capture(), "scope": "synthetic_engineering_not_clinical_validation"})
    return directory


def execute(directory, capture=identity, runner=None):
    if (directory / "started.json").exists() or (directory / "rejected.json").exists():
        raise FileExistsError("Run already attempted")
    prepared = json.loads((directory / "prepared.json").read_text(encoding="utf-8"))
    before = capture()
    if before != prepared["identity"]:
        write_new(directory / "rejected.json", {"status": "REJECTED_IDENTITY_DRIFT", "time_utc": utc(), "observed_identity": before})
        raise RuntimeError("Prepared identity changed; runner was not executed")
    write_new(directory / "started.json", {"time_utc": utc(), "pid": os.getpid(), "identity": before})
    after = None
    try:
        if runner is None:
            runner = import_module(CHALLENGES[prepared["challenge"]]).run
        result = runner()
        write_new(directory / "result.json", result)
        after = capture()
        stable = before == after
        write_new(directory / "completed.json", {"status": "EXECUTED_IDENTITY_STABLE" if stable else "INVALIDATED_IDENTITY_DRIFT", "time_utc": utc(), "identity_after": after, "result_sha256": hashlib.sha256((directory / "result.json").read_bytes()).hexdigest()})
        if not stable:
            raise RuntimeError("Execution identity drift; diagnostic result retained")
        return result
    except Exception as exc:
        failure = {"status": "FAILED", "time_utc": utc(), "exception_type": type(exc).__name__}
        try:
            failure["identity_after_failure"] = after if after is not None else capture()
        except Exception as identity_error:
            failure["identity_capture_error_type"] = type(identity_error).__name__
        write_new(directory / "failed.json", failure)
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("prepare", "execute"))
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--challenge", choices=tuple(CHALLENGES), default="known_disease_audit")
    args = parser.parse_args()
    base = Path(__file__).parent / "results/versioned-challenges"
    if args.mode == "prepare":
        directory = prepare(base, args.run_id, args.challenge)
        print(f"PREPARED_NOT_EXECUTED {directory}")
    else:
        if not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,63}", args.run_id):
            raise SystemExit("Invalid run id")
        execute(base / args.run_id)
        print("EXECUTED_IDENTITY_STABLE; inspect result scope and failures separately")
