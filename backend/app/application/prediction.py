"""Application boundary for the legacy disease-prediction endpoint."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class DiseasePredictionResult:
    prediction: dict[str, Any]
    disease: str
    available: bool


@dataclass(frozen=True)
class DiseasePredictionApplicationService:
    """Coordinate model output and optional detail enrichment without owning inference."""

    predict_disease: Callable[..., Mapping[str, Any]]
    standard_symptom_tags: Callable[[str], tuple[list[dict[str, Any]], Mapping[str, Any]]]

    def predict(self, condition: str, *, details: bool = False) -> DiseasePredictionResult:
        prediction = dict(self.predict_disease(condition, details=details))
        available = prediction.get("available", True)
        if not available:
            return DiseasePredictionResult(prediction=prediction, disease="", available=False)

        disease = prediction.get("disease", "")
        if not disease:
            return DiseasePredictionResult(prediction=prediction, disease="", available=True)

        if details:
            prediction["standard_symptom_tags"], _ = self.standard_symptom_tags(condition)
        return DiseasePredictionResult(prediction=prediction, disease=disease, available=True)
