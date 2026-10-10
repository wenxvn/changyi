"""Reported type-1 background plus symptom cluster needs emergency review.

Based on NHS DKA and NIDDK public guidance; not a DKA diagnosis or treatment.
No model output, computed disease facts, test values or preferences are inputs.
"""
import re
from ..medical_input import known_disease_mention_state
from .contextual_urgency import _affirmed

TYPE1_NAMES = ("1型糖尿病", "一型糖尿病", "Ⅰ型糖尿病")
THIRST = ("口渴", "很渴", "特别渴")
URINATION = ("排尿很多", "排尿增多", "排尿多", "尿量增多", "多尿", "尿多", "尿频")
GI = ("恶心", "呕吐", "腹痛", "胃部不适", "胃部轻微不适", "胃不舒服")


def metabolic_emergency_assessment(text):
    # Do not combine one person's background with another person's symptoms.
    # This deliberately does not claim an exhaustive pronoun/subject resolver.
    actors = set(re.findall(r"我妈妈|我妈|我爸爸|我爸|家人|妈妈|爸爸|朋友|孩子|她|他|我", text))
    if len(actors) > 1 or re.search(r"科普|如果|假如|假设|什么是|举例|例如|听说", text):
        return None
    if re.search(r"(?:^|[，,。；;\n])(?:我)?(?:现在|目前|如今)(?:这些症状|症状)?(?:都|全|全部|完全)?(?:已经|已)?(?:好了|恢复正常|没有症状(?:了)?|没事(?:了)?)\s*[。！!？?]?$", text):
        return None
    background = next((name for name in TYPE1_NAMES if known_disease_mention_state(text, name) == "asserted"), None)
    if not background:
        return None
    thirst, urination, gi = _affirmed(text, THIRST), _affirmed(text, URINATION), _affirmed(text, GI)
    if not (thirst and urination and gi):
        return None
    return {"name": "糖尿病背景下的当前代谢风险组合", "evidence": [background, thirst, urination, gi],
            "department": "急诊医学科",
            "reason": "已报告1型糖尿病，并同时有当前口渴、排尿增多及胃肠不适，可能存在需要及时处理的代谢风险；没有意识混乱不能排除风险，请优先急诊专业评估。本系统不诊断酮症酸中毒。"}
