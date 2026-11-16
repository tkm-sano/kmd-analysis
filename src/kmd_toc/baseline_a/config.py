"""Preregistered rule and workflow settings; reject silent parameter drift."""
from pathlib import Path
import hashlib
from kmd_toc.common.config import read_json, load_conditions, CONFIG_SHA256

ROOT = Path(__file__).resolve().parents[3]
CONFIG = ROOT / 'configs/toc_delivery/a_rule_baseline_v1.json'
SHA256 = '24060d8be817cf8e09c096d1e1717d35c0e3e666870b34bfc8c2f70995d27bf1'


def load_settings(path=CONFIG):
    path = Path(path)
    if hashlib.sha256(path.read_bytes()).hexdigest() != SHA256:
        raise ValueError('A_RULE_SETTINGS_HASH')
    c = read_json(path)
    if (c['common_conditions_sha256'] != CONFIG_SHA256 or
            c['common_conditions_version'] != load_conditions()['conditions_version']):
        raise ValueError('A_COMMON_CONDITIONS_VERSION')
    return c


def settings_block():
    import json
    return '```json\n' + json.dumps(load_settings(), ensure_ascii=False, indent=2) + '\n```'
