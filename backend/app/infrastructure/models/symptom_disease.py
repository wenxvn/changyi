"""Lazy adapter for the repository-owned symptom-to-disease model."""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any, Callable, Mapping


class SymptomDiseaseModelAdapter:
    """Keep model loading/inference details outside the Flask composition root."""

    def __init__(
        self,
        *,
        model_dir: Path,
        model_path: Path,
        normalize: Callable[[str], tuple[str, Mapping[str, str]]],
        runtime_loader: Callable[[], dict[str, Any] | None] | None = None,
    ):
        self.model_dir = model_dir
        self.model_path = model_path
        self.normalize = normalize
        self._runtime: dict[str, Any] | None = None
        self._runtime_error: str | None = None
        self._runtime_loader = runtime_loader
        self._runtime_loader_called = False

    @property
    def runtime_error(self) -> str | None:
        return self._runtime_error

    def _load_runtime(self) -> dict[str, Any] | None:
        if self._runtime is not None:
            return self._runtime
        if self._runtime_error is not None:
            return None

        try:
            if not self.model_path.exists():
                raise FileNotFoundError(self.model_path)
            model_dir = str(self.model_dir)
            if model_dir not in sys.path:
                sys.path.insert(0, model_dir)

            from inference import load_symptom_alias_map, load_symptom_name_map, predict_with_details
            from labels import load_disease_name_map

            with self.model_path.open("r", encoding="utf-8") as handle:
                model = json.load(handle)

            self._runtime = {
                "model": model,
                "disease_name_map": load_disease_name_map(),
                "symptom_alias_map": load_symptom_alias_map(),
                "symptom_name_map": load_symptom_name_map(),
                "predict_with_details": predict_with_details,
            }
            return self._runtime
        except Exception as exc:
            self._runtime_error = str(exc)
            return None

    def _runtime_or_injected(self) -> dict[str, Any] | None:
        if self._runtime_loader is None:
            return self._load_runtime()
        if not self._runtime_loader_called:
            self._runtime_loader_called = True
            try:
                self._runtime = self._runtime_loader()
            except Exception as exc:
                self._runtime_error = str(exc)
        return self._runtime

    def predict(self, condition: str, *, details: bool = False) -> dict[str, Any]:
        normalized, replacements = self.normalize(condition)
        runtime = self._runtime_or_injected()
        if not runtime:
            result = {
                "disease": "",
                "available": False,
                "error": self._runtime_error or "model_unavailable",
            }
            return result if details else {"disease": ""}

        result = dict(runtime["predict_with_details"](
            runtime["model"],
            normalized,
            disease_name_map=runtime["disease_name_map"],
            symptom_alias_map=runtime["symptom_alias_map"],
            symptom_name_map=runtime["symptom_name_map"],
            top_k=5 if details else 3,
        ))
        result["available"] = True
        if details:
            result["colloquial_replacements"] = replacements
        return result if details else {"disease": result.get("disease", "")}
