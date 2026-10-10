"""Bounded eye/joint safety assessment from NHS public symptom guidance."""
import re
from .contextual_urgency import _affirmed, _fragments


def _local_reports(text, location_pattern):
    # A recent continuing interval is distinct from a resolved historical
    # episode. Normalize only this domain copy, never the serving input.
    for fragment in _fragments(text):
        if re.search(r'(?:现在|目前).*(?:好了|恢复正常|没有症状)', fragment) or re.search(r'(?:已经|已)(?:好了|恢复正常|痊愈)\s*$', fragment):
            continue
        current = re.sub(r'过去[0-9一二两三四五六七八九十]+(?:个)?(?:天|小时)(?=(?:左|右)?(?:眼|膝))', '目前', fragment)
        for location in re.finditer(location_pattern, current):
            if not _affirmed(current[:location.end()], [location.group()]):
                continue
            tail = current[location.end():]
            # Another explicitly named part cannot supply this part's cue.
            tail = re.split(r'(?:左|右)?(?:眼睛|眼|膝关节|膝盖|膝)|头部|胸部|腹部|腰部|手臂|小腿|我|她|他', tail)[0]
            yield current[:location.end()] + tail, location.end()


def eye_emergency_assessment(text):
    for local, start in _local_reports(text, r'(?:左|右)?(?:眼睛|眼)'):
        red = _affirmed(local, ('发红', '红'), start_at=start)
        warning = _affirmed(local, ('怕光', '畏光', '看光会疼', '视力模糊', '视力变差', '视力下降', '视物模糊'), start_at=start)
        if red and warning:
            return {'name': '当前红眼合并怕光或视力变化', 'department': '急诊医学科',
                    'reason': '当前红眼合并怕光或视力变化，需要优先急诊专业评估，不能等待普通预约；本系统不诊断眼病。'}
    return None


def joint_urgent_assessment(text):
    for local, start in _local_reports(text, r'(?:左|右)?(?:膝关节|膝盖|膝)'):
        swelling = _affirmed(local, ('肿胀', '肿'), start_at=start)
        pain = _affirmed(local, ('疼痛', '疼', '痛'), start_at=start)
        warning = _affirmed(local, ('摸起来发热', '局部发热', '摸起来发烫', '不能弯曲', '无法弯曲', '不能活动', '无法活动'), start_at=start)
        if swelling and pain and warning:
            return {'name': '当前关节肿痛合并局部发热或活动受限', 'department': '急诊医学科',
                    'reason': '当前关节肿痛合并局部发热或活动受限，需要尽快到医院线下评估，不能等待普通预约；本系统不判断是否为感染。'}
    return None
