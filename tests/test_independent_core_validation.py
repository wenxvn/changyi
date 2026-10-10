import pytest
from evaluation.core_exploration.independent_validation import evaluate, validate_dataset


def dataset():
    return {"schema_version": "independent-core-validation/v1",
            "provenance": {"source_url": "synthetic_fixture", "license": "project_owned_fixture",
                           "origin": "synthetic_engineering", "label_origin": "engineering_policy_only",
                           "privacy_review": "reviewed_no_identity_or_patient_records", "patient_records": False,
                           "development_exposure": "used_for_development"},
            "cases": [{"case_id": "a", "condition": "fixture a", "acceptable_departments": ["内科"], "risk_status": "ROUTINE"},
                      {"case_id": "b", "condition": "fixture b", "acceptable_departments": ["外科"], "risk_status": None},
                      {"case_id": "c", "condition": "fixture c", "acceptable_departments": [], "risk_status": "EMERGENCY"}]}


def test_abstention_and_api_failure_stay_in_the_full_denominator():
    outcomes = iter([{"triage_status": "ROUTINE", "matched_department": "内科"},
                     {"triage_status": "INSUFFICIENT_INFORMATION", "matched_department": None}, None])
    r = evaluate(dataset(), lambda _: next(outcomes))
    assert r["counts"]["total_cases"] == 3
    assert r["counts"]["api_errors"] == 1
    assert r["counts"]["emergency_missed"] == 1
    assert r["department_accuracy_full_denominator"] == .5
    assert r["department_coverage"] == .5
    assert r["department_retained_accuracy"] == 1
    assert r["joint_available_label_accuracy"] == pytest.approx(1/3)
    assert not r["clinical_validation"] and not r["independence_declared"]


def test_all_refused_is_zero_coverage_with_no_retained_accuracy():
    r = evaluate(dataset(), lambda _: {"triage_status": "INSUFFICIENT_INFORMATION", "matched_department": None})
    assert r["department_coverage"] == 0
    assert r["department_retained_accuracy"] is None
    assert r["department_accuracy_full_denominator"] == 0


@pytest.mark.parametrize("change", ["privacy", "duplicate", "patient_record", "answer", "empty"])
def test_unreviewed_or_duplicate_data_is_rejected_before_prediction(change):
    d = dataset()
    if change == "privacy": d["provenance"]["privacy_review"] = "unknown"
    elif change == "duplicate": d["cases"].append(d["cases"][0].copy())
    elif change == "patient_record": d["provenance"]["patient_records"] = True
    elif change == "answer": d["cases"][0]["answer"] = "must not be a model input"
    else: d["cases"] = []
    with pytest.raises(ValueError):
        validate_dataset(d)
