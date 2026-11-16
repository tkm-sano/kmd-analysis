"""Uncalibrated workflow sensitivity, separate from measured program runtime."""
import math
from .config import load_settings


def workforce(rule, vehicles):
    if type(vehicles) is not int or vehicles<1: raise ValueError('HUMAN_VEHICLES')
    return {'one':1,'half_vehicles_ceil':math.ceil(vehicles/2),'all_vehicles':vehicles}[rule]


def estimate_workflow(counts, profile, workers, *, measured_io_validation_s=None):
    if (not counts or any(type(n) is not int or n<0 for n in counts) or
            type(workers) is not int or workers<1): raise ValueError('HUMAN_WORKLOAD')
    if measured_io_validation_s is not None and (not math.isfinite(measured_io_validation_s) or measured_io_validation_s<0):
        raise ValueError('HUMAN_OVERHEAD')
    q = load_settings()['human_time']['profiles'][profile]
    per_stop = sum(q[k] for k in ['lookup_s_per_stop','ordering_s_per_stop','review_s_per_stop'])
    jobs = [(q['vehicle_setup_s']+per_stop*n,v) for v,n in enumerate(counts) if n]
    loads = [0]*workers; assignments = []
    for job,v in sorted(jobs,key=lambda pair:(-pair[0],pair[1])):
        w = min(range(workers),key=lambda i:(loads[i],i)); loads[w]+=job
        assignments.append({'vehicle_index':v,'worker_index':w,'job_s':job})
    serial = q['setup_s']+q['assignment_s_per_stop']*sum(counts)+q['coordination_s_per_used_vehicle']*len(jobs)
    workflow = serial+max(loads)
    return {'profile':profile,'workers':workers,'N':sum(counts),'used_vehicles':len(jobs),
            'workflow_elapsed_s':workflow,'person_seconds':serial+sum(j for j,v in jobs),
            'serial_s':serial,'parallel_makespan_s':max(loads),'worker_loads_s':loads,
            'assignments':assignments,'measured_io_validation_s':measured_io_validation_s,
            'T_human_estimate_s':workflow+measured_io_validation_s if measured_io_validation_s is not None else None,
            'kind':'explicit_research_assumption_sensitivity','human_measured':False,'Sagawa_actual':False}


def human_time_sensitivity(counts, *, measured_io_validation_s=None):
    cfg=load_settings()['human_time']; result=[]
    for name in cfg['profiles']:
        for rule in cfg['staff_rules']:
            r=estimate_workflow(counts,name,workforce(rule,len(counts)),measured_io_validation_s=measured_io_validation_s)
            r['staff_rule']=rule; result.append(r)
    return result
