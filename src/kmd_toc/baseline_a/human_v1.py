"""Human assignment/order -> physical completion only. Never calls NN or search.

A_human_v1 is a distinct workflow from frozen A_rule_v1. Scripted fixtures do
not measure a person's planning time. Timing observations need explicit stages.
"""
from collections import Counter
import csv
from dataclasses import replace
import io
import math

VERSION = 'A_human_v1-20261116'
CONTRACT = 'human-planned-A-human-v1-20261116'
IMPLEMENTATION = 'human_assignment_order_capacity_split_FCFS_v1'
HUMAN_STAGES = {'HUMAN_PLANNING', 'HUMAN_REVIEW'}
STAGES = HUMAN_STAGES | {'PROGRAM', 'PAUSED', 'FINISHED', 'ABANDONED'}


def manual_groups(problem, csv_text):
    reader = csv.DictReader(io.StringIO(csv_text))
    if reader.fieldnames != ['vehicle_id', 'sequence', 'stop_id']:
        raise ValueError('MANUAL_CSV_HEADER')
    vehicles = {v.vehicle_id:i for i,v in enumerate(problem.vehicles)}
    nodes = {s:i for i,s in enumerate(problem.od.ids) if i}
    rows = [[] for _ in problem.vehicles]
    seen = []
    for row in reader:
        if (None in row or None in row.values() or row['vehicle_id'] not in vehicles or
                row['stop_id'] not in nodes or not row['sequence'].isascii() or
                not row['sequence'].isdigit() or int(row['sequence'])<1):
            raise ValueError('MANUAL_ROW')
        rows[vehicles[row['vehicle_id']]].append((int(row['sequence']),nodes[row['stop_id']]))
        seen.append(row['stop_id'])
    if Counter(seen) != Counter(s.stop_id for s in problem.stops):
        raise ValueError('MANUAL_COVERAGE')
    groups=[]
    for row in rows:
        row.sort()
        if [s for s,_ in row] != list(range(1,len(row)+1)):
            raise ValueError('MANUAL_SEQUENCE')
        if len(row)>120:
            raise ValueError('MANUAL_CAPACITY_MAX_TRIPS')
        groups.append(tuple(n for _,n in row))
    return tuple(groups)


def complete_manual(problem, csv_text):
    # Reuse only frozen physical compilation/FCFS; explicitly bypass order search.
    from .rule_v1 import compile_group, schedule, materialize
    from .program_validation import audit_plan
    from kmd_toc.common.validation import validate_plan
    groups=manual_groups(problem,csv_text)
    def retain_human_order(nodes, problem, *, context=None):
        return nodes
    routes=tuple(compile_group(problem,g,orderer=retain_human_order) for g in groups)
    state=schedule(problem,routes)
    plan=materialize(problem,routes,state,{
        'method_version':VERSION,'implementation_id':IMPLEMENTATION,'contract_id':CONTRACT,
        'assignment_and_order':'externally_human_authored_requires_attestation',
        'automated_NN':False,'automated_boundary_improvement':False,
        'completion':'successive_capacity_chunks_then_ready_FCFS',
    })
    plan=replace(plan,plan_id=problem.experiment.scenario_id+'-'+VERSION)
    common, independent=validate_plan(problem,plan),audit_plan(problem,plan)
    agreement=(common.feasible and independent['feasible'] and
               abs(common.D_km-float(independent['D_km']))<=1e-7 and
               abs(common.W_min-float(independent['W_min']))<=1e-7)
    return plan,{'validated':bool(agreement),'common':common.as_dict(),'independent':independent,
                 'human_order_preserved':True,'state':state}


def timing(events, *, validated, human_attested, synthetic=False):
    """Elapsed stage accounting; no fabricated per-stop or external coefficients."""
    if len(events)<2 or events[-1]['phase'] not in {'FINISHED','ABANDONED'}:
        raise ValueError('INCOMPLETE_TIMELINE')
    totals={'human':0.,'program':0.,'other':0.}
    for a,b in zip(events,events[1:]):
        if a['phase'] not in STAGES or b['phase'] not in STAGES:
            raise ValueError('TIMELINE_PHASE')
        values=(a['at_s'],b['at_s'])
        if any(type(x) not in (int,float) or not math.isfinite(x) or x<0 for x in values) or b['at_s']<a['at_s']:
            raise ValueError('TIMELINE_CLOCK')
        if a['phase'] in {'FINISHED','ABANDONED'}:
            raise ValueError('TIMELINE_AFTER_END')
        key='human' if a['phase'] in HUMAN_STAGES else 'program' if a['phase']=='PROGRAM' else 'other'
        totals[key]+=b['at_s']-a['at_s']
    elapsed=events[-1]['at_s']-events[0]['at_s']
    reason=('ABANDONED' if events[-1]['phase']=='ABANDONED' else
            'INVALID_PLAN' if not validated else
            'HUMAN_AUTHORSHIP_NOT_ATTESTED' if not human_attested else
            'MISSING_HUMAN_PLANNING_STAGE' if not any(a['phase']=='HUMAN_PLANNING' and b['at_s']>a['at_s'] for a,b in zip(events,events[1:])) else
            'MISSING_HUMAN_REVIEW_STAGE' if not any(a['phase']=='HUMAN_REVIEW' and b['at_s']>a['at_s'] for a,b in zip(events,events[1:])) else
            'SYNTHETIC_AUTOMATION_NOT_HUMAN_MEASUREMENT' if synthetic else 'MEASURED_DECLARED_WORKFLOW')
    eligible=reason=='MEASURED_DECLARED_WORKFLOW'
    return {'T':elapsed if eligible else None,'T_operational':elapsed if eligible else None,
            'T_human':totals['human'] if eligible else None,
            'T_program':totals['program'],'T_other':totals['other'],
            'T_attempt':elapsed,'T_reason':reason,'operational_adoptable':eligible,
            'diagnostic_stage_seconds':totals,
            'T_kind':'human_planning_tool_review_elapsed_v1','J':None,
            'J_reason':'HUMAN_INCLUSIVE_REFERENCE_NOT_ESTABLISHED'}
