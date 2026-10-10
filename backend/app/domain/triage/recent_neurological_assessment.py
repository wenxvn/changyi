"""Recent whole unilateral arm reports need assessment even after recovery.

NHS TIA public guidance; this never diagnoses stroke or TIA.
"""
import re
from ..medical_input import contains_positive
from .contextual_urgency import _fragments, _affirmed


def _reported_after(text, terms, start):
    reports = []
    for term in terms:
        for match in re.compile(re.escape(term)).finditer(text, start):
            prefix = text[:match.start()].replace(term, ' ' * len(term))
            if contains_positive(prefix[-16:] + term, [term]):
                reports.append(match)
    return max(reports, key=lambda match: match.start()) if reports else None


def recent_arm_assessment(text):
    for fragment in _fragments(text):
        for location in re.finditer(r'(?:整个|整条)(?:左|右)(?:手臂|胳膊|臂)', fragment):
            prefix = fragment[:location.start()]
            if not re.search(r'现在|目前|正在|今天|刚刚|刚才|昨天|本周|这周|最近几天|近几天', prefix):
                continue
            if not _affirmed(fragment[:location.end()], [location.group()]):
                continue
            tail = fragment[location.end():]
            tail = re.split(r'(?:左|右)?(?:手指|手臂|胳膊)|头部|胸部|腿部|我|她|他', tail)[0]
            local = fragment[:location.end()] + tail
            if re.search(r'以前|曾经|去年|既往|是否|不确定|有没有|可能|会不会', tail):
                continue
            numbness = _reported_after(local, ['麻木'], location.end())
            if not numbness:
                continue
            recovered = _reported_after(local, ['完全恢复', '恢复正常', '已经好了'], numbness.end())
            if recovered:
                return {'level': 'urgent', 'name': '近期短暂整侧手臂麻木恢复后仍需评估', 'department': '急诊医学科',
                        'reason': '近期报告整侧手臂短暂麻木，即使已恢复或没有其他神经症状，也需要尽快线下专业评估，不能等待普通预约；本系统不判断是否为脑血管疾病。'}
            if re.search(r'现在|目前|正在|今天|刚刚', local[:numbness.start()]) and _affirmed(local, ['突然'], start_at=location.end()):
                return {'level': 'emergency', 'name': '当前突然整侧手臂麻木需急诊评估', 'department': '急诊医学科',
                        'reason': '当前报告突然整侧手臂麻木，需要优先急诊专业评估，不因没有其他神经症状排除危险；本系统不诊断病因。'}
    return None
