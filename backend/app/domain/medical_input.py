"""Pure functions for normalizing patient wording and handling negation windows.

This module deliberately has no Flask, data repository, model, or routing
dependency. It preserves the legacy input behavior while giving the later
Safety Gate a single, testable input boundary.
"""

from __future__ import annotations


COLLOQUIAL_SYMPTOM_ALIASES = {
    "喘不上来": "呼吸困难",
    "上不来气": "呼吸困难",
    "喘不过气": "呼吸困难",
    "喘不来气": "呼吸困难",
    "透不过气": "呼吸困难",
    "胸口压榨样疼痛": "胸痛",
    "压榨样胸痛": "胸痛",
    "冒冷汗": "出冷汗",
    "冷汗直冒": "出冷汗",
    "胸口堵": "胸闷",
    "胸口压着": "胸闷",
    "心口疼": "胸痛",
    "心脏疼": "胸痛",
    "嗓子不舒服": "咽痛",
    "喉咙疼": "咽痛",
    "拉肚子": "腹泻",
    "肚子疼": "腹痛",
    "胃不舒服": "胃痛",
    "想吐": "恶心",
    "头昏": "头晕",
    "天旋地转": "眩晕",
    "半边身子没劲": "一侧无力",
    "嘴歪": "口角歪斜",
    "说不清话": "说话不清",
    "身上起疙瘩": "皮疹",
    "皮肤痒": "皮肤瘙痒",
    "眼睛看不清": "视力下降",
    "小便疼": "尿痛",
    "尿里有血": "血尿",
    "血糖高": "糖尿病",
}

KNOWN_DISEASE_PATTERNS = [
    "已确诊", "确诊", "医生说", "诊断为", "检查说", "查出来", "复诊", "术后复查",
    "患有", "得了", "我是", "病史", "既往", "报告提示", "考虑",
]


def normalize_patient_expression(condition):
    """Append the current canonical Chinese wording for known colloquialisms."""
    text = condition or ""
    normalized = text
    replacements = []
    for raw, standard in COLLOQUIAL_SYMPTOM_ALIASES.items():
        if raw in text and standard not in normalized:
            normalized += f" {standard}"
            replacements.append({"raw": raw, "standard": standard})
    return normalized, replacements


def contains_positive(text, words):
    """Return whether any word occurs outside the legacy negation window."""
    neg_prefixes = ("无", "没有", "没", "未", "否认", "不伴", "未见")
    neg_breakers = ("但", "但是", "不过", "然而", "却", "仍", "仍然", "伴", "伴有", "出现")
    hard_boundaries = "。！？；;\n\r"

    def is_negated(start):
        window_start = max(0, start - 16)
        prefix = text[window_start:start]
        for mark in hard_boundaries:
            idx = prefix.rfind(mark)
            if idx != -1:
                prefix = prefix[idx + 1:]
        neg_pos = max(prefix.rfind(neg) for neg in neg_prefixes)
        if neg_pos == -1:
            return False
        tail = prefix[neg_pos:]
        if any(br in tail for br in neg_breakers):
            return False
        return len(tail) <= 14

    for word in words:
        if not word:
            continue
        start = text.find(word)
        while start != -1:
            if not is_negated(start):
                return True
            start = text.find(word, start + len(word))
    return False
