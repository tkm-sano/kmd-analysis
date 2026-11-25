"""Explicit opt-in replay/evaluation. No demand generation or quantum execution."""
import argparse
import json
from pathlib import Path
import time
import resource
import traceback
import math
from dataclasses import asdict

from kmd_toc.common.config import digest_file,read_json
from kmd_toc.common.models import load_problem,load_plan as load_legacy_plan
from .models import activate,RestOptions,save_plan,load_plan
from .policy import VERSION,policy_hash,load_policy
from .scheduler import replay
from .validation import validate


def run_case(base,input_path,source_path,output,options,*,action='replay'):
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    source_path=Path(source_path);before=digest_file(source_path);wall=time.perf_counter();cpu=time.process_time()
    p=activate(base,version=VERSION,rest_options=options)
    report={'version':VERSION,'base_input_path':str(Path(input_path).resolve()),'base_problem_hash':base.fingerprint,
            'problem_hash':p.fingerprint,'od_hash':p.od.fingerprint,'policy_sha256':policy_hash(),
            'rest_options':options.payload(),'source_plan_path':str(source_path.resolve()),'source_plan_sha256':before,
            'operation':action,'main_experiment':False,'quantum_calls':0,'demand_generation':False,
            'duty_policy':load_policy(),'derived_vehicles':[asdict(v) for v in p.vehicles],
            'berths_unchanged':[asdict(b) for b in p.berths],
            'code_sha256':{str(f.relative_to(Path(__file__).resolve().parents[3])):digest_file(f)
                           for f in sorted(Path(__file__).parent.glob('*.py'))}}
    try:
        source=load_legacy_plan(source_path) if action=='replay' else load_plan(source_path)
        proposal=replay(p,source,validate=False) if action=='replay' else source
        check=validate(p,proposal);report.update(validation=check,model_feasible=check['model_feasible'])
        report['status']='MODEL_FEASIBLE' if check['model_feasible'] else 'REPLAYED_ASSIGNMENT_INFEASIBLE_NOT_GLOBAL_PROOF'
        report['operational_site_feasibility']=check['stopping_site_feasibility']
        filename='plan.json' if check['model_feasible'] else 'REJECTED_CANDIDATE.json'
        save_plan(proposal,output/filename)
        report['candidate_file']=filename
        report['source_generation_conditions']='preserved_history_not_certified_as_current_B_C_Q_experiment'
        if action=='replay':
            routes=lambda plan:{(t.vehicle_id,t.trip_no):tuple(v.stop_id for v in t.visits) for t in plan.trips}
            report['routes_assignments_and_order_preserved']=routes(source)==routes(proposal)
            report['source_recorded_D_km']=math.fsum(t.distance_m for t in source.trips)/1000
            report['source_recorded_W_total_loading_min']=sum(t.load_start_s-t.ready_s for t in source.trips)/60
            report['delta_D_pinned_replay_km']=check['diagnostic_D_km']-report['source_recorded_D_km']
            report['delta_W_pinned_replay_min']=check['diagnostic_W_total_loading_min']-report['source_recorded_W_total_loading_min']
            if not report['routes_assignments_and_order_preserved'] or abs(report['delta_D_pinned_replay_km'])>1e-7:
                raise RuntimeError('PINNED_REPLAY_ALTERED_ROUTES_OR_DISTANCE')
    except (ValueError,KeyError) as error:
        report.update(status='HOLD_INPUT_OR_ASSIGNMENT_ERROR',error=str(error),model_feasible=False)
    except Exception as error:
        report.update(status='SOFTWARE_FAILURE_HOLD',error=str(error),traceback=traceback.format_exc(),model_feasible=False)
    report.update(wall_s=time.perf_counter()-wall,CPU_s=time.process_time()-cpu,
                  max_process_RSS_MiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,
                  max_RSS_scope='lifetime_process_highwater_not_independent_per_plan_peak',
                  initial_plan_generation_s=None,full_planning_time_s=None,
                  source_plan_unchanged=digest_file(source_path)==before)
    if not report['source_plan_unchanged']:raise RuntimeError('SOURCE_PLAN_CHANGED_DURING_REPLAY')
    with (output/'REPORT.json').open('x') as f:json.dump(report,f,indent=2,ensure_ascii=False,allow_nan=False)
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('replay','evaluate'))
    parser.add_argument('--duty-version',required=True,choices=(VERSION,))
    parser.add_argument('--base-input',required=True);parser.add_argument('--plan',required=True)
    parser.add_argument('--output',required=True)
    parser.add_argument('--allow-unverified-rest-locations',action='store_true')
    parser.add_argument('--confirmed-locations',help='JSON object: existing stop ID -> supplied confirmation evidence')
    args=parser.parse_args();locations=read_json(args.confirmed_locations) if args.confirmed_locations else {}
    options=RestOptions(args.allow_unverified_rest_locations,True,tuple(sorted(locations.items())))
    base=load_problem(args.base_input)
    report=run_case(base,args.base_input,args.plan,args.output,options,action=args.action)
    print(json.dumps({k:report[k] for k in ('status','model_feasible','operational_site_feasibility') if k in report},indent=2))
    return 0 if report['model_feasible'] else 2


if __name__=='__main__':raise SystemExit(main())
