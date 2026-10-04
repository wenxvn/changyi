import app
from evaluation.core_exploration.negated_denial_audit import run


def test_negated_denial_cannot_remove_existing_danger_signal():
    result = run()
    assert result["failed"] == 0, [row for row in result["rows"] if not row["pass"]]


def test_negated_denial_does_not_cancel_later_real_denial():
    assert app._contains_positive("我不否认咳嗽但没有胸痛", ["胸痛"]) is False
    assert app._contains_positive("我不否认呼吸困难", ["呼吸困难"]) is True
