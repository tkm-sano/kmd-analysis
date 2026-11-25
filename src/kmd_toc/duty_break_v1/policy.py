"""User-approved research conditions; separate from all old freeze files."""
from pathlib import Path
import hashlib
from kmd_toc.common.config import ROOT, read_json

VERSION = 'duty-break-20261121-v1'
CONFIG = ROOT/'configs/toc_delivery/duty_break_20261121_v1.json'
CONFIG_SHA256 = '4e6384dff71158184bb9661038c4bd4371c25905b22c97a61411c8ea1a2fe122'


def load_policy():
    if hashlib.sha256(CONFIG.read_bytes()).hexdigest()!=CONFIG_SHA256:
        raise ValueError('DUTY_CONDITIONS_REQUIRE_NEW_VERSION_HASH_CHANGED')
    c = read_json(CONFIG)
    expected = {'shift_start_s':28800, 'shift_end_s':68400, 'duty_span_s':39600,
                'nonbreak_window_s':36000, 'vehicle_return_deadline_s':68400,
                'berth_opening_s':28800, 'berth_closing_s':72000,
                'break_duration_s':3600, 'break_count_per_driver':1,
                'break_start_earliest_s':43200, 'break_start_latest_s':46800,
                'break_end_latest_s':50400, 'pre_shift_tasks_s':0, 'post_return_tasks_s':0,
                'loading_s':1800, 'service_s':120, 'preparation_s':0, 'max_trips':2,
                'drivers_per_vehicle':1}
    if c.get('version') != VERSION or any(type(c.get(k)) is not int or c[k] != v for k,v in expected.items()):
        raise ValueError('DUTY_CONDITIONS_REQUIRE_NEW_VERSION')
    if c.get('driver_changes') is not False or c.get('main_experiment_authorized') is not False:
        raise ValueError('DUTY_POLICY_SCOPE_CHANGED')
    return c


def policy_hash():
    load_policy()
    return hashlib.sha256(CONFIG.read_bytes()).hexdigest()
