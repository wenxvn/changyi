"""Interpretable stopping policies for adaptive inquiry.

Thresholds must be chosen from train/calibration only — never tuned on test.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence


@dataclass(frozen=True)
class StoppingPolicy:
    name: str
    description: str
    max_questions: int
    confidence_threshold: float | None = None
    entropy_ratio_threshold: float | None = None
    set_size_threshold: int | None = None
    margin_threshold: float | None = None

    def should_stop(
        self,
        *,
        entropy: float,
        confidence: float,
        margin: float,
        set_size: int,
        questions_asked: int,
        max_questions: int | None = None,
        max_entropy: float | None = None,
    ) -> bool:
        limit = max_questions if max_questions is not None else self.max_questions
        if questions_asked >= limit:
            return True
        if self.confidence_threshold is not None and confidence >= self.confidence_threshold:
            return True
        if (
            self.entropy_ratio_threshold is not None
            and max_entropy
            and max_entropy > 0
            and (entropy / max_entropy) <= self.entropy_ratio_threshold
        ):
            return True
        if self.set_size_threshold is not None and set_size <= self.set_size_threshold:
            return True
        if self.margin_threshold is not None and margin >= self.margin_threshold:
            return True
        return False

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "max_questions": self.max_questions,
            "confidence_threshold": self.confidence_threshold,
            "entropy_ratio_threshold": self.entropy_ratio_threshold,
            "set_size_threshold": self.set_size_threshold,
            "margin_threshold": self.margin_threshold,
        }


def fit_stopping_thresholds_from_calibration(
    calibration_rows: Sequence[Mapping[str, Any]],
    predict_fn,
) -> dict[str, float]:
    """Choose simple quantile thresholds on calibration predictions only.

    ``predict_fn(row) -> (confidence, entropy, margin, set_size)``
    """

    if not calibration_rows:
        return {
            "confidence_threshold": 0.70,
            "entropy_ratio_threshold": 0.35,
            "set_size_threshold": 1,
            "margin_threshold": 0.25,
        }
    confidences = []
    entropy_ratios = []
    margins = []
    set_sizes = []
    for row in calibration_rows:
        confidence, entropy, margin, set_size, max_entropy = predict_fn(row)
        confidences.append(confidence)
        entropy_ratios.append(entropy / max_entropy if max_entropy else 0.0)
        margins.append(margin)
        set_sizes.append(set_size)
    confidences.sort()
    ratios = sorted(entropy_ratios)
    margin_sorted = sorted(margins)
    n = len(calibration_rows)

    def q(values: Sequence[float], quantile: float) -> float:
        index = min(int(quantile * (len(values) - 1)), len(values) - 1)
        return float(values[index])

    return {
        # Stop when confidence is already high relative to calibration.
        "confidence_threshold": round(q(confidences, 0.70), 4),
        "entropy_ratio_threshold": round(q(ratios, 0.30), 4),
        "set_size_threshold": 1,
        "margin_threshold": round(q(margin_sorted, 0.70), 4),
    }


def default_policies(max_questions: int = 5, thresholds: Mapping[str, float] | None = None) -> list[StoppingPolicy]:
    t = dict(thresholds or {})
    conf = float(t.get("confidence_threshold", 0.70))
    ent = float(t.get("entropy_ratio_threshold", 0.35))
    margin = float(t.get("margin_threshold", 0.25))
    set_size = int(t.get("set_size_threshold", 1))
    return [
        StoppingPolicy(
            name="fixed_n",
            description=f"Always ask up to {max_questions} questions",
            max_questions=max_questions,
        ),
        StoppingPolicy(
            name="entropy_threshold",
            description="Stop when entropy ratio is below calibration quantile",
            max_questions=max_questions,
            entropy_ratio_threshold=ent,
        ),
        StoppingPolicy(
            name="prediction_set_threshold",
            description="Stop when top-3 prediction set is already tiny (set_size<=1)",
            max_questions=max_questions,
            set_size_threshold=set_size,
        ),
        StoppingPolicy(
            name="combined",
            description="Stop when confident OR low entropy OR small set OR large margin",
            max_questions=max_questions,
            confidence_threshold=conf,
            entropy_ratio_threshold=ent,
            set_size_threshold=set_size,
            margin_threshold=margin,
        ),
    ]


def policy_as_callable(policy: StoppingPolicy):
    def _fn(
        *,
        entropy: float,
        confidence: float,
        margin: float,
        set_size: int,
        questions_asked: int,
        max_questions: int | None = None,
        max_entropy: float | None = None,
    ) -> bool:
        return policy.should_stop(
            entropy=entropy,
            confidence=confidence,
            margin=margin,
            set_size=set_size,
            questions_asked=questions_asked,
            max_questions=max_questions,
            max_entropy=max_entropy,
        )

    return _fn
