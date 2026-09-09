import argparse
import csv
import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path


SEPARATORS = [";", "|", ",", "，", "；", "、"]
SYMPTOM_COLUMNS = ["symptom_tags", "symptoms", "symptom_text"]


def parse_symptoms(text):
    normalized = text.strip()
    for sep in SEPARATORS[1:]:
        normalized = normalized.replace(sep, SEPARATORS[0])
    return sorted({item.strip().lower() for item in normalized.split(SEPARATORS[0]) if item.strip()})


def load_dataset(path, min_class_count=1):
    rows = []
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = set(reader.fieldnames or [])
        if "disease" not in fieldnames:
            raise ValueError("CSV missing required column: disease")
        symptom_column = next((name for name in SYMPTOM_COLUMNS if name in fieldnames), None)
        if not symptom_column:
            raise ValueError(f"CSV missing one symptom column: {', '.join(SYMPTOM_COLUMNS)}")
        for index, row in enumerate(reader, start=2):
            disease = (row.get("disease") or "").strip()
            symptoms = parse_symptoms(row.get(symptom_column) or "")
            if not disease or not symptoms:
                raise ValueError(f"Invalid row {index}: disease and symptoms are required")
            rows.append({"disease": disease, "symptoms": symptoms})
    if min_class_count > 1:
        counts = Counter(row["disease"] for row in rows)
        rows = [row for row in rows if counts[row["disease"]] >= min_class_count]
    if len(rows) < 2:
        raise ValueError("Need at least 2 rows to train a model")
    return rows


def split_dataset(rows, test_size, seed):
    grouped = defaultdict(list)
    for row in rows:
        grouped[row["disease"]].append(row)

    rng = random.Random(seed)
    train, test = [], []
    for disease_rows in grouped.values():
        shuffled = disease_rows[:]
        rng.shuffle(shuffled)
        if len(shuffled) == 1:
            train.extend(shuffled)
            continue
        test_count = max(1, round(len(shuffled) * test_size))
        test_count = min(test_count, len(shuffled) - 1)
        test.extend(shuffled[:test_count])
        train.extend(shuffled[test_count:])

    rng.shuffle(train)
    rng.shuffle(test)
    return train, test


def fit(rows, alpha, min_symptom_df):
    class_counts = Counter(row["disease"] for row in rows)
    document_frequency = Counter()
    for row in rows:
        document_frequency.update(set(row["symptoms"]))
    vocabulary = sorted(symptom for symptom, count in document_frequency.items() if count >= min_symptom_df)
    vocabulary_set = set(vocabulary)
    symptom_counts = {disease: Counter() for disease in class_counts}
    total_symptom_counts = Counter()

    for row in rows:
        disease = row["disease"]
        filtered_symptoms = [symptom for symptom in row["symptoms"] if symptom in vocabulary_set]
        symptom_counts[disease].update(filtered_symptoms)
        total_symptom_counts[disease] += len(filtered_symptoms)

    return {
        "model_type": "multinomial_naive_bayes_for_symptom_tags",
        "alpha": alpha,
        "classes": sorted(class_counts),
        "class_counts": dict(class_counts),
        "vocabulary": vocabulary,
        "min_symptom_df": min_symptom_df,
        "symptom_counts": {k: dict(v) for k, v in symptom_counts.items()},
        "total_symptom_counts": dict(total_symptom_counts),
        "training_rows": len(rows),
    }


def log_scores(model, symptoms):
    symptoms = [symptom for symptom in symptoms if symptom in model["vocabulary"]]
    class_counts = model["class_counts"]
    total_rows = sum(class_counts.values())
    vocab_size = len(model["vocabulary"])
    alpha = model["alpha"]
    scores = {}

    for disease in model["classes"]:
        score = math.log(class_counts[disease] / total_rows)
        denom = model["total_symptom_counts"].get(disease, 0) + alpha * vocab_size
        counts = model["symptom_counts"].get(disease, {})
        for symptom in symptoms:
            score += math.log((counts.get(symptom, 0) + alpha) / denom)
        scores[disease] = score
    return scores


def predict(model, symptoms, top_k=3):
    scores = log_scores(model, symptoms)
    max_score = max(scores.values())
    exp_scores = {label: math.exp(score - max_score) for label, score in scores.items()}
    total = sum(exp_scores.values())
    ranked = sorted(
        ((label, value / total) for label, value in exp_scores.items()),
        key=lambda item: item[1],
        reverse=True,
    )
    return ranked[:top_k]


def evaluate(model, rows):
    if not rows:
        return {"test_rows": 0, "accuracy": None, "top3_accuracy": None}

    correct = 0
    top3 = 0
    for row in rows:
        ranked = predict(model, row["symptoms"], top_k=3)
        labels = [label for label, _ in ranked]
        correct += labels[0] == row["disease"]
        top3 += row["disease"] in labels
    return {
        "test_rows": len(rows),
        "accuracy": correct / len(rows),
        "top3_accuracy": top3 / len(rows),
    }


def main():
    parser = argparse.ArgumentParser(description="Train a disease classifier from symptom tags.")
    parser.add_argument(
        "--data",
        default="data/disease_symptom_structured_41diseases_long.csv",
        help="CSV with disease and symptom_tags/symptoms/symptom_text columns",
    )
    parser.add_argument("--model", default="models/symptom_disease_nb.json", help="Output model JSON path")
    parser.add_argument("--test-size", type=float, default=0.25, help="Per-class test split ratio")
    parser.add_argument("--alpha", type=float, default=1.0, help="Laplace smoothing value")
    parser.add_argument("--min-class-count", type=int, default=1, help="Drop disease labels with fewer rows")
    parser.add_argument("--min-symptom-df", type=int, default=2, help="Drop symptom tags seen in fewer rows")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    rows = load_dataset(args.data, min_class_count=args.min_class_count)
    train_rows, test_rows = split_dataset(rows, args.test_size, args.seed)
    model = fit(train_rows, args.alpha, args.min_symptom_df)
    metrics = evaluate(model, test_rows)
    model["metrics"] = metrics
    model["data_path"] = args.data
    model["total_rows_after_filtering"] = len(rows)
    model["test_size"] = args.test_size

    output = Path(args.model)
    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w", encoding="utf-8") as f:
        json.dump(model, f, ensure_ascii=False, indent=2)

    print(f"trained_rows={len(train_rows)}")
    print(f"test_rows={metrics['test_rows']}")
    print(f"classes={len(model['classes'])}")
    print(f"vocabulary={len(model['vocabulary'])}")
    if metrics["accuracy"] is not None:
        print(f"accuracy={metrics['accuracy']:.3f}")
        print(f"top3_accuracy={metrics['top3_accuracy']:.3f}")
    print(f"model={output}")


if __name__ == "__main__":
    main()
