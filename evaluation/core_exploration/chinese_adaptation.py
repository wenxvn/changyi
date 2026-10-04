"""Chinese engineering adaptation with case-group and renderer-family isolation."""
from __future__ import annotations
import json
import random
import warnings
from collections import Counter
from pathlib import Path

import numpy as np
from scipy.special import softmax
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.feature_extraction import DictVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score, accuracy_score
from sklearn.model_selection import GroupKFold, GroupShuffleSplit
from threadpoolctl import threadpool_limits

from backend.app.domain.symptom_assertions import parse_asserted_symptoms
from .study import atomic_json, labels, fit_temperature, model_logits, study_lock
from .validation import expanded_metrics
from .semantic_bridge import NAMES, ALIASES
from evaluation.care_routing.round3_split_audit import load_structured
from evaluation.model.evaluate_grouped import near_duplicate_components

OUT = Path(__file__).parent / "results/chinese-adaptation-v1"
TRAIN_TEMPLATES = ("症状为{symptoms}。", "主要不适是{symptoms}。", "我有{symptoms}。")
TEST_TEMPLATES = ("最近身体不舒服：{symptoms}，希望了解就医方向。", "目前感到{symptoms}，该如何继续整理信息？")


def render(row, template, rng):
    names = [NAMES.get(code, code) for code in row["symptoms"]]
    rng.shuffle(names)
    return template.format(symptoms="、".join(names))


def asserted_features(texts):
    return [{code: 1. for code in parse_asserted_symptoms(text, ALIASES)["present"]} for text in texts]


def vectorize(name, training, others):
    if name == "asserted_binary":
        vector = DictVectorizer()
        x_train = vector.fit_transform(asserted_features(training))
        return x_train, [vector.transform(asserted_features(texts)) for texts in others]
    vector = TfidfVectorizer(analyzer="char", ngram_range=(1, 3) if name == "char13" else (2, 4), sublinear_tf=True)
    x_train = vector.fit_transform(training)
    return x_train, [vector.transform(texts) for texts in others]


def texts_and_labels(rows, templates, seed):
    rng = random.Random(seed)
    texts, targets = [], []
    for row in rows:
        for template in templates:
            texts.append(render(row, template, rng))
            targets.append(labels([row])[0])
    return texts, np.array(targets)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with study_lock(OUT / "run.lock"), threadpool_limits(limits=2):
        rows = load_structured().rows
        components, stats = near_duplicate_components(rows, mode="global", threshold=.8)
        groups = np.zeros(len(rows), dtype=int)
        for group, indices in enumerate(components):
            groups[indices] = group
        for seed in (42, 123, 2026):
            folds = GroupKFold(n_splits=5, shuffle=True, random_state=seed)
            for fold, (outer_train, test_idx) in enumerate(folds.split(rows, groups=groups)):
                for representation in ("char24", "char13", "asserted_binary"):
                    path = OUT / f"{seed}-{fold}-{representation}.json"
                    if path.exists():
                        continue
                    local_groups = groups[outer_train]
                    training_idx, cal_idx = next(GroupShuffleSplit(n_splits=1, test_size=.2, random_state=seed+fold).split(outer_train, groups=local_groups))
                    train = [rows[outer_train[i]] for i in training_idx]
                    cal = [rows[outer_train[i]] for i in cal_idx]
                    test = [rows[i] for i in test_idx]
                    inner_idx, val_idx = next(GroupShuffleSplit(n_splits=1, test_size=.25, random_state=seed+100+fold).split(training_idx, groups=local_groups[training_idx]))
                    inner, val = [train[i] for i in inner_idx], [train[i] for i in val_idx]
                    inner_text, inner_y = texts_and_labels(inner, TRAIN_TEMPLATES, seed)
                    val_text, val_y = texts_and_labels(val, TRAIN_TEMPLATES, seed+1)
                    x_inner, (x_val,) = vectorize(representation, inner_text, [val_text])
                    records = []
                    for c in (.1, 1., 10.):
                        for balance in (None, "balanced"):
                            model = LogisticRegression(C=c, class_weight=balance, max_iter=1500, random_state=seed)
                            with warnings.catch_warnings(record=True) as caught:
                                warnings.simplefilter("always");model.fit(x_inner, inner_y)
                            predicted = model.predict(x_val)
                            records.append({"C":c,"class_weight":balance,"macro_f1":float(f1_score(val_y,predicted,average="macro",zero_division=0)),"accuracy":float(accuracy_score(val_y,predicted)),"warnings":[str(w.message) for w in caught]})
                    chosen = max(records,key=lambda r:(r['macro_f1'],r['accuracy']))
                    train_text, train_y = texts_and_labels(train, TRAIN_TEMPLATES, seed)
                    cal_text, cal_y = texts_and_labels(cal, TRAIN_TEMPLATES, seed+2)
                    test_text, test_y = texts_and_labels(test, TEST_TEMPLATES, seed+3)
                    x_train, (x_cal,x_test) = vectorize(representation, train_text, [cal_text,test_text])
                    model = LogisticRegression(C=chosen['C'],class_weight=chosen['class_weight'],max_iter=1500,random_state=seed).fit(x_train,train_y)
                    known_cal = np.isin(cal_y,model.classes_)
                    t = fit_temperature(model_logits(model,x_cal[known_cal]),cal_y[known_cal],model.classes_) if known_cal.sum()>=5 else 1.
                    p = softmax(model_logits(model,x_test)/t,axis=1)
                    result={'status':'complete','seed':seed,'fold':fold,'representation':representation,'chosen':chosen,'candidates':records,'raw_test_cases':len(test),'rendered_test_cases':len(test_y),'metrics':expanded_metrics(test_y,p,model.classes_),'cal_supported':int(known_cal.sum()),'cal_unseen':int((~known_cal).sum()),'temperature':t,'train_templates':list(TRAIN_TEMPLATES),'test_templates':list(TEST_TEMPLATES),'scope':'synthetic Chinese engineering proxy from structured cases, NOT clinical validation','case_group_disjoint':not bool(set(groups[outer_train])&set(groups[test_idx]))}
                    atomic_json(path,result)
                    print(f"DONE {seed} fold{fold} {representation} acc={result['metrics']['accuracy']:.4f}",flush=True)
        atomic_json(OUT/'state.json',{'status':'complete','jobs':45,'inner_fits':270,'case_count':len(rows),'component_stats':stats,'scope':'synthetic engineering only'})
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
