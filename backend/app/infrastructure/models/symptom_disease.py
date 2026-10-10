"""Lazy adapter for the repository-owned symptom-to-disease model."""

from __future__ import annotations

import json
import re
import hashlib
from importlib import import_module
from importlib.machinery import ModuleSpec
from importlib.util import module_from_spec
from pathlib import Path
import sys
from typing import Any, Callable, Mapping
from ...domain.symptom_assertions import parse_asserted_symptoms
from ...domain.medical_input import COLLOQUIAL_SYMPTOM_ALIASES

# Preserve the legacy dataset for reproducibility, but do not use this unverified
# semantic equivalence in website evidence. See R-031 and alias-semantic-v1.
SEMANTIC_ALIAS_QUARANTINE = {
    "抽搐": "unverified_semantic_equivalence",
    "胸闷": "unverified_semantic_equivalence",
    "尿频": "unverified_semantic_equivalence",
}
PROBABILITY_SEMANTICS = {
    "kind": "uncalibrated_model_posterior", "calibrated": False,
    "clinical_probability": False, "scope": "auxiliary_prototype_model",
}
ABSTENTION_NOTICES = {
    "qualified_negation_scope_unverified": "描述包含对症状程度的否认，辅助疾病分析暂需复核，请结合完整症状进行专业评估。",
    "unverified_semantic_equivalence": "部分症状含义尚未核验，辅助疾病分析暂不提供。",
    "unsupported_model_feature": "部分症状尚不支持可靠的辅助疾病分析，暂不提供疾病推测。",
    "contradictory_symptom_assertions": "同一症状的肯定与否认存在冲突，请先核对描述。",
    "noncurrent_symptom_context": "描述含历史或非当前症状，暂不推测当前疾病。",
    "symptom_assertion_uncertain": "症状是否存在尚未确认，辅助疾病分析暂不提供。",
    "no_supported_symptoms": "未获得可用于辅助疾病分析的明确症状，请补充描述。",
}


def qualified_symptom_negation_spans(text, aliases):
    """A denied degree/duration does not assert or deny the parent symptom."""
    issues = []
    for alias, code in sorted(aliases.items(), key=lambda item: len(item[0]), reverse=True):
        for match in re.finditer(re.escape(alias), text):
            if any(item["start"] <= match.start() and match.end() <= item["end"] for item in issues):
                continue
            prefix = re.split(r"[，,。；;！？\n]|但是|不过|但|而是", text[:match.start()])[-1]
            denial = re.search(r"(?P<neg>没有|没|否认|不是)\s*(?:有|出现)?\s*(?P<degree>严重|剧烈|明显|持续)\s*(?:的)?\s*$", prefix)
            if not denial:
                continue
            previous = prefix[denial.start() - 1] if denial.start() else ""
            if (denial["neg"] in {"没有", "没"} and previous == "有") or (denial["neg"] == "否认" and previous == "不") or (denial["neg"] == "不是" and previous == "是"):
                continue
            parent_code = "fever" if alias in {"发热", "发烧"} else code
            issues.append({"alias": alias, "code": parent_code, "qualifier": denial["degree"], "start": match.start(), "end": match.end()})
    return issues


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
            model_dir = str(self.model_dir.resolve())
            namespace = "_changyi_symptom_model_" + hashlib.sha256(model_dir.encode("utf-8")).hexdigest()[:16]
            if namespace not in sys.modules:
                spec = ModuleSpec(namespace, loader=None, is_package=True)
                spec.submodule_search_locations = [model_dir]
                sys.modules[namespace] = module_from_spec(spec)
            inference = import_module(namespace + ".inference")
            labels = import_module(namespace + ".labels")

            with self.model_path.open("r", encoding="utf-8") as handle:
                model = json.load(handle)

            self._runtime = {
                "model": model,
                "disease_name_map": labels.load_disease_name_map(),
                "symptom_alias_map": inference.load_symptom_alias_map(),
                "symptom_name_map": inference.load_symptom_name_map(),
                "predict_with_details": inference.predict_with_details,
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
                "error": "model_unavailable",
                "abstained": True,
                "abstain_reason": "model_unavailable",
                "notice": "辅助疾病分析暂时不可用，请结合症状信息与专业评估。",
                "probability_semantics": dict(PROBABILITY_SEMANTICS),
                "input_coverage": {"scope": "recognized_lexical_evidence_only", "full_text_understanding_verified": False, "model_feature_count": 0},
            }
            return result if details else {"disease": ""}

        assertions = None
        mapping_issues = []
        scope_issues = []
        model_input = normalized
        if runtime["symptom_alias_map"]:
            assertion_text = condition
            for raw, standard in sorted(COLLOQUIAL_SYMPTOM_ALIASES.items(), key=lambda pair: len(pair[0]), reverse=True):
                assertion_text = assertion_text.replace(raw, standard)
            vocabulary = runtime["model"].get("vocabulary", ())
            original_assertions = parse_asserted_symptoms(assertion_text, runtime["symptom_alias_map"], vocabulary)
            for item in original_assertions["evidence"]:
                if item["state"] == "absent":
                    continue
                reason = SEMANTIC_ALIAS_QUARANTINE.get(item["alias"])
                if not reason and not any(code in vocabulary for code in item["codes"]):
                    reason = "unsupported_model_feature"
                if reason:
                    mapping_issues.append({"alias": item["alias"], "legacy_code": runtime["symptom_alias_map"][item["alias"]], "reason": reason})
            approved_aliases = {alias: code for alias, code in runtime["symptom_alias_map"].items() if alias not in SEMANTIC_ALIAS_QUARANTINE}
            assertions = parse_asserted_symptoms(assertion_text, approved_aliases, vocabulary)
            scope_issues = qualified_symptom_negation_spans(assertion_text, approved_aliases)
            if scope_issues:
                masked = list(assertion_text)
                for issue in scope_issues:
                    masked[issue["start"]:issue["end"]] = " " * (issue["end"] - issue["start"])
                assertions = parse_asserted_symptoms("".join(masked), approved_aliases, vocabulary)
                for code in {issue["code"] for issue in scope_issues}:
                    if code not in assertions["present"] and code not in assertions["absent"]:
                        assertions["unknown"] = sorted(set(assertions["unknown"]) | {code})
                assertions["needs_clarification"] = True
            model_input = assertions["present"]
            if mapping_issues or scope_issues or assertions["unknown"] or assertions["uncertainty_conflicts"] or assertions["contradiction"] or assertions["noncurrent_context"]:
                model_input = []
        result = dict(runtime["predict_with_details"](
            runtime["model"],
            model_input,
            disease_name_map=runtime["disease_name_map"],
            symptom_alias_map=runtime["symptom_alias_map"],
            symptom_name_map=runtime["symptom_name_map"],
            top_k=5 if details else 3,
        ))
        result["available"] = True
        result["probability_semantics"] = dict(PROBABILITY_SEMANTICS)
        result["input_coverage"] = {
            "scope": "recognized_lexical_evidence_only", "full_text_understanding_verified": False,
            "model_feature_count": sum(code in runtime["model"].get("vocabulary", ()) for code in result.get("normalized_symptoms", [])),
        }
        result["abstained"] = not bool(result.get("disease") or result.get("predictions"))
        if result["abstained"]:
            reason = "no_supported_symptoms"
            if any(issue["reason"] == "unverified_semantic_equivalence" for issue in mapping_issues):
                reason = "unverified_semantic_equivalence"
            elif mapping_issues:
                reason = "unsupported_model_feature"
            elif scope_issues:
                reason = "qualified_negation_scope_unverified"
            elif assertions:
                if assertions["contradiction"]:
                    reason = "contradictory_symptom_assertions"
                elif assertions["noncurrent_context"]:
                    reason = "noncurrent_symptom_context"
                elif assertions["unknown"] or assertions["uncertainty_conflicts"]:
                    reason = "symptom_assertion_uncertain"
            result["abstain_reason"] = reason
            result["notice"] = ABSTENTION_NOTICES[reason]
        else:
            result["notice"] = "辅助疾病分析只参考已识别的症状，可能遗漏其他描述；分值不能当作患病概率。"
        if assertions is not None:
            result["input_scope_review"] = {"required": bool(scope_issues), "issues": scope_issues, "scope": "auxiliary_severity_denial_not_clinical_judgement"}
            result["mapping_review"] = {"required": bool(mapping_issues), "issues": mapping_issues, "scope": "auxiliary_model_evidence_not_safety_gate"}
            result["input_assertions"] = {key: assertions[key] for key in ("present", "absent", "unknown", "contradiction", "uncertainty_conflicts", "noncurrent_context")}
            result["aliases"] = {item["alias"]: code for item in assertions["evidence"] if item["state"] == "present" for code in item["codes"] if code in model_input}
        if details:
            result["colloquial_replacements"] = replacements
        return result if details else {"disease": result.get("disease", "")}
