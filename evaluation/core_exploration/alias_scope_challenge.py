"""Full existing-alias scope regression; synthetic, not clinical labels."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from .assertion_challenge import SYMPTOMS, TEMPLATES
from .semantic_bridge import ALIASES, parse_chinese


def expected_codes(alias, state="present"):
    code = ALIASES[alias]
    if alias in ("发热", "发烧"):
        return ["fever"]
    # Parent presence follows a positive grade; the converse for negation or
    # uncertainty is invalid. Historical snapshots used the earlier oracle.
    return sorted(["fever", code]) if code in ("high_fever", "mild_fever") and state == "present" else [code]


def cases():
    for alias in sorted(ALIASES):
        for family, template, state in TEMPLATES:
            yield {"family": f"full_alias_{family}", "text": template.format(s=alias), "expected": {state: expected_codes(alias, state)}}
    for first in SYMPTOMS:
        for second in SYMPTOMS:
            if first == second:
                continue
            codes = sorted([ALIASES[first], ALIASES[second]])
            yield {"family": "post_coordinated_denial", "text": f"{first}和{second}都没有", "expected": {"absent": codes}}
            yield {"family": "post_coordinated_unknown", "text": f"{first}和{second}都不确定", "expected": {"unknown": codes}}
            yield {"family": "unknown_then_positive", "text": f"不确定是否{first}但有{second}", "expected": {"unknown": [ALIASES[first]], "present": [ALIASES[second]]}}


def run():
    rows = []
    for case in cases():
        expected = {state: sorted(case["expected"].get(state, [])) for state in ("present", "absent", "unknown")}
        parsed = parse_chinese(case["text"])
        actual = {state: parsed[state] for state in expected}
        rows.append({**case, "expected": expected, "actual": actual, "pass": expected == actual})
    return {"scope": "synthetic_alias_scope_not_clinical_validation", "protocol_version": "alias_scope_parent_direction_v2", "aliases": len(ALIASES), "total": len(rows), "passed": sum(row["pass"] for row in rows), "failed": sum(not row["pass"] for row in rows), "rows": rows}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit("Refusing to overwrite evidence")
    result = run()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({key: value for key, value in result.items() if key != "rows"}, ensure_ascii=False))
