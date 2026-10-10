"""Registered demographic-only descriptions do not establish medical symptoms."""
import re


def demographic_only_description(text):
    if not isinstance(text, str) or not text.strip():
        return False
    rest = re.sub(r'(?:今年)?\d{1,3}\s*(?:岁|个?月|天)(?:大)?', '', text)
    tokens = ('新生儿', '成年人', '年龄', '性别', '儿童', '小儿', '小孩', '宝宝', '婴儿',
              '成人', '老人', '男性', '女性', '男孩', '女孩', '患者', '今年', '我', '是', '男', '女')
    for token in tokens:
        rest = rest.replace(token, '')
    rest = re.sub(r'[\s，,。；;：:、]', '', rest)
    return not rest
