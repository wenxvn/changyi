"""Bounded reported blood-pressure assessment; no diagnosis or treatment.

Adult severe-reading assessment references AHA public guidance and NICE NG136.
"""
import re
from .contextual_urgency import _affirmed

TIME = re.compile(r'今天|现在|目前|刚刚|昨天|以前|曾经|去年|上周|既往')
CURRENT = {'今天', '现在', '目前', '刚刚'}
READING = re.compile(r'血压(?:读数)?\s*(?:为|是|测得|量到|发现|[:：])?\s*(\d{2,3})\s*/\s*(\d{2,3})\s*(mmHg(?![A-Za-z])|毫米汞柱)?', re.I)
DANGER = ('胸痛', '呼吸困难', '气短', '背痛', '麻木', '无力', '视力变化', '视力模糊', '说话困难', '意识混乱')


def _current(prefix):
    times = list(TIME.finditer(prefix))
    return bool(times and times[-1].group() in CURRENT)


def _current_danger(text):
    for term in DANGER:
        for match in re.finditer(term, text):
            if not _current(text[:match.start()]):
                continue
            suffix = re.split(r'[，,。；;！？\n]', text[match.end():])[0]
            if re.match(r'(?:已经|已)?(?:恢复正常|好了|消失)', suffix):
                continue
            prefix = text[:match.start()][-32:].replace(term, ' ' * len(term))
            if _affirmed(prefix + term + suffix, [term], start_at=len(prefix)):
                return term
    return None


def blood_pressure_assessment(text):
    text = text.translate(str.maketrans('０１２３４５６７８９／', '0123456789/'))
    reports = []
    for fragment_match in re.finditer(r'[^。；;！？\n]+', text):
        fragment = fragment_match.group()
        if re.search(r'科普|如果|假如|假设|什么是|举例|例如|听说', fragment):
            continue
        # The fragment may omit an earlier age/current sentence; temporal
        # context belongs to the original occurrence, not another report.
        offset = fragment_match.start()
        for anchor in re.finditer('血压', fragment):
            start = offset + anchor.start()
            if not _current(text[:start]):
                continue
            tail = fragment[anchor.start():]
            reading = READING.match(tail)
            high = re.match(r'血压(?:读数)?(?:为|是|测得|量到|发现|[:：])?\s*(?:很高|非常高|特别高|过高|异常高|明显升高)', tail)
            partial = re.match(r'血压(?:读数)?(?:为|是|测得|量到|发现|[:：])?\s*\d', tail)
            if re.search(r'不确定|是否|是不是|有没有|可能', fragment[:anchor.start()][-16:]):
                if reading or high or partial:
                    reports.append(None)
                continue
            if not _affirmed(fragment[:anchor.end()], ['血压']):
                continue
            if reading:
                reports.append((int(reading[1]), int(reading[2]), 'mmhg' if reading[3] else None))
            elif high or partial:
                reports.append(None)
    if not reports:
        return None
    pending = {'level': 'pending', 'name': '当前血压报告需确认', 'department': None,
               'reason': '当前血压报告的信息或适用范围尚需确认，请补充实际完整读数、单位、测量时间和年龄，并及时专业复核；不能按没有危险信号安排普通预约。'}
    if None in reports or len(set(reports)) > 1:
        return pending
    systolic, diastolic, unit = reports[0]
    if not unit or systolic <= diastolic:
        return pending
    if systolic < 180 and diastolic < 120:
        return None
    actors = set(re.findall(r'我妈妈|我妈|我爸爸|我爸|家人|妈妈|爸爸|朋友|孩子|她|他|我', text))
    ages = re.findall(r'(\d{1,3})岁', text)
    adult = len(ages) == 1 and 18 <= int(ages[0]) <= 120
    if len(actors) > 1 or not adult or _affirmed(text, ['怀孕', '妊娠', '孕妇']):
        return pending
    danger = _current_danger(text)
    if danger:
        return {'level': 'emergency', 'name': '当前严重升高血压读数合并危险表现', 'department': '急诊医学科',
                'reason': '当前报告严重升高的血压读数，并有当前危险表现，需要优先急诊专业评估；本系统不诊断高血压危象或提供降压用药指令。'}
    return {'level': 'urgent', 'name': '当前严重升高血压读数需及时评估', 'department': '急诊医学科',
            'reason': '当前报告严重升高的血压读数，即使未报告上述危险表现，也需要尽快专业评估，不能等待普通预约；本系统不诊断或调整降压药。'}
