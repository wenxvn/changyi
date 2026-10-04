"""Research fixtures from existing names; never modify serving dictionaries."""
from collections import defaultdict
from backend.app.domain.symptom_assertions import parse_asserted_symptoms


def build_bridge(names, aliases):
    targets = defaultdict(set)
    for code, name in names.items():
        targets[name].add(code)
    candidate = dict(aliases)
    additions, conflicts = [], []
    for name, codes in sorted(targets.items()):
        if len(codes) != 1 or (name in aliases and aliases[name] not in codes):
            conflicts.append({"name": name, "declared_codes": sorted(codes), "existing_code": aliases.get(name)})
            continue
        if name not in aliases:
            code = next(iter(codes))
            candidate[name] = code
            additions.append({"name": name, "declared_code": code})
    return candidate, additions, conflicts


def run():
    from evaluation.core_exploration.semantic_bridge import NAMES, ALIASES
    from evaluation.care_routing.round3_split_audit import load_structured
    source_codes = {code for row in load_structured().rows for code in row["symptoms"]}
    selected_names = {code: name for code, name in NAMES.items() if code in source_codes}
    candidate, additions, conflicts = build_bridge(selected_names, ALIASES)
    templates = (("report", "我有{name}", "present"), ("denial", "我没有{name}", "absent"),
                 ("existence_query", "我不确定是否有{name}", "unknown"), ("history", "去年{name}", "unknown"))
    rows = []
    for code, name in sorted(selected_names.items()):
        for template, pattern, expected in templates:
            text = pattern.format(name=name)
            original = parse_asserted_symptoms(text, ALIASES)
            bridged = parse_asserted_symptoms(text, candidate)
            rows.append({"declared_code": code, "declared_name": name, "template": template,
                         "text": text, "expected_dictionary_state": expected,
                         "baseline_states": [state for state in ("present", "absent", "unknown") if code in original[state]],
                         "bridge_states": [state for state in ("present", "absent", "unknown") if code in bridged[state]],
                         "baseline_contract_pass": code in original[expected],
                         "bridge_contract_pass": code in bridged[expected],
                         "clinical_semantics_verified": False})
    return {"scope": "research_only_declared_name_bridge_contract_not_model_or_clinical_accuracy",
            "total": len(rows), "failed": sum(not row["bridge_contract_pass"] for row in rows),
            "baseline_contract_failures": sum(not row["baseline_contract_pass"] for row in rows),
            "name_count": len(selected_names), "dictionary_name_count": len(NAMES),
            "names_outside_structured_inventory": sorted(set(NAMES) - source_codes),
            "added_alias_count": len(additions),
            "conflicts": conflicts, "additions": additions, "rows": rows,
            "clinical_accuracy": None, "model_fits": 0,
            "serving_dictionary_changed": False, "untranslated_codes_filled": 0}
