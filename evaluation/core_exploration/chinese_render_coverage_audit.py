"""Coverage of the existing synthetic renderer, not clinical Chinese labels."""
from collections import Counter

from backend.app.domain.symptom_assertions import parse_asserted_symptoms


def audit_rows(rows, names, aliases):
    occurrences = Counter(code for row in rows for code in row["symptoms"])
    named = {code for code in occurrences if code in names}
    recovered = {code for code in named
                 if code in parse_asserted_symptoms(names[code], aliases)["present"]}
    details = [{"row_index": index, "symptom_count": len(row["symptoms"]),
                "english_fallback_codes": [code for code in row["symptoms"] if code not in named],
                "named_but_not_recovered_codes": [code for code in row["symptoms"]
                                                 if code in named and code not in recovered]}
               for index, row in enumerate(rows)]
    return {"total": len(rows), "failed": 0,
            "symptom_occurrences": sum(occurrences.values()), "unique_symptom_codes": len(occurrences),
            "named_occurrences": sum(occurrences[code] for code in named),
            "english_fallback_occurrences": sum(occurrences[code] for code in occurrences if code not in named),
            "fully_named_rows": sum(not row["english_fallback_codes"] for row in details),
            "named_but_not_recovered_occurrences": sum(occurrences[code] for code in named - recovered),
            "codes": [{"code": code, "occurrences": count, "has_name": code in named,
                       "name_recovers_own_code": code in recovered}
                      for code, count in sorted(occurrences.items())], "rows": details}


def run():
    from evaluation.care_routing.round3_split_audit import load_structured
    from evaluation.core_exploration.semantic_bridge import NAMES, ALIASES
    result = audit_rows(load_structured().rows, NAMES, ALIASES)
    return {"scope": "existing_synthetic_chinese_renderer_feature_coverage_not_clinical_validation",
            "clinical_accuracy": None, "clinical_labels_verified": 0,
            "translation_semantics_verified": False, **result}
