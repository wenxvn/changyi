import argparse
import json

from inference import (
    load_symptom_alias_map,
    load_symptom_name_map,
    normalize_symptoms,
    predict_with_details,
)
from labels import load_disease_name_map, translate_disease_name
from train import parse_symptoms, predict


def main():
    parser = argparse.ArgumentParser(description="Predict likely diseases from symptom tags.")
    parser.add_argument("--model", default="models/symptom_disease_41_nb.json", help="Trained model JSON path")
    parser.add_argument("--symptoms", required=True, help="Symptoms separated by ; | , or Chinese punctuation")
    parser.add_argument("--top-k", type=int, default=3, help="Number of predictions to show")
    parser.add_argument("--name-only", action="store_true", help="Print only the top disease name")
    parser.add_argument("--details", action="store_true", help="Print JSON details with follow-up suggestions")
    parser.add_argument("--english", action="store_true", help="Print original English disease labels")
    args = parser.parse_args()

    with open(args.model, "r", encoding="utf-8") as f:
        model = json.load(f)

    name_map = {} if args.english else load_disease_name_map()
    alias_map = load_symptom_alias_map()
    symptom_name_map = load_symptom_name_map()

    details = predict_with_details(
        model,
        args.symptoms,
        disease_name_map=name_map,
        symptom_alias_map=alias_map,
        symptom_name_map=symptom_name_map,
        top_k=args.top_k,
    )

    if args.details:
        print(json.dumps(details, ensure_ascii=False, indent=2))
        return

    if args.name_only:
        print(details["disease"] or "症状信息不足")
        return

    symptoms, _ = normalize_symptoms(args.symptoms, alias_map)
    known = [s for s in symptoms if s in model["vocabulary"]]
    unknown = [s for s in symptoms if s not in model["vocabulary"]]
    ranked = predict(model, known, top_k=args.top_k) if known else []

    if not ranked:
        print("症状信息不足")
        return

    print("known_symptoms=" + ";".join(known))
    if unknown:
        print("unknown_symptoms=" + ";".join(unknown))
    if details["need_more_info"] and details["follow_up_symptoms"]:
        print("suggest_follow_up=" + "、".join(details["follow_up_symptoms"]))
    for label, probability in ranked:
        print(f"{translate_disease_name(label, name_map)}\t{probability:.4f}")


if __name__ == "__main__":
    main()
