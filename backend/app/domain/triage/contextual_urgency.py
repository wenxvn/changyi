"""Bounded compound-symptom urgency, independent of any learned model.

Sources: NHS DVT and kidney-infection public guidance. This asks for timely
assessment, does not diagnose either condition or prescribe treatment.
"""
from __future__ import annotations
import re
from ..medical_input import contains_current_safety_signal

URINARY_PAIN = ("排尿灼痛", "排尿疼痛", "尿痛", "小便疼")
FLANK_PAIN = ("腰侧疼痛", "腰侧痛", "腰痛", "背部疼痛", "背痛")
FEVER = ("发热", "发烧", "高热", "高烧")


def _affirmed(text, terms, *, start_at=0):
    covered = []
    for term in sorted(terms, key=len, reverse=True):
        for match in re.finditer(re.escape(term), text):
            if match.start() < start_at or any(left <= match.start() and match.end() <= right for left, right in covered):
                continue
            covered.append(match.span())
            prefix, suffix = text[:match.start()], text[match.end():]
            if re.match(r"(?:已经|已|现在)?(?:好了|没有了|消失|痊愈)", suffix):
                continue
            if re.match(r"(?:是否|不确定|说不清|是不是|有没有)", suffix):
                continue
            if re.search(r"不确定|是否|是不是|有没有|可能|会不会", prefix[-16:]):
                continue
            # Other occurrences cannot supply this occurrence's truth value.
            local = prefix.replace(term, " " * len(term)) + term
            if contains_current_safety_signal(local, [term]):
                return term
    return None


def _fragments(text):
    for fragment in re.split(r"[。；;！？\n]|但是|但|不过|而是", text):
        if re.search(r"科普|如果|假如|假设|什么是|举例|例如|听说|会有", fragment):
            continue
        actors = set(re.findall(r"我妈妈|我妈|我爸爸|我爸|家人|妈妈|爸爸|朋友|孩子|她|他|我", fragment))
        if len(actors) > 1:
            continue
        yield fragment


def contextual_urgent_assessment(text):
    for fragment in _fragments(text):
        urinary = _affirmed(fragment, URINARY_PAIN)
        flank = _affirmed(fragment, FLANK_PAIN)
        fever = _affirmed(fragment, FEVER)
        if urinary and flank and fever:
            return {"rule_id": "urinary_flank_fever_assessment", "name": "排尿疼痛合并发热和腰侧痛", "department": "急诊医学科",
                    "evidence": [urinary, flank, fever],
                    "reason": "排尿疼痛合并发热和腰背侧疼痛，需要尽快到医院线下评估，不能仅按普通症状安排；本系统不判断是否为感染。"}
        locations = list(re.finditer(r"(?:左|右|单侧|一侧|一条)(?:小腿|腿部|下肢|腿)", fragment))
        for location in locations:
            if not _affirmed(fragment[:location.end()], [location.group()]):
                continue
            # Do not merge another limb, body area, or person's pain into this
            # leg. Comparisons occurring after its own pain remain irrelevant.
            tail = fragment[location.end():]
            tail = re.split(r"(?:左|右|单侧|一侧|一条)(?:小腿|腿部|下肢|腿)|头部|头|手臂|胳膊|腹部|胸部|腰部|背部|我|她|他", tail)[0]
            local = fragment[:location.end()] + tail
            swelling = _affirmed(local, ("肿胀", "肿"), start_at=location.end())
            pain = _affirmed(local, ("疼痛", "酸痛", "疼", "痛"), start_at=location.end())
            if swelling and pain:
                return {"rule_id": "unilateral_leg_swelling_pain_assessment", "name": "单侧腿部肿痛需及时评估", "department": "急诊医学科",
                        "evidence": [location.group(), swelling, pain],
                        "reason": "当前单侧腿部肿胀并疼痛，需要尽快到医院线下评估，不能等待普通预约；本系统不判断是否为血栓。"}
    return None
