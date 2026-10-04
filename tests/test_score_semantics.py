import app
from evaluation.core_exploration.score_semantics_audit import run


def test_score_publication_semantics():
    result = run()
    assert result["failed"] == 0, [row for row in result["rows"] if not row["pass"]]


def test_legacy_relative_score_formula_is_preserved():
    candidates = app.build_htriage_analysis("咳嗽")["disease_candidates"]
    assert candidates and candidates[0]["probability"] == 82
    assert all(8 <= row["probability"] <= 92 for row in candidates)
