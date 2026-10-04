"""Paired current-source research experiment, never a serving model."""
import hashlib
import json
import warnings
import numpy as np
from scipy.special import softmax
from sklearn.feature_extraction import DictVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import GroupKFold, GroupShuffleSplit
from threadpoolctl import threadpool_limits

from backend.app.domain.symptom_assertions import parse_asserted_symptoms
from .canonical_name_bridge_audit import build_bridge
from .chinese_adaptation import texts_and_labels, TRAIN_TEMPLATES, TEST_TEMPLATES
from .semantic_bridge import NAMES, ALIASES
from .study import model_logits, fit_temperature
from .validation import expanded_metrics
from evaluation.care_routing.round3_split_audit import load_structured
from evaluation.model.evaluate_grouped import near_duplicate_components


def fit_features(training, other_texts, aliases):
    def features(texts):
        return [{code: 1. for code in parse_asserted_symptoms(text, aliases)["present"]} for text in texts]
    vector = DictVectorizer()
    train = vector.fit_transform(features(training))
    return vector, train, [vector.transform(features(texts)) for texts in other_texts]


def run():
    rows = load_structured().rows
    components, group_stats = near_duplicate_components(rows, mode="global", threshold=.8)
    groups = np.zeros(len(rows), dtype=int)
    for group, indices in enumerate(components):
        groups[indices] = group
    bridge, additions, conflicts = build_bridge(NAMES, ALIASES)
    if conflicts:
        raise ValueError("Declared bridge has unresolved conflicts")
    records = []
    with threadpool_limits(limits=2):
        for seed in (42, 123, 2026):
            for fold, (outer, test) in enumerate(GroupKFold(n_splits=5, shuffle=True, random_state=seed).split(rows, groups=groups)):
                train_local, cal_local = next(GroupShuffleSplit(n_splits=1, test_size=.2, random_state=seed+fold).split(outer, groups=groups[outer]))
                train, cal = outer[train_local], outer[cal_local]
                inner_local, val_local = next(GroupShuffleSplit(n_splits=1, test_size=.25, random_state=seed+100+fold).split(train, groups=groups[train]))
                inner, val = train[inner_local], train[val_local]
                assert not (set(groups[train]) & set(groups[cal]) or set(groups[outer]) & set(groups[test]) or set(groups[inner]) & set(groups[val]))
                def render(indices, templates, offset):
                    return texts_and_labels([rows[int(i)] for i in indices], templates, seed+offset)
                inner_text, inner_y = render(inner, TRAIN_TEMPLATES, 0)
                val_text, val_y = render(val, TRAIN_TEMPLATES, 1)
                train_text, train_y = render(train, TRAIN_TEMPLATES, 0)
                cal_text, cal_y = render(cal, TRAIN_TEMPLATES, 2)
                for method, aliases in (("current_alias", ALIASES), ("declared_name_bridge", bridge)):
                    _, x_inner, (x_val,) = fit_features(inner_text, [val_text], aliases)
                    candidates = []
                    for c in (.1, 1., 10.):
                        for balance in (None, "balanced"):
                            model = LogisticRegression(C=c, class_weight=balance, max_iter=1500, random_state=seed)
                            with warnings.catch_warnings(record=True) as caught:
                                warnings.simplefilter("always")
                                model.fit(x_inner, inner_y)
                            predicted = model.predict(x_val)
                            candidates.append({"C": c, "class_weight": balance,
                                "macro_f1": float(f1_score(val_y, predicted, average="macro", zero_division=0)),
                                "accuracy": float(accuracy_score(val_y, predicted)),
                                "warning_categories": [w.category.__name__ for w in caught]})
                    chosen = max(candidates, key=lambda r: (r["macro_f1"], r["accuracy"]))
                    vector, x_train, (x_cal,) = fit_features(train_text, [cal_text], aliases)
                    model = LogisticRegression(C=chosen["C"], class_weight=chosen["class_weight"], max_iter=1500, random_state=seed)
                    with warnings.catch_warnings(record=True) as caught:
                        warnings.simplefilter("always")
                        model.fit(x_train, train_y)
                    supported = np.isin(cal_y, model.classes_)
                    temperature = fit_temperature(model_logits(model, x_cal[supported]), cal_y[supported], model.classes_) if supported.sum() >= 5 else 1.
                    # No outer test text/label is used before selection/calibration.
                    test_text, test_y = render(test, TEST_TEMPLATES, 3)
                    test_features = [{code: 1. for code in parse_asserted_symptoms(text, aliases)["present"]} for text in test_text]
                    p = softmax(model_logits(model, vector.transform(test_features))/temperature, axis=1)
                    learned = {"features": vector.get_feature_names_out().tolist(), "classes": model.classes_.tolist(),
                               "coef": model.coef_.tolist(), "intercept": model.intercept_.tolist()}
                    record = {"seed": seed, "fold": fold, "method": method, "chosen": chosen, "candidates": candidates,
                              "temperature": float(temperature), "cal_supported": int(supported.sum()), "cal_unseen": int((~supported).sum()),
                              "splits": {name: indices.tolist() for name, indices in (("train", train), ("cal", cal), ("inner", inner), ("validation", val), ("test", test))},
                              "case_group_disjoint": True, "raw_test_cases": len(test), "metrics": expanded_metrics(test_y, p, model.classes_),
                              "learned_state": learned, "model_identity_sha256": hashlib.sha256(json.dumps(learned, sort_keys=True).encode()).hexdigest(),
                              "warning_categories": [w.category.__name__ for w in caught]}
                    records.append(record)
                    print(f"DONE seed={seed} fold={fold} method={method}", flush=True)
    summary = {}
    for method in ("current_alias", "declared_name_bridge"):
        selected = [r for r in records if r["method"] == method]
        denominator = sum(r["metrics"]["n"] for r in selected)
        summary[method] = {"jobs": len(selected), "rendered_test_rows": denominator,
            "accuracy": sum(r["metrics"]["accuracy"]*r["metrics"]["n"] for r in selected)/denominator,
            "mean_macro_f1": float(np.mean([r["metrics"]["macro_f1"] for r in selected])),
            "mean_ece": float(np.mean([r["metrics"]["ece"] for r in selected])),
            "unseen_department_rows": sum(r["metrics"]["unseen_department_rows"] for r in selected)}
    return {"scope": "research_only_synthetic_mixed_language_proxy_not_clinical_validation", "total": len(records), "failed": 0,
            "case_count": len(rows), "inner_fits": 180, "final_fits": len(records), "dictionary_names": len(NAMES),
            "bridge_additions": len(additions), "group_stats": group_stats, "group_ids": groups.tolist(),
            "train_templates": list(TRAIN_TEMPLATES), "test_templates": list(TEST_TEMPLATES),
            "selection": "inner_macro_f1_then_accuracy; temperature_cal_only; no_test_based_method_selection",
            "clinical_accuracy": None, "serving_changed": False, "summary": summary, "records": records}
