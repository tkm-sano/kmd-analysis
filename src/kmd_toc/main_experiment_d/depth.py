"""Approved depth only. Other optimizer/n/K/R/T/J settings remain undecided."""
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CONFIG = ROOT / 'configs/p2_freeze_20261120/main_experiment_d.json'
CONFIG_SHA256 = 'd478872fb810b5913cc1765cd6ecebe28080e293ac8a376c67073b35b4245e4d'


def frozen_config():
    raw = CONFIG.read_bytes()
    if hashlib.sha256(raw).hexdigest() != CONFIG_SHA256:
        raise ValueError('FROZEN_DEPTH_CONFIG_CHANGED')
    return json.loads(raw)


def check_depth(value):
    if type(value) is not int or value != frozen_config()['qaoa']['depth_p']:
        raise ValueError('MAIN_D_DEPTH_OVERRIDE_FORBIDDEN')


def checked_angles(angles):
    expected = 2 * frozen_config()['qaoa']['depth_p']
    if len(angles) != expected or not all(math.isfinite(float(x)) for x in angles):
        raise ValueError('P2_REQUIRES_FOUR_FINITE_ANGLES')
    return tuple(map(float, angles))
