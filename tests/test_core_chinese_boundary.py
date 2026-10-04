from evaluation.core_exploration.semantic_bridge import parse_chinese


def test_uncertain_chest_pain_does_not_become_asserted_present():
    parsed = parse_chinese("担心会不会胸痛")
    assert "chest_pain" not in parsed["present"]
    assert parsed["needs_clarification"]


def test_resolved_history_blocks_learned_current_direction():
    parsed = parse_chinese("小时候胸痛，现在好了")
    assert parsed["needs_clarification"]


def test_unspecified_fever_is_not_high_fever():
    parsed = parse_chinese("发热")
    assert parsed["present"] == ["fever"]


def test_nested_alias_does_not_undo_a_denial():
    parsed = parse_chinese("没有连续打喷嚏")
    assert "continuous_sneezing" not in parsed["present"]
    assert "continuous_sneezing" in parsed["absent"]
