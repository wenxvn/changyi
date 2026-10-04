from evaluation.core_exploration.cause_uncertainty_audit import run
import app


def test_unknown_cause_does_not_erase_reported_symptom():
    result = run()
    assert result["failed"] == 0, [row for row in result["rows"] if not row["pass"]]


def test_current_word_does_not_cancel_hypothetical_cause_context():
    prediction = app.predict_disease_name("假如现在不确定为什么咳嗽", details=True)
    assert prediction["abstained"] is True
    assert prediction["input_assertions"]["unknown"] == ["cough"]
