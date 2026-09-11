"""Application factory used by the legacy entry point and API v1."""

from pathlib import Path

from .config import AppSettings


def create_app(config=None):
    """Create the configured Flask shell without removing legacy routes."""
    from flask import Flask
    from flask_cors import CORS

    settings = AppSettings.from_env()
    application = Flask(
        __name__,
        template_folder=str(settings.project_root / "templates"),
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
    return application


__all__ = ["create_app"]
