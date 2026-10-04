from evaluation.core_exploration.canonical_name_bridge_audit import build_bridge


def test_existing_alias_conflict_is_not_overwritten():
    original = {"合成名称": "original_code"}
    candidate, additions, conflicts = build_bridge({"new_code": "合成名称"}, original)
    assert candidate == original and not additions
    assert conflicts == [{"name": "合成名称", "declared_codes": ["new_code"], "existing_code": "original_code"}]


def test_duplicate_declared_name_is_left_unresolved():
    candidate, additions, conflicts = build_bridge({"one": "同名", "two": "同名"}, {})
    assert not candidate and not additions and conflicts[0]["declared_codes"] == ["one", "two"]


def test_new_candidate_preserves_original_dictionary():
    original = {"旧名称": "old"}
    candidate, additions, conflicts = build_bridge({"new": "新名称"}, original)
    assert original == {"旧名称": "old"}
    assert candidate == {"旧名称": "old", "新名称": "new"}
    assert len(additions) == 1 and not conflicts
