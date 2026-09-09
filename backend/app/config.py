"""Configuration values shared by the legacy app and new application layers."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class AppSettings:
    project_root: Path
    environment: str = "development"
    region_code: str = "320400"
    app_version: str = "0.3.0-competition-foundation"
    ranking_version: str = "h_triagerank_v1_symptom_disease_penalty"
    triage_rules_version: str = "legacy-2026.09-baseline"
    model_version: str = "symptom-nb-v1-baseline"
    dataset_version: str = "changzhou-data-baseline-2026.09"
    region_pack_version: str = "320400-2026.09-draft"
    cors_origins: tuple[str, ...] = ("http://127.0.0.1:5002", "http://localhost:5002")

    @classmethod
    def from_env(cls, project_root: Path | None = None) -> "AppSettings":
        raw_origins = os.environ.get("CHANGYI_CORS_ORIGINS", "")
        origins = tuple(item.strip() for item in raw_origins.split(",") if item.strip())
        return cls(
            project_root=project_root or PROJECT_ROOT,
            environment=os.environ.get("CHANGYI_ENV", "development"),
            region_code=os.environ.get("CHANGYI_REGION_CODE", "320400"),
            app_version=os.environ.get("CHANGYI_APP_VERSION", cls.app_version),
            ranking_version=os.environ.get("CHANGYI_RANKING_VERSION", cls.ranking_version),
            triage_rules_version=os.environ.get("CHANGYI_TRIAGE_RULES_VERSION", cls.triage_rules_version),
            model_version=os.environ.get("CHANGYI_MODEL_VERSION", cls.model_version),
            dataset_version=os.environ.get("CHANGYI_DATASET_VERSION", cls.dataset_version),
            region_pack_version=os.environ.get("CHANGYI_REGION_PACK_VERSION", cls.region_pack_version),
            cors_origins=origins or cls.cors_origins,
        )

    @property
    def region_root(self) -> Path:
        return self.project_root / "data" / "regions"

    def flask_mapping(self) -> dict:
        return {
            "ENVIRONMENT": self.environment,
            "REGION_CODE": self.region_code,
            "APP_VERSION": self.app_version,
            "RANKING_VERSION": self.ranking_version,
            "TRIAGE_RULES_VERSION": self.triage_rules_version,
            "MODEL_VERSION": self.model_version,
            "DATASET_VERSION": self.dataset_version,
            "REGION_PACK_VERSION": self.region_pack_version,
            "PROJECT_ROOT": str(self.project_root),
            "REGION_ROOT": str(self.region_root),
            "CORS_ORIGINS": self.cors_origins,
        }
