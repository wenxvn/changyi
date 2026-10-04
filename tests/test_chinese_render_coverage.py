from evaluation.core_exploration.chinese_render_coverage_audit import audit_rows


def test_untranslated_and_unrecoverable_features_keep_full_denominator():
    rows = [{"symptoms": ["cough", "untranslated"]}, {"symptoms": ["unmatched_name", "cough"]}]
    result = audit_rows(rows, {"cough": "咳嗽", "unmatched_name": "合成未登记名称"}, {"咳嗽": "cough"})
    assert result["total"] == 2 and result["symptom_occurrences"] == 4
    assert result["named_occurrences"] == 3 and result["english_fallback_occurrences"] == 1
    assert result["fully_named_rows"] == 1
    assert result["named_but_not_recovered_occurrences"] == 1
    assert len(result["rows"]) == 2 and len(result["codes"]) == 3


def test_empty_inventory_does_not_fabricate_coverage():
    result = audit_rows([], {}, {})
    assert result["total"] == result["symptom_occurrences"] == result["fully_named_rows"] == 0
