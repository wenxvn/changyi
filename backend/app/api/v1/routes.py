"""Low-risk v1 foundation routes."""

from __future__ import annotations

from flask import Blueprint, current_app, jsonify

from .response import failure, success


api_v1 = Blueprint("api_v1", __name__, url_prefix="/api/v1")


def _region_service():
    return current_app.extensions["changyi.region_read_service"]


def _handler(name: str, *args):
    """Resolve a canonical v1 handler from the single runtime composition."""
    handler = current_app.extensions.get("changyi.v1_handlers", {}).get(name)
    if handler is None:
        return jsonify(failure(
            "SERVICE_NOT_READY",
            "v1 handler registry is not configured",
            region_code=current_app.config["REGION_CODE"],
            model_version=current_app.config["MODEL_VERSION"],
        )), 503
    return handler(*args)


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
    is_ready, active_region_count = _region_service().readiness(current_app.config["REGION_CODE"])
    status = 200 if is_ready else 503
    payload = success(
        {"status": "ready" if is_ready else "not_ready", "active_region_count": active_region_count},
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
    summaries = _region_service().public_summaries()
    return jsonify(success(
        summaries,
        region_code=current_app.config["REGION_CODE"],
        model_version=current_app.config["MODEL_VERSION"],
    ))


@api_v1.post("/triage")
def triage():
    return _handler("api_v1_triage")


@api_v1.post("/triage/followups")
def followups():
    return _handler("api_v1_followups")


@api_v1.post("/recommendations")
def recommendations():
    return _handler("api_v1_recommendations")


@api_v1.get("/hospitals")
def hospitals():
    return _handler("api_v1_hospitals")


@api_v1.get("/hospitals/<int:hid>")
def hospital_detail(hid: int):
    return _handler("api_v1_hospital_detail", hid)


@api_v1.get("/doctors")
def doctors():
    return _handler("api_v1_doctors")


@api_v1.get("/doctors/<int:did>")
def doctor_detail(did: int):
    return _handler("api_v1_doctor_detail", did)


@api_v1.get("/summary")
def summary():
    """Serve the small, read-only resource summary used by the new frontend."""
    return _handler("api_v1_summary")


@api_v1.get("/evidence")
def evidence():
    """Serve read-only evaluation, provenance, and version evidence."""
    return _handler("api_v1_evidence")


@api_v1.get("/map")
def map_view():
    """Serve coordinate-backed public resources for the map view."""
    return _handler("api_v1_map")
