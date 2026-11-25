"""Pilot IO and current constraints; no changes to frozen implementations."""
from dataclasses import asdict
from fractions import Fraction
import gzip
import json
from pathlib import Path

from kmd_toc.common.config import ROOT
from kmd_toc.common.models import load_problem
from kmd_toc.duty_break_v1.models import activate,RestOptions,load_plan
from kmd_toc.duty_break_v1.validation import require_valid
from kmd_toc.duty_break_v1.local import metrics
from kmd_toc.d_final_selection_v1.ranking import Metrics,metric_record
from kmd_toc.nkr_p2_study import model as legacy
from kmd_toc.d_local_design.pipeline import dump,read,digest,INPUTS,SAVED

CONFIG=ROOT/'configs/nkr_unlimited_20261121_v1/protocol.json'
DEFAULT_OUT=ROOT/'output/nkr_unlimited_20261121_v1'


def gzsave(path,data):
    with gzip.open(path,'wt') as f:json.dump(data,f,allow_nan=False)


def problem(scale):
    raw=read(CONFIG)['rest_options']
    return activate(load_problem(INPUTS/scale),version='duty-break-20261121-v1',
        rest_options=RestOptions(raw['allow_assumed_locations'],raw['allow_post_final_depot_break'],tuple(tuple(x) for x in raw['confirmed_locations'])))


def checked(p,plan):
    report=require_valid(p,plan)
    d,w=metrics(p,plan)
    if abs(float(d)-report['D_km'])>1e-7 or abs(float(w)-report['W_total_loading_min'])>1e-9:
        raise ValueError('INDEPENDENT_DW_DISAGREEMENT')
    return Metrics(d,w),report


def recorded(m):
    return {'D_km':float(m.D),'W_total_min':float(m.W),'D_exact':str(m.D),'W_exact':str(m.W)}


def from_record(r):return Metrics(Fraction(r['D_exact']),Fraction(r['W_exact']))


def load_payload(path):
    # JSON parser is identical for compressed candidate and checkpoint payloads.
    if str(path).endswith('.gz'):
        with gzip.open(path,'rt') as f:raw=json.load(f)
        return payload_plan(raw)
    return load_plan(path)


def payload_plan(raw):
    from kmd_toc.common.models import Trip,Visit
    from kmd_toc.duty_break_v1.models import DutyPlan,Break
    data=dict(raw)
    if data.get('schema_version')!='duty-break-plan-v1':raise ValueError('NO_MIXED_PLAN_VERSION')
    trips=[]
    for record in data.pop('trips'):
        t=dict(record);t['visits']=tuple(Visit(**v) for v in t['visits']);trips.append(Trip(**t))
    breaks=tuple(Break(**b) for b in data.pop('breaks'))
    return DutyPlan(**data,trips=tuple(trips),breaks=breaks)


def check_pins(out):
    manifest=read(Path(out)/'MANIFEST.json')
    for name,sha in manifest['pins'].items():
        if digest(ROOT/name)!=sha:raise ValueError('SOURCE_OR_INPUT_CHANGED:'+name)
    return manifest
