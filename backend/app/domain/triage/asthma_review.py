"""Clarify ongoing asthma rescue response without inferring a drug dose."""
import re
from ..medical_input import known_disease_mention_state
from .contextual_urgency import _affirmed


def asthma_rescue_context(text):
    actors = set(re.findall(r"我妈妈|我妈|我爸爸|我爸|家人|妈妈|爸爸|朋友|孩子|她|他|我", text))
    if len(actors) > 1 or re.search(r"科普|如果|假如|假设|什么是|举例|例如|听说", text):
        return None
    if known_disease_mention_state(text, "哮喘") != "asserted":
        return None
    if re.search(r"(?:现在|目前)(?:症状)?(?:都|全|全部|完全)?(?:已经|已)?(?:好了|恢复正常|没有症状(?:了)?)\s*[。！!？?]?$", text):
        return None
    # A continuing recent interval is not a resolved historical event. This
    # copy is only for this bounded context, never patient text or model input.
    current = re.sub(r"过去[0-9一二两三四五六七八九十]+(?:个)?(?:小时|分钟)(?=一直|持续|仍)", "目前", text)
    breathing = _affirmed(current, ("喘鸣", "胸部发紧", "胸口发紧", "胸闷"))
    rescue = _affirmed(current, ("急救吸入器", "缓解吸入器", "救援吸入器"))
    if not (breathing and rescue and re.search(r"一直|持续|反复|仍|又回来|复发|又出现|不缓解", current)):
        return None
    # Explicit maximum-plan failure is distinct from a count of uses.
    maximum_failure = False
    for clause in re.split(r"[。；;！？\n]", current):
        if _affirmed(clause, (rescue,)) and _affirmed(clause, ("个人方案最大剂量", "最大救援量", "最大剂量")):
            after = clause.split(rescue, 1)[1]
            maximum_failure = bool(re.search(r"(?:仍|仍然|还是)?(?:没有|没|未)(?:缓解|改善|好转)|无效", after))
            if maximum_failure:
                break
    return {"breathing": breathing, "rescue": rescue, "explicit_maximum_failure": maximum_failure}
