"""Flask application factory for the canonical v1 API and React shell."""

from pathlib import Path
import re

from .config import AppSettings


def create_app(config=None):
    """Create the configured Flask shell and register the versioned API."""
    from flask import Flask, request
    from flask_cors import CORS

    settings = AppSettings.from_env()
    application = Flask(
        __name__,
        static_folder=str(settings.project_root / "static"),
        static_url_path="/static",
    )
    application.config.from_mapping(settings.flask_mapping())
    if config:
        application.config.update(config)

    from .application.regions import RegionReadApplicationService
    from .infrastructure.regions.registry import RegionRegistry

    application.extensions["changyi.region_read_service"] = RegionReadApplicationService(
        registry=lambda: RegionRegistry.from_root(Path(application.config["REGION_ROOT"])),
    )

    origins = application.config.get("CORS_ORIGINS") or settings.cors_origins
    CORS(application, origins=list(origins))

    from .api.v1.routes import api_v1

    application.register_blueprint(api_v1)

    @application.after_request
    def cache_content_addressed_photo_variants(response):
        if response.status_code in (200, 304) and re.fullmatch(r"/static/images/doctor-variants/[0-9a-f]{20}-(80|160|320)\.webp", request.path):
            response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
            response.mimetype = "image/webp"
        return response

    return application


__all__ = ["create_app"]
