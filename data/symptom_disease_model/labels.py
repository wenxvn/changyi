import json
from pathlib import Path


DEFAULT_DISEASE_ZH_PATH = Path(__file__).with_name("disease_name_zh.json")


def load_disease_name_map(path=DEFAULT_DISEASE_ZH_PATH):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def translate_disease_name(name, name_map):
    return name_map.get(name, name)
