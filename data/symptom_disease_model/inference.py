from collections import Counter
import json
from pathlib import Path

from labels import translate_disease_name
from train import parse_symptoms, predict


DEFAULT_SYMPTOM_ALIAS_PATH = Path(__file__).with_name("symptom_alias_zh.json")
DEFAULT_SYMPTOM_ZH_PATH = Path(__file__).with_name("symptom_name_zh.json")


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_symptom_alias_map(path=DEFAULT_SYMPTOM_ALIAS_PATH):
    return load_json(path)


def load_symptom_name_map(path=DEFAULT_SYMPTOM_ZH_PATH):
    return load_json(path)


def normalize_symptom_input(value):
    if isinstance(value, list):
        return ";".join(str(item) for item in value)
    if value is None:
        return ""
    return str(value)


def normalize_symptoms(value, alias_map=None):
    alias_map = alias_map or load_symptom_alias_map()
    text = normalize_symptom_input(value).strip().lower()
    raw_symptoms = parse_symptoms(text)
    normalized = []
    aliases = {}

    matched_aliases = []
    for alias, mapped in alias_map.items():
        if alias and alias in text:
            normalized.append(mapped)
            aliases[alias] = mapped
            matched_aliases.append(alias)

    for symptom in raw_symptoms:
        mapped = alias_map.get(symptom, symptom)
        if mapped == symptom and any(alias in symptom for alias in matched_aliases):
            continue
        normalized.append(mapped)
        if mapped != symptom:
            aliases[symptom] = mapped

    return sorted(set(normalized)), aliases


def symptom_label(tag, symptom_name_map):
    return symptom_name_map.get(tag, tag.replace("_", " "))


def suggest_follow_up_symptoms(model, known_symptoms, ranked, symptom_name_map, limit=5):
    known = set(known_symptoms)
    candidates = Counter()

    for disease, probability in ranked[:3]:
        for symptom, count in model["symptom_counts"].get(disease, {}).items():
            if symptom not in known:
                candidates[symptom] += count * max(probability, 0.01)

    return [
        symptom_label(symptom, symptom_name_map)
        for symptom, _ in candidates.most_common(limit)
    ]


def predict_with_details(
    model,
    symptoms,
    disease_name_map=None,
    symptom_alias_map=None,
    symptom_name_map=None,
    top_k=5,
    min_known_symptoms=3,
    min_confidence=0.35,
):
    disease_name_map = disease_name_map or {}
    symptom_alias_map = symptom_alias_map or load_symptom_alias_map()
    symptom_name_map = symptom_name_map or load_symptom_name_map()

    normalized, aliases = normalize_symptoms(symptoms, symptom_alias_map)
    vocabulary = set(model["vocabulary"])
    known = [symptom for symptom in normalized if symptom in vocabulary]
    unknown = [symptom for symptom in normalized if symptom not in vocabulary]

    if not known:
        return {
            "disease": "",
            "need_more_info": True,
            "known_symptoms": [],
            "unknown_symptoms": unknown,
            "normalized_symptoms": normalized,
            "aliases": aliases,
            "follow_up_symptoms": [],
            "predictions": [],
        }

    ranked = predict(model, known, top_k=top_k)
    top_disease, top_probability = ranked[0]
    need_more_info = len(known) < min_known_symptoms or top_probability < min_confidence
    follow_up = suggest_follow_up_symptoms(model, known, ranked, symptom_name_map)

    return {
        "disease": translate_disease_name(top_disease, disease_name_map),
        "need_more_info": need_more_info,
        "known_symptoms": [symptom_label(symptom, symptom_name_map) for symptom in known],
        "unknown_symptoms": unknown,
        "normalized_symptoms": normalized,
        "aliases": aliases,
        "follow_up_symptoms": follow_up,
        "predictions": [
            {
                "disease": translate_disease_name(disease, disease_name_map),
                "probability": round(probability, 4),
            }
            for disease, probability in ranked
        ],
    }
