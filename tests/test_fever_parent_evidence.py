from evaluation.core_exploration.fever_parent_audit import run
import app


def test_grade_denial_does_not_deny_derived_parent():
    result = run()
    assert result["failed"] == 0, [row for row in result["rows"] if not row["pass"]]


def test_unknown_derived_code_does_not_count_or_shift_model_labels():
    tags, prediction = app._model_standard_symptom_tags("没有高烧但有低烧")
    assert prediction["input_coverage"]["model_feature_count"] == 1
    assert {item["standard_code"] for item in tags} == {"mild_fever"}
    assert {item["tag"] for item in tags} == {"低烧"}


def test_auxiliary_only_candidates_cannot_erase_general_rule_fallback():
    assert app.match_department("没有高烧但有低烧") == "全科医学科"
