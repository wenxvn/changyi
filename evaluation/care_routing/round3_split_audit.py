"""Round3: honest-evaluation expansion audit and split builders.

Primary goal: determine whether the 304-row structured set (plus provenance-
tracked extras from the repo's wider training_long file) can yield a larger
honest test without relaxing leakage protection.
"""

from __future__ import annotations

import json
import random
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from data.symptom_disease_model.train import load_dataset
from evaluation.model.evaluate_grouped import (
    jaccard,
    near_duplicate_components,
    sha256_file,
)

from .disease_department import department_for

ROOT = Path(__file__).resolve().parents[2]
STRUCTURED_PATH = ROOT / "data/symptom_disease_model/data/disease_symptom_structured_41diseases_long.csv"
LONG_PATH = ROOT / "data/symptom_disease_model/data/disease_symptom_training_long.csv"
SOURCES_PATH = ROOT / "data/symptom_disease_model/data/disease_symptom_sources.json"

# Established honest threshold from Round1/2. Secondary thresholds are audited
# with explicit cross-split leakage checks, never silently adopted.
PRIMARY_THRESHOLD = 0.8
AUDIT_THRESHOLDS = (0.7, 0.8, 0.85, 0.9)
# If any train-test pair has Jaccard >= this, the split is considered leaky.
CROSS_SPLIT_LEAK_THRESHOLD = 0.75


def _norm_disease(name: str) -> str:
    return (name or "").strip().lower()


@dataclass(frozen=True)
class DatasetBundle:
    name: str
    rows: list[dict[str, Any]]
    sources: dict[str, Any]


def load_structured() -> DatasetBundle:
    rows = load_dataset(str(STRUCTURED_PATH))
    for row in rows:
        row["source"] = "structured_41"
    return DatasetBundle(
        name="structured_41",
        rows=rows,
        sources={
            "path": str(STRUCTURED_PATH.relative_to(ROOT)),
            "sha256": sha256_file(STRUCTURED_PATH),
            "row_count": len(rows),
            "note": "sh anover_disease_symptoms_prec_full / MIT per HF tags",
        },
    )


def load_expanded() -> DatasetBundle:
    """Structured 304 + unique extras for the same 41 diseases from training_long.

    Extras keep provenance. This is still public dataset text, not clinical cases.
    """

    structured = load_structured()
    long_rows = load_dataset(str(LONG_PATH))
    name_map = {_norm_disease(row["disease"]): row["disease"] for row in structured.rows}
    seen: dict[str, set[frozenset[str]]] = defaultdict(set)
    rows: list[dict[str, Any]] = []
    for row in structured.rows:
        key = row["disease"]
        fingerprint = frozenset(row["symptoms"])
        seen[key].add(fingerprint)
        rows.append(
            {
                "disease": key,
                "symptoms": list(row["symptoms"]),
                "source": "structured_41",
            }
        )
    extra = 0
    for row in long_rows:
        canonical = name_map.get(_norm_disease(row["disease"]))
        if not canonical:
            continue
        fingerprint = frozenset(row["symptoms"])
        if fingerprint in seen[canonical]:
            continue
        seen[canonical].add(fingerprint)
        rows.append(
            {
                "disease": canonical,
                "symptoms": list(row["symptoms"]),
                "source": "training_long_extra",
            }
        )
        extra += 1
    sources = json.loads(SOURCES_PATH.read_text(encoding="utf-8"))
    return DatasetBundle(
        name="expanded_41",
        rows=rows,
        sources={
            "structured_path": str(STRUCTURED_PATH.relative_to(ROOT)),
            "structured_sha256": structured.sources["sha256"],
            "long_path": str(LONG_PATH.relative_to(ROOT)),
            "long_sha256": sha256_file(LONG_PATH),
            "row_count": len(rows),
            "extra_rows": extra,
            "disease_count": len({row["disease"] for row in rows}),
            "provenance": sources,
            "note": "expanded public-text set for the 41 prototype labels; not clinical cases",
        },
    )


def component_threshold_audit(
    rows: Sequence[Mapping[str, Any]],
    thresholds: Sequence[float] = AUDIT_THRESHOLDS,
) -> dict[str, Any]:
    report = []
    for threshold in thresholds:
        components, stats = near_duplicate_components(list(rows), mode="same_label", threshold=threshold)
        by_disease = Counter(rows[component[0]]["disease"] for component in components)
        report.append(
            {
                "threshold": threshold,
                "component_count": stats["component_count"],
                "singleton_count": stats["singleton_count"],
                "largest_component_size": stats["largest_component_size"],
                "diseases_with_1_component": sum(1 for count in by_disease.values() if count == 1),
                "diseases_with_2_components": sum(1 for count in by_disease.values() if count == 2),
                "diseases_with_3plus_components": sum(1 for count in by_disease.values() if count >= 3),
                "per_disease_component_count": dict(sorted(by_disease.items())),
            }
        )
    return {
        "primary_threshold": PRIMARY_THRESHOLD,
        "definitions": {
            "component": "same-label connected components over symptom-set Jaccard",
            "why_not_only_fingerprint": "exact fingerprint cannot group template near-rewrites",
            "leak_guard": f"cross-split pair Jaccard must stay < {CROSS_SPLIT_LEAK_THRESHOLD}",
        },
        "thresholds": report,
    }


def quota_split(
    rows: Sequence[Mapping[str, Any]],
    *,
    threshold: float = PRIMARY_THRESHOLD,
    seed: int = 42,
    train_frac: float = 0.6,
    cal_frac: float = 0.2,
    min_components_for_test: int = 3,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    """Quota split over near-duplicate components.

    Diseases with fewer than ``min_components_for_test`` components never enter
    test, so we do not force coverage by breaking leakage protection.
    """

    components, stats = near_duplicate_components(list(rows), mode="same_label", threshold=threshold)
    rng = random.Random(seed)
    by_disease: dict[str, list[list[int]]] = defaultdict(list)
    for component in components:
        by_disease[rows[component[0]]["disease"]].append(component)

    train_idx: list[int] = []
    cal_idx: list[int] = []
    test_idx: list[int] = []
    per_disease = []
    excluded = []
    for disease in sorted(by_disease):
        comps = by_disease[disease][:]
        rng.shuffle(comps)
        n = len(comps)
        department = department_for(disease)
        if n < min_components_for_test:
            for component in comps:
                train_idx.extend(component)
            excluded.append(disease)
            per_disease.append(
                {
                    "disease": disease,
                    "department": department,
                    "components": n,
                    "split": "train_only",
                    "reason": f"components<{min_components_for_test}",
                }
            )
            continue
        n_test = max(1, int(round(n * (1.0 - train_frac - cal_frac))))
        n_cal = max(1, int(round(n * cal_frac)))
        n_train = n - n_test - n_cal
        if n_train < 1:
            n_train = 1
            n_test = max(1, n - n_train - n_cal)
            if n_train + n_cal + n_test > n:
                n_cal = max(0, n - n_train - n_test)
        train_idx.extend(i for component in comps[:n_train] for i in component)
        cal_idx.extend(i for component in comps[n_train:n_train + n_cal] for i in component)
        test_idx.extend(i for component in comps[n_train + n_cal:] for i in component)
        per_disease.append(
            {
                "disease": disease,
                "department": department,
                "components": n,
                "train_components": n_train,
                "cal_components": n_cal,
                "test_components": n - n_train - n_cal,
                "split": "quota",
            }
        )

    train = [rows[i] for i in train_idx]
    cal = [rows[i] for i in cal_idx]
    test = [rows[i] for i in test_idx]
    meta = {
        "threshold": threshold,
        "seed": seed,
        "train_rows": len(train),
        "cal_rows": len(cal),
        "test_rows": len(test),
        "test_disease_count": len({row["disease"] for row in test}),
        "train_disease_count": len({row["disease"] for row in train}),
        "excluded_from_test": excluded,
        "component_stats": stats,
        "per_disease": per_disease,
    }
    return train, cal, test, meta


def cross_split_leakage_audit(
    train: Sequence[Mapping[str, Any]],
    test: Sequence[Mapping[str, Any]],
    threshold: float = CROSS_SPLIT_LEAK_THRESHOLD,
) -> dict[str, Any]:
    pairs = 0
    cross_label = 0
    max_j = 0.0
    examples = []
    train_sets = [(frozenset(row["symptoms"]), row["disease"]) for row in train]
    for row in test:
        test_set = frozenset(row["symptoms"])
        for train_set, train_label in train_sets:
            score = jaccard(test_set, train_set)
            if score > max_j:
                max_j = score
            if score >= threshold:
                pairs += 1
                if train_label != row["disease"]:
                    cross_label += 1
                if len(examples) < 5:
                    examples.append(
                        {
                            "jaccard": round(score, 4),
                            "train_disease": train_label,
                            "test_disease": row["disease"],
                        }
                    )
    return {
        "threshold": threshold,
        "pair_count": pairs,
        "cross_label_pair_count": cross_label,
        "max_jaccard": round(max_j, 4),
        "examples": examples,
        "leaky": pairs > 0,
    }


def evaluate_component_definition_limits(bundle: DatasetBundle) -> dict[str, Any]:
    audit = component_threshold_audit(bundle.rows)
    train, cal, test, meta = quota_split(bundle.rows, threshold=PRIMARY_THRESHOLD, seed=42)
    leak = cross_split_leakage_audit(train, test)
    # Secondary expanded-style quota on 0.85 for the structured set (still primary protocol first).
    train85, cal85, test85, meta85 = quota_split(bundle.rows, threshold=0.85, seed=42)
    leak85 = cross_split_leakage_audit(train85, test85)
    return {
        "bundle": bundle.name,
        "row_count": len(bundle.rows),
        "threshold_audit": audit,
        "primary_quota_split": {**meta, "leakage": leak},
        "secondary_0_85_quota_split": {**meta85, "leakage": leak85},
        "upper_limit_statement": (
            "structured_41 在 threshold=0.8 诚实 quota 下 test 仍有限；"
            "不得为覆盖 41 类强行拆散 component。expanded_41 可扩大 test，但仍是公开文本集而非临床病例。"
        ),
    }


def write_external_eval_schema(path: Path | None = None) -> dict[str, Any]:
    path = path or (Path(__file__).with_name("data_schema") / "external_eval_schema.json")
    schema = {
        "schema_version": "external-triage-eval/v1",
        "purpose": "Future manually curated / hospital-approved evaluation set importer",
        "rows": [
            {
                "case_id": "string, opaque",
                "symptom_text": "free text, de-identified",
                "symptom_tags": ["standard_code"],
                "absent_symptoms": ["standard_code"],
                "department_label": "care-routing label, not diagnosis claim",
                "disease_label": "optional research label",
                "safety_flags": ["optional existing safety tags only"],
                "source": "curated_clinic|expert_panel|public_deidentified",
                "annotation_status": "unlabeled|weak|expert_reviewed|rejected",
                "license": "string",
                "updated_at": "ISO date",
            }
        ],
        "import_rules": [
            "No synthetic rows may be marked expert_reviewed.",
            "Leakage: near-duplicate components must not cross train/test.",
            "Safety flags may only reuse existing evaluation/safety tags.",
            "Missing license/source blocks import into the primary table.",
        ],
        "status": "schema_only_no_results",
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(schema, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"path": str(path), "schema_version": schema["schema_version"], "results": None}
