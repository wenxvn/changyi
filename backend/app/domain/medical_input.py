"""Pure functions for normalizing patient wording and handling negation windows.

This module deliberately has no Flask, data repository, model, or routing
dependency. It preserves the legacy input behavior while giving the later
Safety Gate a single, testable input boundary.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import re
from typing import Any

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
    "胸口疼": "胸痛",
    "心口压着": "胸闷",
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


@dataclass(frozen=True)
class FollowupAnswer:
    """One answer kept separate from the patient's original free-text input."""

    question_id: str
    value: str | None = None
    text_answer: str | None = None


@dataclass(frozen=True)
class TriageInput:
    """Canonical triage input; follow-up prompts never become symptom text."""

    original_condition: str
    scenario: str = "common"
    followup_answers: tuple[FollowupAnswer, ...] = ()


def normalize_followup_answers(raw_answers: Sequence[Mapping[str, Any]] | None) -> tuple[FollowupAnswer, ...]:
    """Normalize already-validated structured answers for rule evaluation."""

    normalized: list[FollowupAnswer] = []
    for answer in raw_answers or ():
        question_id = str(answer.get("question_id") or "").strip()
        value = answer.get("value")
        text_answer = answer.get("text_answer")
        normalized.append(FollowupAnswer(
            question_id=question_id,
            value=value.strip() if isinstance(value, str) else None,
            text_answer=text_answer.strip() if isinstance(text_answer, str) else None,
        ))
    return tuple(normalized)


def followup_answer_map(raw_answers: Sequence[Mapping[str, Any]] | Sequence[FollowupAnswer] | None) -> dict[str, str]:
    """Return a stable question-id to answer-value map for safety rules."""

    result: dict[str, str] = {}
    for answer in raw_answers or ():
        if isinstance(answer, FollowupAnswer):
            value = answer.value or answer.text_answer
            question_id = answer.question_id
        else:
            value = answer.get("value") or answer.get("text_answer")
            question_id = str(answer.get("question_id") or "")
        if question_id and isinstance(value, str) and value.strip():
            result[question_id] = value.strip()
    return result


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


CURRENT_SELF_MARKERS = (
    "我现在", "我目前", "我突然", "我今天", "我刚刚", "我刚", "我正",
    "现在我", "正在我", "刚出现", "刚发生", "刚发现", "今天突然", "突然我",
    "目前我", "现症", "当前症状", "现在突然",
)


COPULA_EXISTENCE_SIGNALS = frozenset({"呼吸困难", "喘不上气", "意识不清", "抽搐", "惊厥"})


def has_explicit_existence_question(prefix, signal=None):
    # Limit the new copula scope to registered symptom cues. Existing disease
    # concern policies are distinct from asking whether a symptom exists.
    copula = "|是不是" if signal in COPULA_EXISTENCE_SIGNALS else ""
    return bool(re.search(
        rf"(?:不确定|说不清)?(?:有没有|(?:是否{copula})(?:有|存在|没有|不存在)?)(?:明显|持续|真的|出现|存在)?\s*$", prefix))


def uncertain_signal_mentions(text, signal_words):
    """Find explicit uncertainty before existing risk terms, not diagnoses."""
    found = []
    marker = r"(?:不确定|说不清)?(?:有没有|是否(?:有|存在)?)"
    for word in sorted(set(signal_words), key=len, reverse=True):
        if word and re.search(marker + r"(?:明显|持续|真的|出现|存在)?" + re.escape(word), text):
            found.append(word)
        elif word:
            for match in re.finditer(re.escape(word), text):
                prefix = re.split(r"[，,。；;！？\n]|但是|但|不过|而是", text[:match.start()])[-1]
                if has_explicit_hypothetical_prefix(prefix) or has_explicit_existence_question(prefix, word):
                    found.append(word)
                    break
    return found


def _seizure_report_contexts(text):
    """Reports needing risk confirmation, independent of learned vocabulary.

    This is a conservative review policy, not a seizure diagnosis. Existing
    confirmed emergency rules must run before callers use this result.
    """
    found = []
    for match in re.finditer(r"抽搐|惊厥", text):
        prefix = re.split(r"[，,。；;！？\n]|但是|但|不过", text[:match.start()])[-1]
        suffix = re.split(r"[，,。；;！？\n]|但是|但|不过", text[match.end():])[0]
        uncertain = bool(re.search(r"不确定|说不清|有没有|是否|不是没有|会不会", prefix) or re.match(r"不确定|说不清", suffix))
        uncertain = uncertain or has_explicit_existence_question(prefix, match.group())
        current = bool(re.search(r"现在|目前|正在|刚刚|今天", prefix))
        if re.search(r"科普|什么是|如果|假如", prefix):
            continue
        if re.match(r"是什么|是什么意思", suffix):
            continue
        if re.search(r"曾经|以前|小时候|去年|历史", prefix) and not current:
            continue
        denial = re.search(r"(?:没有|没|否认(?:有)?|未(?:见|出现)?|不伴)(?:明显的?)?(?:持续|一直(?:在)?)?$", prefix)
        if not denial:
            # Only registered risk terms in an explicit negative list; do not
            # treat denial of another unrelated fact as denial of this report.
            member = r"(?:意识混乱|意识不清|意识异常|呼吸困难|胸痛|抽搐|惊厥)"
            denial = re.search(r"(?:没有|没|无|否认(?:有)?|未见|未出现|不伴(?:有)?)"
                               + member + r"(?:[、和及与或]" + member + r")*[、和及与或]$", prefix)
        negated_denial = bool(denial and denial.group().startswith("否认") and denial.start() > 0 and prefix[denial.start() - 1] == "不")
        if not uncertain and denial and not negated_denial:
            continue
        if re.fullmatch(r"(?:已经|已|现在)?(?:好了|消失(?:了)?|没有了|痊愈)", suffix):
            continue
        ongoing = bool(re.search(r"(?:持续|一直(?:在)?)$", prefix) or suffix.startswith("不止"))
        found.append({"signal": match.group(), "uncertain": uncertain, "ongoing": ongoing})
    return found


def seizure_review_mentions(text):
    return sorted({item["signal"] for item in _seizure_report_contexts(text)})


def uncertain_seizure_mentions(text):
    return sorted({item["signal"] for item in _seizure_report_contexts(text) if item["uncertain"]})


def seizure_current_emergency_report(text):
    return any(item["ongoing"] and not item["uncertain"] for item in _seizure_report_contexts(text))

QUESTION_OR_HISTORY_MARKERS = (
    "是不是", "会不会", "算不算", "什么情况下", "什么情况会",
    "家里人", "家人", "父母", "我爸", "我妈", "孩子会", "小孩会", "老人会",
    "以前", "历史上", "曾经", "过去", "之前", "听说", "据说",
    "吗", "么？",
)


def is_general_question_or_history(text):
    """True when the phrasing looks like a general question or third-party/history.

    A first-person current-state assertion always wins, so
    "我现在说话不清，是不是中风" still counts as a current symptom report.
    """

    normalized = "".join((text or "").split())
    if not normalized:
        return False
    if any(marker in normalized for marker in CURRENT_SELF_MARKERS):
        return False
    bystander = r"(?:我妈妈|我妈|我爸爸|我爸|家人|孩子|小孩|老人|朋友)(?:现在|目前|正在|刚刚|突然)"
    educational_bystander = False
    for match in re.finditer(bystander, normalized):
        prefix = re.split(r"[，,。；;！？\n]|但是|但|不过", normalized[:match.start()])[-1]
        if re.search(r"如果|假如|科普|什么是", prefix):
            educational_bystander = True
            continue
        # An explicit current report follows the same existing risk rules
        # regardless of whether the person typing is the person affected.
        return False
    if educational_bystander:
        return True
    return any(marker in normalized for marker in QUESTION_OR_HISTORY_MARKERS)


NON_DISEASE_ROUTING_TERMS = frozenset({"中医", "针灸", "推拿", "产科", "产检", "分娩", "产后"})


def consultation_route_scope(text):
    """Limited anonymous subject scope for non-Safety routing, never identity."""
    self_marks = list(re.finditer(r"现在我(?!妈|爸)|目前我(?!妈|爸)|我现在|我目前|我自己", text))
    proxy_marks = []
    for mark in re.finditer(r"(?:代替|帮|代|替)(?:我)?(?:妈妈|爸爸|家人|母亲|父亲|她|他)", text):
        prefix = re.split(r"[，,。；;！？\n]|但是|但|不过", text[:mark.start()])[-1]
        if not re.search(r"(?:不是|并非|不|没有|无须)$", prefix):
            proxy_marks.append(mark)
    if not self_marks or (proxy_marks and proxy_marks[-1].start() > self_marks[-1].start()):
        return {"routing_text": text, "background_text": "", "explicit_self": False}
    current, background = [], []
    role = "self"
    for clause in re.split(r"[，,。；;！？\n]|但是|但|不过", text):
        marks = list(re.finditer(r"我妈妈|我妈|我爸爸|我爸|家人|母亲|父亲|妈妈|爸爸|孩子|(?<!其)[她他]|我(?!妈|爸)", clause))
        start = 0
        for mark in marks:
            if mark.start() > start:
                (current if role == "self" else background).append(clause[start:mark.start()])
            role = "self" if mark.group() == "我" else "relative"
            start = mark.start()
        (current if role == "self" else background).append(clause[start:])
    return {"routing_text": "，".join(current), "background_text": "，".join(background), "explicit_self": True}


def is_non_disease_routing_term(term, department=""):
    """Limited directory/context taxonomy, not an exhaustive medical ontology."""
    return term in NON_DISEASE_ROUTING_TERMS or (term == department and term.endswith("科"))


def has_local_hypothesis(prefix, suffix):
    """Recognize explicit local hypothetical wording, without a Safety decision."""
    return bool(re.search(r"如果|假如|假设|倘若", prefix[-16:])
                or re.match(r"(?:只是|仅是|仅仅是|是)(?:一个|一种)?(?:假设|假想|举例|例子)", suffix))


def has_explicit_hypothetical_prefix(prefix):
    """Limited direct hypothetical existence wording; never a model signal."""
    return bool(re.search(
        r"(?:如果|假如|假设|倘若)\s*(?:我(?:妈妈|爸爸)?|家人|妈妈|爸爸|朋友)?\s*(?:现在|目前|正在)?\s*(?:不否认)?\s*(?:有|出现)?\s*(?:明显|持续)?\s*$",
        prefix,
    ))


UNRESOLVED_EXCLUSION_ACTION = r"(?:未(?:能(?:够)?)?|不能(?:够)?|无法|没(?:有|能(?:够)?)?)\s*(?:明确|完全)?\s*排除"


def has_unresolved_exclusion_action(prefix, *, starts_at_token=False):
    if starts_at_token:
        return bool(re.match(UNRESOLVED_EXCLUSION_ACTION, prefix))
    return bool(re.search(UNRESOLVED_EXCLUSION_ACTION + r"\s*$", prefix))


def known_disease_mention_state(text, word):
    """Classify a disease mention as reported, uncertain, or absent; not diagnose."""
    states = []
    for match in re.finditer(re.escape(word), text):
        prefix = re.split(r"[，,。；;！？\n]|但是|但|不过", text[:match.start()])[-1]
        suffix = re.split(r"[，,。；;！？\n]", text[match.end():])[0]
        if has_unresolved_exclusion_action(prefix):
            states.append("uncertain")
            continue
        completed_exclusion = re.search(r"(?:已经|已|明确)\s*排除\s*$", prefix)
        if completed_exclusion:
            before_action = prefix[:completed_exclusion.start()]
            blocked = bool(re.search(r"(?:未(?:能)?|不能|无法|不|尚未|将|准备|计划|需要|建议)\s*$", before_action))
            states.append("uncertain" if blocked else "absent")
            continue
        uncertain = bool(re.search(r"不确定|是否|是不是|怀疑|疑似|可能|会不会|担心|待排|未确诊|误诊|不否认", prefix[-16:]))
        uncertain = uncertain or bool(re.search(r"(?:考虑|倾向(?:于)?|不能排除|未(?:能)?排除|排查)(?:诊断)?(?:为|是|有|患有)?\s*$", prefix))
        uncertain = uncertain or bool(re.match(r"(?:但|但是|现在)?(?:不确定|未确诊|尚未确诊|待确认|是什么|是什么意思)", suffix))
        # Only a direct predicate qualifies; a later hypothetical symptom does
        # not turn an already reported disease into an uncertain mention.
        uncertain = uncertain or has_local_hypothesis(prefix, suffix)
        if uncertain:
            states.append("uncertain")
        elif contains_positive_known_disease(prefix.replace(word, " " * len(word)) + word, [word]):
            states.append("asserted")
        else:
            states.append("absent")
    if "asserted" in states:
        return "conflicting" if any(state != "asserted" for state in states) else "asserted"
    if states and states[-1] == "absent":
        return "absent"
    return "uncertain" if "uncertain" in states else "absent"


def contains_positive_known_disease(text, words):
    """Preserve explicit local confirmation when another clause denies a symptom."""
    if contains_positive(text, words):
        return True
    for word in words:
        if not word:
            continue
        for match in re.finditer(re.escape(word), text):
            prefix = re.split(r"[，,。；;！？\n]|但是|但|不过", text[:match.start()])[-1]
            if re.search(r"已确诊|确诊|诊断为|患有", prefix) and contains_positive(prefix + word, [word]):
                return True
    return False


def contains_current_safety_signal(text, words, *, require_current=False):
    """Match Safety evidence per occurrence, excluding explicit past context.

    Only Safety callers use this boundary; it does not rewrite the user's text
    or classify diseases. Existing negation logic remains the positive check.
    """
    for word in words:
        if not word:
            continue
        for match in re.finditer(re.escape(word), text):
            prefix = re.split(r"[，,。；;！？\n]|但是|但|不过", text[:match.start()])[-1]
            suffix = re.split(r"[，,。；;！？\n]|但是|但|不过", text[match.end():])[0]
            if has_explicit_hypothetical_prefix(prefix):
                continue
            # This occurrence asks whether the signal exists. Another actual
            # occurrence remains eligible; cause uncertainty is not existence.
            if has_explicit_existence_question(prefix, word):
                continue
            current_markers = list(re.finditer(r"现在|目前|正在|今天|刚刚", prefix))
            temporal_prefix = prefix[current_markers[-1].end():] if current_markers else prefix
            historical = bool(re.search(r"以前|曾经|去年|小时候|既往|历史上|过去|之前", temporal_prefix))
            unresolved = bool(re.match(r"(?:仍|仍然|一直|尚未|还)(?:未恢复|没有恢复|没有好|未缓解|不缓解|在持续)", suffix))
            # Limit this historical-to-current exception to existing direct
            # breathing/consciousness cues, never disease recovery labels.
            unresolved_strong = unresolved and word in {"呼吸困难", "喘不上气", "意识不清", "呼之不应"}
            direct_self = bool(re.fullmatch(r"\s*我(?:有|出现|感觉|感觉到)?\s*", prefix))
            direct_self = direct_self and not bool(re.match(
                r"(?:是不是|是否|有没有|不确定|说不清|已经好了|已好了|好了|消失|痊愈)", suffix))
            if require_current and (not (current_markers or unresolved_strong or direct_self) or re.search(r"科普|如果|假如|什么是", prefix)):
                continue
            if historical and not unresolved:
                continue
            # Neutralize earlier identical occurrences in the prefix so the
            # legacy helper checks this occurrence, retaining its negation span.
            negation_prefix = (prefix[current_markers[-1].end():] if current_markers
                               else prefix if direct_self else text[:match.start()])
            local_prefix = negation_prefix[-16:].replace(word, " " * len(word))
            if contains_positive(local_prefix + word, [word]):
                return True
    return False


def qualified_chest_presence_pending(text):
    """A bounded denial of severity does not resolve current chest presence."""
    if contains_current_safety_signal(text, ["胸痛"]):
        return False
    for match in re.finditer("胸痛", text):
        prefix = re.split(r"[，,。；;！？\n]|但是|但|不过|而是", text[:match.start()])[-1]
        denial = re.search(r"(?P<neg>没有|没|否认|不是)\s*(?:有|出现)?\s*(?:严重|剧烈)\s*(?:的)?\s*$", prefix)
        if not denial:
            continue
        previous = prefix[denial.start() - 1] if denial.start() else ""
        if (denial["neg"] in {"没有", "没"} and previous == "有") or (denial["neg"] == "否认" and previous == "不") or (denial["neg"] == "不是" and previous == "是"):
            continue
        current = list(re.finditer(r"现在|目前|正在|今天|刚刚", prefix))
        context = prefix[current[-1].end():] if current else prefix
        if re.search(r"以前|曾经|去年|小时候|既往|历史上|过去|之前", context):
            continue
        return True
    return False


def contains_positive(text, words):
    """Return whether any word occurs outside the legacy negation window."""
    neg_prefixes = ("无", "没有", "没", "未", "否认", "不伴", "未见", "不是")
    neg_breakers = ("但", "但是", "不过", "然而", "却", "仍", "仍然", "伴", "伴有", "出现", "而是")
    # Double-negation phrases assert presence; never treat them as a clear denial.
    double_neg_markers = ("不是没有", "并非没有", "不能说没有", "不是没", "并非没")
    hard_boundaries = "。！？；;\n\r"

    def is_negated(start):
        window_start = max(0, start - 16)
        prefix = text[window_start:start]
        # Only an explicit new current clause ends the preceding denial.
        # A comma alone still permits coordinated negation (没有胸痛，咳嗽).
        current_clauses = list(re.finditer(r"[，,]\s*(?:我\s*)?(?:现在|目前|正在|今天|刚刚)", prefix))
        if current_clauses:
            prefix = prefix[current_clauses[-1].end():]
        for mark in hard_boundaries:
            idx = prefix.rfind(mark)
            if idx != -1:
                prefix = prefix[idx + 1:]
        double_spans = [match.span() for marker in double_neg_markers
                        for match in re.finditer(re.escape(marker), prefix)]
        negations = [(match.start(), neg) for neg in neg_prefixes for match in re.finditer(re.escape(neg), prefix)
                     if not any(left <= match.start() < right for left, right in double_spans)
                     if not (neg in {"未", "无", "没", "没有"} and has_unresolved_exclusion_action(prefix[match.start():]))
                     if not (match.start() > 0 and ((neg == "不是" and prefix[match.start() - 1] == "是")
                                                    or (neg == "否认" and prefix[match.start() - 1] == "不")))]
        if not negations:
            return False
        neg_pos, neg_word = max(negations)
        # A negated predicate (不伴/未出现) is not a new positive clause.
        # Breakers only act after the negative token and its direct predicate.
        tail = prefix[neg_pos + len(neg_word):]
        tail = re.sub(r"^(?:(?:有|出现|伴有|伴随)\s*)+", "", tail)
        if neg_word == "不是" and any(bridge in tail for bridge in ("引起", "导致", "造成")):
            return False
        if any(br in tail for br in neg_breakers):
            return False
        return len(prefix[neg_pos:]) <= 14

    for word in words:
        if not word:
            continue
        start = text.find(word)
        while start != -1:
            if not is_negated(start):
                return True
            start = text.find(word, start + len(word))
    return False
