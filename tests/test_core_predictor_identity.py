"""Regression at the actual selective/calibration prediction seam."""
from unittest.mock import patch

from evaluation.care_routing import direct_department as dd
from evaluation.care_routing import model_baselines as mb
from evaluation.care_routing.selective_routing import run_selective_routing
from evaluation.competition.run_matrix import build_matrix


def toy_rows():
    return [
        {"disease": "Common Cold", "symptoms": ["cough", "runny_nose"]},
        {"disease": "Common Cold", "symptoms": ["cough", "fever"]},
        {"disease": "Fungal infection", "symptoms": ["itching", "skin_rash"]},
        {"disease": "Fungal infection", "symptoms": ["itching", "red_skin"]},
    ]


def test_selective_does_not_train_a_second_calibration_model():
    rows = toy_rows()
    with patch.object(mb, "fit_logistic_regression", wraps=mb.fit_logistic_regression) as second_fit:
        result = run_selective_routing(rows, rows[::2], rows[1::2], model_name="char_ngram_tfidf_lr")
    assert second_fit.call_count == 0, "cal/test must use the same fitted predictor"
    assert result["full_coverage"]["retained_rows"] == 2


def test_stored_predictor_scores_same_rows_identically():
    rows = toy_rows()
    fitted = dd.fit_direct_department_models(rows, rows[::2], rows[1::2])
    state = fitted["_fitted"]["char_ngram_tfidf_lr"]
    assert dd.predict_fitted_department(state, rows[1::2]) == fitted["_predictions"]["char_ngram_tfidf_lr"]["ranked_calibrated"]


def test_competition_std_is_numeric():
    row = next(r for r in build_matrix()["rows"] if r["track"] == "direct_department_char_ngram_lr")
    assert isinstance(row["std"], (int, float))


def test_robustness_identity_has_zero_delta_and_no_second_fit():
    from evaluation.care_routing import round4_robustness_safety as robust
    rows = toy_rows()
    split = (rows, rows[::2], rows[1::2], {})
    with patch.object(robust, "quota_split", return_value=split), patch.object(mb, "fit_logistic_regression", wraps=mb.fit_logistic_regression) as second_fit:
        result = robust.robustness_selective(rows, model_name="char_ngram_tfidf_lr")
    assert second_fit.call_count == 0
    identity = result["per_kind"]["identity"]
    assert identity["coverage_delta"] == 0
    assert identity["accuracy_delta"] in (0, None)


def test_safety_check_cannot_pass_from_unchanged_default_numbers():
    from evaluation.care_routing.round4_robustness_safety import safety_first_offline_check
    failed = {"case_count": 142, "red_flag_recall": .9, "under_triage_rate": .1, "over_triage_rate": 0., "emergency_false_negative": 1, "review_required": ["miss"]}
    with patch("evaluation.safety.evaluate_safety.evaluate_cases", return_value=failed):
        result = safety_first_offline_check(department_model_accuracy=.95)
    assert not result["all_pass"]
