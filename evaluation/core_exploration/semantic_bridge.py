"""Research-only symbolic text bridge; no import by Safety or the formal API.

Dictionary mappings are engineering fixtures, not medically reviewed labels.
Preserve uncertainty/negation and never infer high fever from generic fever.
"""
from __future__ import annotations
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ALIASES = json.loads((ROOT / "data/symptom_disease_model/symptom_alias_zh.json").read_text(encoding="utf-8"))
NAMES = json.loads((ROOT / "data/symptom_disease_model/symptom_name_zh.json").read_text(encoding="utf-8"))


def coarse(code):
    return ["fever", code] if code in ("high_fever", "mild_fever") else [code]


def parse_chinese(text):
    from backend.app.domain.symptom_assertions import parse_asserted_symptoms
    return parse_asserted_symptoms(text, ALIASES)


def extract_english(codes, vocabulary):
    text = " ; ".join(codes).replace("_", " ").lower()
    found = set()
    for code in vocabulary:
        phrase = code.replace("_", " ")
        pattern = r"(?<!\w)" + re.escape(phrase) + r"s?(?!\w)"
        for match in re.finditer(pattern, text):
            prefix = re.split(r"[.;]| but ", text[:match.start()])[-1][-24:]
            if re.search(r"(?:no|not|without|denies)\s+$", prefix):
                continue
            found.update(coarse(code))
    # Generic fever supplies only a coarse code, never a severe/mild assertion.
    if re.search(r"\bfever\b", text) and not re.search(r"\b(?:no|without) fever\b", text):
        found.add("fever")
    return sorted(found)
