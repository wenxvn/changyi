"""Round4 unit tests."""

from __future__ import annotations

from evaluation.care_routing.department_confusion import (
    data_gap_map,
    department_confusion_report,
    shared_symptom_stats,
)
from evaluation.care_routing.direct_department import (
    fit_direct_department_models,
    summarize_dept_predictions,
)
from evaluation.care_routing.model_baselines import (
    build_char_ngram_tfidf_features,
    build_fusion_features,
    build_tfidf_features,
)
from evaluation.care_routing.round3_split_audit import load_expanded, quota_split
from evaluation.care_routing.round4_learning import representation_ablation_from_matrix
from evaluation.care_routing.round4_robustness_safety import safety_first_offline_check
from evaluation.care_routing.selective_routing import (
    risk_coverage_curve,
    selective_metrics,
    threshold_for_coverage,
)


def test_char_ngram_features():
    rows = [
        {"disease": "A", "symptoms": ["chest_pain", "cough"]},
        {"disease": "B", "symptoms": ["headache", "nausea"]},
    ]
    feats = build_char_ngram_tfidf_features(rows, rows)
    assert len(feats) == 2
    assert any(feats[0].keys())


def test_fusion_features():
    rows = [{"disease": "A", "symptoms": ["cough"]}]
    word = build_tfidf_features(rows, rows)
    char = build_char_ngram_tfidf_features(rows, rows)
    fused = build_fusion_features(word, char)
    assert len(fused) == 1
    assert any(k.startswith("w:") for k in fused[0])
    assert any(k.startswith("c:") for k in fused[0])


def test_direct_department_fit_smoke():
    expanded = load_expanded()
    train, cal, test, _ = quota_split(expanded.rows, threshold=0.8, seed=42)
    result = fit_direct_department_models(train, cal, test, seed=42)
    for key in (
        "multinomial_nb",
        "logistic_regression_binary",
        "char_ngram_tfidf_lr",
        "word_char_fusion_lr",
        "three_state_lr",
    ):
        assert key in result["models"]
        assert result["models"][key]["test_rows"] == len(test)


def test_selective_metrics_and_curve():
    ranked = [
        [("A", 0.8), ("B", 0.2)],
        [("B", 0.6), ("A", 0.4)],
        [("A", 0.9), ("B", 0.1)],
        [("C", 0.55), ("A", 0.45)],
    ]
    y_true = ["A", "B", "B", "C"]
    thr = threshold_for_coverage([0.8, 0.6, 0.9, 0.55], 0.5)
    metrics = selective_metrics(ranked, y_true, signal="max_probability", threshold=thr)
    assert metrics["retained_rows"] >= 1
    assert 0.0 <= metrics["coverage"] <= 1.0
    curve = risk_coverage_curve(ranked, ranked, y_true, y_true, signal="max_probability")
    assert len(curve["points"]) == 6


def test_department_confusion_and_gap():
    y_true = ["心血管内科", "呼吸内科", "心血管内科", "神经内科"]
    y_pred = ["呼吸内科", "呼吸内科", "神经内科", "神经内科"]
    report = department_confusion_report(y_true, y_pred)
    assert report["top_confusion_pairs"]
    expanded = load_expanded()
    gap = data_gap_map(expanded.rows, y_true=y_true, y_pred=y_pred, seed=42)
    assert gap["disclaimer"]
    assert gap["top_n_to_collect"]
    stats = shared_symptom_stats(expanded.rows, "心血管内科", "呼吸内科")
    assert "shared_top_symptoms" in stats


def test_safety_check_passes():
    result = safety_first_offline_check(department_model_accuracy=0.45)
    assert result["all_pass"] is True


def test_ablation_helper():
    matrix = {
        "aggregate": {
            "headline": {
                "logistic_regression_binary": {
                    "accuracy": {"mean": 0.4, "std": 0.01},
                    "macro_f1": {"mean": 0.3, "std": 0.01},
                    "top2_accuracy": {"mean": 0.6, "std": 0.01},
                    "ece": {"mean": 0.05, "std": 0.01},
                },
                "char_ngram_tfidf_lr": {
                    "accuracy": {"mean": 0.42, "std": 0.02},
                    "macro_f1": {"mean": 0.31, "std": 0.01},
                    "top2_accuracy": {"mean": 0.61, "std": 0.01},
                    "ece": {"mean": 0.06, "std": 0.01},
                },
            }
        }
    }
    ablation = representation_ablation_from_matrix(matrix)
    assert ablation["best_representation_under_lr"] == "char_ngram_tfidf_lr"
