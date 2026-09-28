"""Authorized classical execution only. Never overwrites frozen inputs/results.

PYTHONPATH=05_src/traffic_simulation .conda/bin/python -m
r24_minimal_evrp.run_charging_validation --output <new gate directory>
"""
import argparse,csv,hashlib,json,sys,time,subprocess,platform,traceback
from pathlib import Path
from fractions import Fraction as F
from .charging import context,exact_reference,fleet_replay,json_number
from .charging_independent import validate,validate_exhaustive

R=Path(__file__).resolve().parents[3];BASE=R/'reproducibility/outputs/traffic_simulation'
P2=BASE/'r24_minimal_evrp_charging_authority/20260926_v2';P3=P2.parent/'20260926_v3'
DESIGN=BASE/'r24_minimal_evrp_design_authority/20260926_v1'
INSTANCE=BASE/'r24_vrptw_benchmark_spec/20260921_v1/instances/R24-RND-N002-R01-RHO050-TW-WIDE.json'
LEDGER=BASE/'r24_vrptw_uniform_vs_structured_comparison/20260922_v1/COMPARISON_CIRCUIT_LEDGER.json'
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def load():
    instance=read(INSTANCE);od=read(P2/'DIRECTED_CHARGER_OD.json');pre=read(P2/'CHARGING_VALIDATION_PRECHECK.json');design=read(DESIGN/'MINIMAL_EVRP_AUTHORITY.json')
    return instance,od,pre,design,context(instance,od,pre,design)

def verify_protected(out):
    before=read(out/'PROTECTED_INPUTS_BEFORE.json')
    for p,h in before.items():
        if sha(R/p)!=h:raise RuntimeError('STOP: protected hash drift '+p)
    totals=read(LEDGER)['totals']
    if (totals['scientific_consumed'],totals['shots_consumed'],totals['reserved'])!=(541,1107968,0):raise RuntimeError('STOP: ledger')
    return before,totals

def guard(event,args):
    if event=='import' and any(args[0]==p or args[0].startswith(p+'.') for p in ['qiskit','qiskit_aer']):raise RuntimeError('STOP: quantum import prohibited')

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);out=parser.parse_args().output.resolve()
    if (out/'EXECUTION_STARTED.json').exists():raise RuntimeError('Refuse repeat/overwrite execution')
    before,totals=verify_protected(out);sys.addaudithook(guard)
    def write(n,x): (out/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
    instance,od,pre,design,ctx=load()
    control=dict(P_required_min_kw=json_number(ctx['threshold']),rule='ceil_to_1kW(1.10 * P_required_min)',P_validation_kw=10,
        source='Current explicit user instruction; model-derived threshold',classification='CONTROLLED_VALIDATION_CONDITION',
        real_world_charging_performance_authority='UNRESOLVED_DEFERRED',S0_eligible=False,
        B_initial_kwh=json_number(ctx['initial']),initial_SOC_pct=json_number(100*ctx['initial']/20),B_max_kwh=20,B_min_kwh=2,r_kwh_per_km='.127',
        margin_kw=json_number(ctx['power']-ctx['threshold']),margin_ratio=json_number(ctx['power']/ctx['threshold']),
        q_design_kwh=pre['q_required_kwh'],t_design_s=json_number(360*F(pre['q_required_kwh'])),
        remaining_design_time_margin_s=json_number(F(pre['available_charge_time_s'])-360*F(pre['q_required_kwh'])),
        eta=1,queue_s=0,setup_s=0,topology='one real physical charger; at most n+1 occurrences per used vehicle; all sequence gaps considered',
        conditions='all used vehicles same controlled initial energy; authorized access and available connector; no station occupancy coupling; two connectors available assumption if both vehicles used',
        numerical_policy=dict(exact_energy_time_tolerance=0,MILP_energy_residual_kwh='1e-9',MILP_time_residual_s='1e-7',primary_fix_s='1e-7'))
    write('CONTROLLED_VALIDATION_AUTHORITY.json',control)
    write('EXECUTION_STARTED.json',dict(classical_only=True,python=sys.executable,python_version=platform.python_version(),permission='Current user task explicitly authorizes Exact+MILP; historical real-world authority remains unresolved',quantum_delta=0))
    started=time.perf_counter();executions=[]
    try:
        refs={}
        for name,enabled in [('disabled',False),('enabled',True)]:
            t=time.perf_counter();refs[name]=exact_reference(ctx,enabled)
            executions.append(dict(type='exact_enumeration',case=name,wall_time_s=time.perf_counter()-t,candidates=refs[name]['enumerated_count']))
        write('CHARGING_EXACT_REFERENCE.json',refs)
        if refs['disabled']['status']!='PROVEN_INFEASIBLE' or refs['enabled']['status']!='PROVEN_OPTIMAL':raise RuntimeError('STOP: exact expected feasibility mismatch')
        checks={name:validate_exhaustive(instance,od,pre,ref) for name,ref in refs.items()}
        write('CHARGING_INDEPENDENT_VALIDATION.json',dict(exact=checks))
        if any(x['status']!='PASS' for x in checks.values()):raise RuntimeError('STOP: independent exact audit mismatch')
        from .charging_milp import solve
        milps={}
        for name,enabled in [('disabled',False),('enabled',True)]:
            milps[name]=solve(ctx,enabled)
            executions.extend(dict(type='MILP',case=name,**stage) for stage in milps[name]['stages'])
            write('CHARGING_MILP_RESULT.json',milps)
        if milps['disabled']['status']!='PROVEN_INFEASIBLE' or milps['enabled']['status']!='PROVEN_OPTIMAL':raise RuntimeError('STOP: exact/MILP feasibility mismatch')
        m=milps['enabled'];mcheck=validate(instance,od,pre,m['plans'],m['replay'],True,floating=True)
        checks['milp_enabled']=mcheck
        write('CHARGING_INDEPENDENT_VALIDATION.json',checks)
        if mcheck['status']!='PASS' or not mcheck['independent_feasible']:raise RuntimeError('STOP: MILP independent validation mismatch')
        opt=refs['enabled']['candidates'][refs['enabled']['optimal_indices'][0]]
        exact=opt['result'];cross={}
        cross['primary_agrees']=abs(F(str(m['replay']['primary_travel_s']))-F(str(exact['primary_travel_s'])))<=F('1e-7')
        cross['secondary_agrees']=abs(F(str(m['replay']['secondary_charging_s']))-F(str(exact['secondary_charging_s'])))<=F('1e-7')
        norm=lambda result:sorted(tuple(r['nodes']) for r in result['routes'] if r['used'])
        cross['route_agrees_modulo_identical_vehicle_labels']=norm(exact)==norm(m['replay'])
        cross['disabled_infeasible_agreement']=True;cross['independent_checks_pass']=True
        write('CROSS_VALIDATION.json',cross)
        if not all(cross.values()):raise RuntimeError('STOP: exact/MILP optimum mismatch')
        disabled_plans=[dict(vehicle_id=p['vehicle_id'],nodes=p['nodes'],charges={k:0 for k in p['charges']}) for p in opt['plans']]
        diagnostic=fleet_replay(ctx,disabled_plans)
        write('CHARGING_DISABLED_RESULT.json',dict(status='PROVEN_INFEASIBLE',exact_reference='CHARGING_EXACT_REFERENCE.json',MILP_reference='CHARGING_MILP_RESULT.json',same_optimal_charging_route_diagnostic=diagnostic,first_violation=[r['first_reserve_violation'] for r in diagnostic['routes'] if r['used']],TW_separate='See temporal_feasible per route; energy failure not temporal failure'))
        write('CHARGING_ENABLED_RESULT.json',dict(status='PROVEN_OPTIMAL',plans=opt['plans'],replay=exact,independent_validation=validate(instance,od,pre,opt['plans'],exact,True),vehicle_label_ties=refs['enabled']['optimal_indices']))
        for n,rows in [('CHARGING_BATTERY_TRAJECTORY.csv',[e for r in exact['routes'] for e in r['events']]),('CHARGING_TEMPORAL_REPLAY.csv',[e for r in exact['routes'] for e in r['events']]),('CHARGING_ARCS.csv',[e for r in exact['routes'] for e in r['arcs']])]:
            with (out/n).open('w',newline='') as f:
                w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
        write('CLASSICAL_EXECUTION_RECORD.json',dict(executions=executions,total_wall_time_s=time.perf_counter()-started,quantum_circuits=0,quantum_shots=0,Aer_calls=0,QAOA_runs=0,new_quantum_reservations=0,counts_separate_from_quantum_ledger=True))
        verify_protected(out)
        print(json.dumps(dict(status='CROSS_VALIDATION_PASS_PENDING_TESTS_AND_FREEZE',exact_objective=refs['enabled']['objective'],exact_counts={k:v['enumerated_count'] for k,v in refs.items()},feasible_counts={k:v['feasible_count'] for k,v in refs.items()},milp_stages=len(executions)-2,output=str(out)),indent=2))
    except Exception as error:
        write('FAILURE.json',dict(status='MINIMAL_EVRP_CLASSICAL_MODEL_NOT_FROZEN',reason=str(error),traceback=traceback.format_exc(),executions=executions,parameters_unchanged=True,next_task='Investigate documented implementation/validation mismatch; no parameter tuning'))
        raise
if __name__=='__main__':main()
