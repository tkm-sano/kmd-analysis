"""One fresh-process method execution with common measured load/validate scope."""
from collections import Counter
from pathlib import Path
import json
import resource
import time
import numpy as np
from kmd_toc.common.models import load_problem,load_plan
from kmd_toc.common.runtime import run_measured,environment
from kmd_toc.baseline_a.independent import recompute
from kmd_toc.baseline_a.human_time import human_time_sensitivity


def json_default(value):
    if isinstance(value,np.generic):return value.item()
    if isinstance(value,np.ndarray):return value.tolist()
    raise TypeError(type(value).__name__)


def execute(input_dir,method,output,primary='D',other_limit=None,offset=0):
    out=Path(output);out.mkdir(parents=True,exist_ok=False);captured={}
    def load():
        p=load_problem(input_dir);captured['problem']=p;return p
    def build(p,mark):
        if method in ['A1','A2','A3']:
            from kmd_toc.baseline_a.construction import create_plan
            return create_plan(p,method,offset,mark)
        if method in ['B','C']:
            from .classical import create_classical
            return create_classical(p,method,primary,other_limit,mark)
        if method=='D':
            from .hybrid import create_hybrid
            return create_hybrid(p,primary,other_limit,mark)
        raise ValueError('METHOD_ID')
    result=run_measured(load,build);result['T_program_s']=result.pop('T_s')
    result.update(method=method,primary=primary,other_limit=other_limit,angle_offset_deg=offset,
                  max_rss_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,environment=environment())
    result['T_semantics']='input read start through final common independent validation; program wall seconds; NOT human time'
    if result['plan'] is not None:
        path=out/'plan.json';path.write_text(json.dumps(result['plan'],ensure_ascii=False,indent=2,default=json_default)+'\n');plan=load_plan(path)
        if result['status']=='FEASIBLE':
            p=captured['problem'];second=recompute(p,plan)
            result['second_validation']=second
            if not second['feasible'] or abs(float(second['D_km'])-result['D_km'])>1e-7 or abs(float(second['W_min'])-result['W_min'])>1e-7:
                result.update(status='AUDIT_FAILURE',D_km=None,W_min=None,T_program_s=None)
            result['input_hash']=p.fingerprint;result['OD_hash']=p.od.fingerprint;result['scenario_id']=p.experiment.scenario_id
            if method.startswith('A'):
                counts=Counter()
                for t in plan.trips:counts[t.vehicle_id]+=len(t.visits)
                e={e['name']:e['elapsed_s'] for e in result['timing_events']};overhead=e['input_load_end']+e['independent_validation_end']-e['independent_validation_start']
                result['human_time_sensitivity']=human_time_sensitivity([counts[v.vehicle_id] for v in p.vehicles],measured_io_validation_s=overhead)
    (out/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False,default=json_default)+'\n')
    return result
