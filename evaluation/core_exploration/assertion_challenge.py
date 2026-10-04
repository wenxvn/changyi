"""Synthetic Chinese assertion regression challenge, never clinical accuracy."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from .semantic_bridge import ALIASES, parse_chinese

SYMPTOMS = ("咳嗽", "头痛", "恶心", "腹泻", "胸痛", "鼻塞")
# Expected states are specified independently of the implementation.
TEMPLATES = (
    ("positive", "我有{s}", "present"),
    ("negative", "没有{s}", "absent"),
    ("negative_with_particle", "没有明显的{s}", "absent"),
    ("denied_presence", "否认有{s}", "absent"),
    ("not_occurred", "未出现{s}", "absent"),
    ("post_negative", "{s}没有了", "absent"),
    ("uncertain", "不确定有没有{s}", "unknown"),
    ("post_uncertain", "{s}不确定", "unknown"),
    ("past", "曾经{s}", "unknown"),
    ("past_year", "去年有{s}", "unknown"),
    ("resolved", "{s}已经好了", "unknown"),
    ("resolved_disappearance", "{s}已消失", "unknown"),
    ("not_improved", "{s}没有减轻", "present"),
    ("not_resolved", "{s}没有好", "present"),
    ("partly_improved", "{s}有所好转", "present"),
)


def cases():
    for symptom in SYMPTOMS:
        for family, template, state in TEMPLATES:
            yield {"family": family, "text": template.format(s=symptom), "expected": {state: [ALIASES[symptom]]}}
    for first in SYMPTOMS:
        for second in SYMPTOMS:
            if first == second:
                continue
            yield {"family": "contrast", "text": f"没有{first}，但是有{second}", "expected": {"absent": [ALIASES[first]], "present": [ALIASES[second]]}}
            yield {"family": "coordinated_denial", "text": f"没有{first}和{second}", "expected": {"absent": sorted([ALIASES[first], ALIASES[second]])}}
            for prefix in ("否认有", "未出现"):
                yield {"family": "expanded_coordinated_denial", "text": f"{prefix}{first}和{second}", "expected": {"absent": sorted([ALIASES[first], ALIASES[second]])}}


def run():
    rows = []
    for case in cases():
        parsed = parse_chinese(case["text"])
        expected = {state: sorted(case["expected"].get(state, [])) for state in ("present", "absent", "unknown")}
        actual = {state: parsed[state] for state in expected}
        rows.append({**case, "expected": expected, "actual": actual, "pass": expected == actual})
    return {"scope": "synthetic_assertion_regression_not_clinical_validation", "total": len(rows), "passed": sum(row["pass"] for row in rows), "failed": sum(not row["pass"] for row in rows), "rows": rows}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit("Refusing to overwrite prior evidence")
    result = run()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({key: result[key] for key in ("scope", "total", "passed", "failed")}, ensure_ascii=False))
