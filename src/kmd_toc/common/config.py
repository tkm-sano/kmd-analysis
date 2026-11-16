"""Pinned adopted conditions; new values require a new version and review."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = ROOT / 'configs/toc_delivery/common_conditions_v1_1.json'
# Approved v1.1 adoption; protects all nested policy values.
CONFIG_SHA256 = 'bbb15417a4eee5072f8118056c90ab422d792b4cedc35a6a06bf6bc0497fe8d2'


def digest_file(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                    separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def read_json(path):
    """Reject duplicate fields and non-JSON NaN/Infinity, including nested ones."""
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('DUPLICATE_JSON_FIELD: ' + key)
            result[key] = value
        return result
    def constant(value):
        raise ValueError('NONFINITE_JSON_NUMBER: ' + value)
    return json.loads(Path(path).read_text(), object_pairs_hook=pairs, parse_constant=constant)


def load_conditions(path=CONFIG_PATH):
    content = Path(path).read_bytes()
    if hashlib.sha256(content).hexdigest() != CONFIG_SHA256:
        raise ValueError('CONDITIONS_HASH_MISMATCH: use a new adopted version')
    return json.loads(content)


def ready_s(v, count, conditions=None):
    c = load_conditions() if conditions is None else conditions
    if type(v) is not int or type(count) is not int or not 0 <= v < count:
        raise ValueError('INVALID_VEHICLE_INDEX')
    return c['operations']['opening_s'] + (3600 * (2 * v + 1)) // (2 * count)


def conditions_table(conditions=None):
    """Exact generated region in COMMON_CONDITIONS_V1.md, checked in tests."""
    c = load_conditions() if conditions is None else conditions
    rows = ['|設定キー|採択値|', '|---|---|']
    for section in ('scope', 'units', 'operations', 'scenarios', 'timing_policy',
                    'road_policy', 'comparison'):
        for key, value in c[section].items():
            rows.append(f'|{section}.{key}|{json.dumps(value, ensure_ascii=False, sort_keys=True)}|')
    rows.append(f'|first_ready_rule|{c["first_ready_rule"]}|')
    rows.append(f'|conditions_version|{c["conditions_version"]}|')
    return '\n'.join(rows)
