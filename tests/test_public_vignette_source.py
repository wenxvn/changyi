"""Ensure the external evidence uses its actual cohort and avoids answer leakage."""
import hashlib
import json
from evaluation.core_exploration.public_vignettes import ROOT, COMMIT


def test_actual_source_denominator_is_not_inferred_from_the_readme():
    source = json.loads((ROOT / "source.json").read_text(encoding="utf-8"))
    assert source["source_commit"] == COMMIT
    assert source["raw_source_rows"] == 960
    assert source["source_vignette_id_count"] == 60
    assert source["selected_base_case_count"] == 27
    assert {r["case_id"] for r in source["cases"]} == {f"F{i}" for i in range(1, 28)}
    assert len({r["base_case_id"] for r in source["cases"]}) == 27


def test_translations_bind_to_the_full_frozen_source_without_prediction_fields():
    source_raw = (ROOT / "source.json").read_bytes()
    translated = json.loads((ROOT / "translations.json").read_text(encoding="utf-8"))
    assert translated["source_sha256"] == hashlib.sha256(source_raw).hexdigest()
    assert translated["translation_medically_reviewed"] is False
    assert len(translated["cases"]) == 27
    for row in translated["cases"]:
        assert set(row) == {"case_id", "base_case_id", "domain", "condition_en", "condition_zh", "source_gold"}
        assert "TRIAGE:" not in row["condition_en"]
        assert "CONFIDENCE:" not in row["condition_en"]
        assert "EXPLANATION" not in row["condition_en"]
        assert row["condition_zh"] and row["condition_en"]


def test_initial_external_failure_and_development_recheck_have_separate_provenance():
    before = json.loads((ROOT / "before-v6.8.json").read_text(encoding="utf-8"))
    after = json.loads((ROOT / "development-after-v6.9.json").read_text(encoding="utf-8"))
    for report in (before, after):
        assert report["total_source_cases"] == len(report["rows"]) == 27
        assert report["base_case_count"] == 27
        assert report["strict_source_emergency_cases"] == 2
        assert report["strict_source_emergency_not_er"] == 2
        assert report["clinical_validation"] is False
        assert report["source_grade_compatible_count"] == sum(r["source_grade_compatible"] for r in report["rows"])
    assert after["development_exposure"] == "used_for_development"
    assert after["translations_sha256"] == before["translations_sha256"]
