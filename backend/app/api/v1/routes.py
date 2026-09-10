"""Low-risk v1 foundation routes."""

from __future__ import annotations

from pathlib import Path

from flask import Blueprint, current_app, jsonify

from .legacy_adapter import call_legacy_handler
from .response import failure, success
from ...infrastructure.regions.registry import RegionRegistry


api_v1 = Blueprint("api_v1", __name__, url_prefix="/api/v1")


def _registry() -> RegionRegistry:
    return RegionRegistry.from_root(Path(current_app.config["REGION_ROOT"]))


@api_v1.get("/health")
def health():
    return jsonify(success(
        {"status": "ok", "service": "changyi"},
        region_code=current_app.config["REGION_CODE"],
        model_version=current_app.config["MODEL_VERSION"],
        app_version=current_app.config["APP_VERSION"],
    ))


@api_v1.get("/ready")
def ready():
    registry = _registry()
    active = registry.active()
    is_ready = any(region.code == current_app.config["REGION_CODE"] for region in active)
    status = 200 if is_ready else 503
    payload = success(
        {"status": "ready" if is_ready else "not_ready", "active_region_count": len(active)},
        region_code=current_app.config["REGION_CODE"],
        model_version=current_app.config["MODEL_VERSION"],
    ) if is_ready else failure(
        "REGION_NOT_READY",
        "active Region Pack 不可用",
        region_code=current_app.config["REGION_CODE"],
        model_version=current_app.config["MODEL_VERSION"],
    )
    return jsonify(payload), status


@api_v1.get("/regions")
def regions():
    registry = _registry()
    summaries = registry.public_summaries(active_only=True)
    return jsonify(success(
        summaries,
        region_code=current_app.config["REGION_CODE"],
        model_version=current_app.config["MODEL_VERSION"],
    ))


@api_v1.post("/triage")
def triage():
    return call_legacy_handler("api_v1_triage")


@api_v1.post("/triage/followups")
def followups():
    return call_legacy_handler("api_v1_followups")


@api_v1.post("/recommendations")
def recommendations():
    return call_legacy_handler("api_v1_recommendations")


@api_v1.get("/hospitals")
def hospitals():
    return call_legacy_handler("api_v1_hospitals")


@api_v1.get("/doctors")
def doctors():
    return call_legacy_handler("api_v1_doctors")
