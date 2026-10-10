"""Conservative assertion extraction for auxiliary model input, never Safety."""
from __future__ import annotations
import re
from typing import Mapping
from .medical_input import has_local_hypothesis, has_explicit_hypothetical_prefix


def has_asserted_cough_route_evidence(text: str):
    """Bounded non-Safety routing evidence, independent of any model adapter."""
    state = parse_asserted_symptoms(text, {"咳嗽": "cough"})
    return ("cough" in state["present"] and "cough" not in state["unknown"]
            and "cough" not in state["contradiction"]
            and "cough" not in state["uncertainty_conflicts"]
            and not state["noncurrent_context"])


def _postposed_assertion(suffix: str, aliases: Mapping[str, str]):
    """Scope a complete trailing assertion over an explicit alias-only list."""
    terminal = re.search(r"(?P<collective>都|均)?(?P<state>没有(?:了)?|不确定|说不清)$", suffix)
    if not terminal:
        return None
    remaining = suffix[:terminal.start()]
    if remaining == "现在":
        remaining = ""
    if remaining:
        # Without 都/均, the statement may apply only to the last item.
        if not terminal["collective"] or remaining[0] not in "、和及与":
            return None
        terms = re.split(r"[、和及与]", remaining[1:])
        if not terms or not all(term in aliases for term in terms):
            return None
    return "absent" if terminal["state"].startswith("没有") else "unknown"


def parse_asserted_symptoms(text: str, aliases: Mapping[str, str], vocabulary=()):
    positive, negative, unknown = set(), set(), set()
    evidence, covered_spans = [], []
    noncurrent = bool(re.search(r"科普|问一下|什么是|如果出现|我妈妈|我爸爸|家里人|以前.+现在没有|(?:以前|小时候|去年).+(?:现在|如今).*(?:好了|没有|消失|痊愈)", text))
    document_noncurrent = noncurrent
    for alias, code in sorted(aliases.items(), key=lambda item: len(item[0]), reverse=True):
        if not alias or not re.search(r"[\u4e00-\u9fff]", alias):
            continue
        for match in re.finditer(re.escape(alias), text):
            if any(start <= match.start() and match.end() <= end for start, end in covered_spans):
                continue
            covered_spans.append((match.start(), match.end()))
            full_clause_prefix = re.split(r"[，,。；;！？\n]|但是|不过|但|后来|而是", text[:match.start()])[-1]
            clause_prefix = full_clause_prefix.rsplit("现在", 1)[-1]
            prefix = clause_prefix[-14:]
            suffix = re.split(r"[，,。；;！？\n]|但是|不过|但|而是", text[match.end():])[0].strip()
            postposed = _postposed_assertion(suffix, aliases)
            presence_prefix = re.sub(r"(?:不确定|说不清)(?:为什么|为何)", "", prefix)
            uncertain = bool(re.search(r"有没有|是否|是不是|不确定|说不清|好像|可能|不是没有|不是没|不否认|担心会不会|会不会", presence_prefix))
            uncertain = uncertain or bool(re.fullmatch(r"(?:是不是|是否|有没有)(?:存在|有|没有|不存在)?", suffix))
            uncertain = uncertain or has_local_hypothesis(prefix, suffix)
            uncertain = uncertain or has_explicit_hypothetical_prefix(full_clause_prefix)
            uncertain = uncertain or bool(re.search(
                r"(?:不确定(?:是否|有没有|是不是)?|是否|是不是|有没有|假如|如果|假设|倘若|可能)\s*(?:有|会|出现)?\s*现在\s*(?:有|会|出现|就|没有|没|无|不是)?\s*(?:明显|持续)?\s*$",
                full_clause_prefix,
            ))
            if presence_prefix != prefix:
                # The current-time delimiter must not turn a hypothetical
                # cause question into a report of an actual symptom.
                uncertain = uncertain or has_local_hypothesis(full_clause_prefix, suffix)
            uncertain = uncertain or postposed == "unknown"
            # Resolve complete postposed statements only: '没有减轻/没有好'
            # still describes a current symptom and must remain affirmative.
            absent = bool(re.search(r"(?:没有|没|无|未见|未|否认|不伴|不出现|不是)(?:有|出现)?(?:明显|任何|持续|一点)?的?$", prefix))
            absent = absent or postposed == "absent"
            historical = bool(re.search(r"曾经|之前|以前|去年|小时候", clause_prefix))
            resolved = bool(re.fullmatch(r"(?:已经|已|现在)?(?:好了|消失(?:了)?|痊愈(?:了)?)", suffix))
            mention_noncurrent = document_noncurrent or historical or resolved
            noncurrent = noncurrent or mention_noncurrent
            if not absent and re.search(r"[、和及与或]$", prefix):
                denial = list(re.finditer(r"(?:没有|没|无|未见|未|否认|不伴|不出现)(?:有|出现)?", clause_prefix))
                if denial:
                    after_denial = clause_prefix[denial[-1].end():]
                    absent = not bool(re.search(r"但是|不过|出现|伴有|(?:^|[、和及与])有", after_denial))
            state = "unknown" if uncertain or mention_noncurrent else "absent" if absent else "present"
            # A present child supports its coarse parent. Denying or being
            # unsure of one grade does not deny or establish all fever.
            codes = ["fever"] if alias in ("发热", "发烧") else (["fever", code] if code in ("high_fever", "mild_fever") and state == "present" else [code])
            (unknown if state == "unknown" else negative if state == "absent" else positive).update(codes)
            evidence.append({"alias": alias, "codes": codes, "state": state})
    # Explicit symbolic codes keep their existing developer/CLI contract.
    symbolic_tokens = [token for token in re.split(r"[;,，；|\s]+", text.lower()) if token]
    if symbolic_tokens and all(token in vocabulary for token in symbolic_tokens):
        positive.update(symbolic_tokens)
    contradiction = positive & negative
    uncertainty_conflicts = unknown & (positive | negative)
    negative -= positive
    unknown -= positive | negative
    return {"present": sorted(positive), "absent": sorted(negative), "unknown": sorted(unknown), "contradiction": sorted(contradiction), "uncertainty_conflicts": sorted(uncertainty_conflicts), "noncurrent_context": noncurrent, "evidence": evidence, "needs_clarification": bool(contradiction or unknown or uncertainty_conflicts or noncurrent or not positive), "scope": "auxiliary_model_input_not_safety_gate"}
