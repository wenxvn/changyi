from evaluation.core_exploration.paired_name_bridge_study import fit_features


def test_evaluation_only_feature_cannot_enter_fitted_vocabulary():
    vector, train, (held_out,) = fit_features(["我有咳嗽"], [["我有颈部疼痛"]], {"咳嗽": "cough", "颈部疼痛": "neck_pain"})
    assert vector.get_feature_names_out().tolist() == ["cough"]
    assert train.nnz == 1 and held_out.nnz == 0
