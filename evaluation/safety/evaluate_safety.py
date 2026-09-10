"""Run the provisional Safety Evaluation Set against the legacy triage path."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

from backend.app.domain.triage.safety_gate import triage_status_from_legacy


CASES_PATH = Path(__file__).with_name("safety_cases.json")


def load_cases(path: Path = CASES_PATH) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != "safety-evaluation/v1":
        raise ValueError("unsupported safety evaluation schema")
    return payload["cases"]


def _matches_expected(expected: str, observed: str) -> bool:
    if expected == "NOT_EMERGENCY":
        return observed != "EMERGENCY"
    return observed == expected


def evaluate_cases(
    cases: Iterable[Mapping[str, Any]],
    triage_fn: Callable[[str], Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    if triage_fn is None:
        from app import analyze_medical_triage

        triage_fn = analyze_medical_triage

    rows = []
    for case in cases:
        triage = triage_fn(str(case.get("condition") or ""))
        observed = triage_status_from_legacy(triage).value
        expected = str(case.get("expected_status") or "")
        rows.append({
            "id": str(case.get("id") or ""),
            "category": str(case.get("category") or ""),
            "expected_status": expected,
            "observed_status": observed,
            "matches_expectation": _matches_expected(expected, observed),
            "red_flag": bool(case.get("red_flag")),
            "review_status": str(case.get("review_status") or "review_required"),
        })

    red_flags = [row for row in rows if row["red_flag"]]
    negatives = [row for row in rows if row["expected_status"] == "NOT_EMERGENCY"]
    insufficiency = [row for row in rows if row["expected_status"] == "INSUFFICIENT_INFORMATION"]
    red_flag_misses = [row for row in red_flags if row["observed_status"] != "EMERGENCY"]
    emergency_false_positives = [row for row in negatives if row["observed_status"] == "EMERGENCY"]
    review_required = [
        row["id"] for row in rows
        if row["review_status"] == "review_required" or not row["matches_expectation"]
    ]

    def rate(numerator: int, denominator: int) -> float | None:
        return round(numerator / denominator, 4) if denominator else None

    return {
        "schema_version": "safety-evaluation-report/v1",
        "case_count": len(rows),
        "red_flag_count": len(red_flags),
        "red_flag_recall": rate(len(red_flags) - len(red_flag_misses), len(red_flags)),
        "under_triage_rate": rate(len(red_flag_misses), len(red_flags)),
        "over_triage_rate": rate(len(emergency_false_positives), len(negatives)),
        "emergency_false_negative": len(red_flag_misses),
        "insufficient_information_count": len(insufficiency),
        "insufficient_information_matches": sum(
            row["observed_status"] == "INSUFFICIENT_INFORMATION" for row in insufficiency
        ),
        "review_required": review_required,
        "cases": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, default=CASES_PATH)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    report = evaluate_cases(load_cases(args.cases))
    if args.as_json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"Safety Evaluation Set: {report['case_count']} cases")
        print(f"Red Flag Recall: {report['red_flag_recall']}")
        print(f"Under-triage Rate: {report['under_triage_rate']}")
        print(f"Over-triage Rate: {report['over_triage_rate']}")
        print(f"Emergency False Negative: {report['emergency_false_negative']}")
        print("Review required: " + ", ".join(report["review_required"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
