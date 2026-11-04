"""Read-only independent arithmetic audit; no project modules or scientific runners imported."""
from pathlib import Path
import csv, json, hashlib, collections, math, subprocess
from fractions import Fraction as F

R=Path('/home/takuma/kmd-analysis')
U=Path('/home/takuma/kmd-analysis-pre-clean-20261102-112222/untracked')
B=Path('/home/takuma/kmd-analysis-preservation-20261014-173544-a64e484c/backup')
L=B.parent/'relocated'
O=Path(__file__).resolve().parent
inventory={}; schemas={}; checks=[]
def sha(p):
    with p.open('rb') as h:return hashlib.file_digest(h,'sha256').hexdigest()
def use(p):
    p=Path(p)
    if not p.is_file():
        for base in [R,U,B,L]:
            try: rel=p.relative_to(base);break
            except ValueError:pass
        else: raise FileNotFoundError(p)
        candidates=[base/rel for base in [R,U,B,L] if (base/rel).is_file()]
        if not candidates:raise FileNotFoundError(p)
        p=candidates[0]
    if str(p) not in inventory:
        inventory[str(p)]={'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size,'location': 'GIT_TREE' if p.is_relative_to(R) else 'EXTERNAL_UNTRACKED_COPY' if p.is_relative_to(U) else 'PRESERVATION_COPY'}
    return p
def js(p):return json.loads(use(p).read_text())
def rows(p,pk=None):
    p=use(p)
    with p.open() as h:r=csv.DictReader(h);a=list(r); cols=r.fieldnames
    types={};nulls={};ranges={}
    for c in cols:
        vals=[x[c] for x in a if x[c] not in ('','null','NULL','NaN','nan')]
        nulls[c]=len(a)-len(vals)
        try:
            nums=[float(F(x)) for x in vals];types[c]='number/string-encoded';ranges[c]=[min(nums),max(nums)] if nums else None
        except (ValueError,ZeroDivisionError):types[c]='string/structured'
    schemas[str(p)]={'rows':len(a),'columns':cols,'types':types,'nulls':nulls,'numeric_ranges':ranges,'duplicate_full_rows':len(a)-len({tuple(x.values()) for x in a}),'primary_key':pk,'duplicate_keys':len(a)-len({tuple(x[k] for k in pk) for x in a}) if pk else 'NOT_ASSERTED'}
    return a
def check(label,expected,actual,tol=0,where=''):
    ok=abs(float(expected)-float(actual))<=tol if isinstance(expected,(float,int)) and isinstance(actual,(float,int)) else expected==actual
    checks.append(dict(label=label,expected=expected,actual=actual,difference=(float(actual)-float(expected)) if isinstance(expected,(float,int)) and isinstance(actual,(float,int)) else None,tolerance=tol,status='PASS' if ok else 'FAIL',location=where))
def table(name,a):
    if not a:return
    with (O/name).open('w',newline='') as h:w=csv.DictWriter(h,fieldnames=list(a[0]));w.writeheader();w.writerows(a)
def dump(name,a):(O/name).write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n')

start={'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),'status':subprocess.check_output(['git','status','--short'],cwd=R,text=True),'python':subprocess.check_output(['python','--version'],text=True).strip()}
dump('AUDIT_ENVIRONMENT.json',start)
# Register authority, settings, snapshots and prior independent records separately from verification.
dirs=['cpx01_d11_validation_20261017','causal_engineering_audit_20261027/run01','integrated_research_results_20261028/run02','material_ev_stage2_20261026/run02','t09_open_data_model_20261029/run01','t08_t09_conditional_bridge_20261030/run01','unified_no_windows_r0_r8_20261022','r0_r8_main_results_20261023','staged_qaoa_validation_20261102']
for d in dirs:
    p=U/'review_outputs'/d
    for f in p.glob('*'):
        if f.is_file() and f.suffix in ('.md','.json','.py','.log','.txt'):use(f)
    for f in (p/'SOURCE_SNAPSHOT').rglob('*.py'):use(f)
for f in [R/'README.md',R/'docs/QUANTITATIVE_GUIDE.md',R/'configs/CANONICAL_CONFIG_INDEX.csv',R/'reproducibility/release/GITHUB_DISTRIBUTION_MANIFEST.json',R/'01_research_design/methodology/CONTROLLED_MASS_TO_DC_MODEL_FREEZE.json',R/'01_research_design/scenario_evaluation/final_quantitative_study_20261008/FINAL_QUANTITATIVE_RESULT_FREEZE.json',U/'docs/research/CPX01_D10_ADOPTION_DECISION_20261017.md',U/'docs/research/CPX01_D13_RD01_RD10_ADOPTION_DECISIONS_20261017.md',U/'docs/research/CPX01_D13_Q01_Q10_ADOPTION_DECISIONS_20261017.md']:
    use(f)
for f in (R/'src').rglob('*.py'):use(f)
for f in (R/'scripts').glob('*.py'):use(f)
# A: independent decision arithmetic from each row, raw plan readback.
p=U/'review_outputs/cpx01_d11_validation_20261017'
a=rows(p/'operations_2808.csv',['scenario_id','PID']);conditions=rows(p/'conditions_36.csv',['scenario_id'])
check('A decisions',2808,len(a));check('A conditions',36,len(conditions))
bad=[]; raw={}; rawroutes={}
for i,x in enumerate(a,2):
    aq=x['quantum_acquired']=='True';tc=-int(x['L'])+int(x['T_C']);tq=-int(x['L'])+int(x['T_Q']);cut=-int(x['B'])
    # Select earliest event, result before cutoff at equality.
    first=min((tq,0),(cut,1)); qm=aq and first[1]==0
    adopt=tq if qm else max(tc,first[0]);depart=max(0,adopt+int(x['T_dispatch'])+(0 if qm else int(x['T_switch'])))
    if x['adopted_method']!=('QUANTUM' if qm else 'CLASSICAL') or int(x['t_depart'])!=depart:bad.append(i)
    if x['PID'] not in raw:
        q=js(x['quantum_source']);c=js(x['classical_source']);raw[x['PID']]=(q,c)
        rawroutes[x['PID']]={'CLASSICAL':c['customer_order'],'QUANTUM':q.get('best_final_feasible_route',{}).get('route_ids') if q.get('best_final_feasible_route') else None}
    order=rawroutes[x['PID']][x['adopted_method']]
    if json.loads(x['visit_order'])!=order:bad.append(i)
check('A policy/selected raw route mismatch rows',0,len(bad),where='operations_2808.csv data rows '+str(bad[:20]))
check('A raw acquired',64,sum(q['final_feasible_count']>0 for q,c in raw.values()))
logical={(x['PID'],tuple(json.loads(x['visit_order'])),int(x['t_depart'])) for x in a}
saved=rows(p/'logical_candidates.csv',['PID','route_identity','t_depart'])
check('A logical candidate set',True,logical=={(x['PID'],tuple(json.loads(x['visit_order'])),int(x['t_depart'])) for x in saved})
statsA={'physical_problems':len(raw),'acquired':sum(q['final_feasible_count']>0 for q,c in raw.values()),'acquisition_rate':sum(q['final_feasible_count']>0 for q,c in raw.values())/len(raw),'adopted':dict(collections.Counter(x['adopted_method'] for x in a)),'departures':dict(collections.Counter(x['t_depart'] for x in a)),'logical_candidates':len(logical),'logical_departures':dict(collections.Counter(str(x[2]) for x in logical)),'complete_run_signature_count':None,'same_raw_routes':sum(v['CLASSICAL']==v['QUANTUM'] for v in rawroutes.values()),'raw_classical_search_sum_s':sum(c['phases']['search_s'] for q,c in raw.values()),'raw_classical_search_mean_s':sum(c['phases']['search_s'] for q,c in raw.values())/78,'raw_quantum_wall_sum_s':sum(q['wall_s'] for q,c in raw.values()),'raw_quantum_wall_mean_s':sum(q['wall_s'] for q,c in raw.values())/78}
native=rows(U/'review_outputs/causal_engineering_audit_20261027/run01/A_NATIVE_TASK_COMPLETION.csv',['run_id','task_id'])
for i,x in enumerate(native,2):
    complete=max(float(x['native_stop_reached_s']),float(x['ready_s']))+float(x['service_duration_s'])
    check('A candidate completion '+str(i),complete,float(x['model_completion_s']),1e-8,'A_NATIVE_TASK_COMPLETION.csv:'+str(i)+':model_completion_s')
base=rows(U/'review_outputs/causal_engineering_audit_20261027/run01/A_BASELINE_METRICS.csv',['run_id'])
statsA['native_diagnostic']={'runs':len(base),'task_rows':len(native),'technical_status':dict(collections.Counter(x['run_technical_status'] for x in base)),'demand_PE':sum(int(x['q_PE']) for x in native),'on_time_PE':sum(int(x['q_PE']) for x in native if float(x['model_completion_s'])<=float(x['D03_completion_deadline_s'])),'minimum_slack_s':min(float(x['deadline_slack_s']) for x in native)}
dump('A_RECALCULATED.json',statsA)
# B: fixed eight optimized configurations; all other controls retained separately.
stage=U/'review_outputs/staged_qaoa_validation_20261102'
manifest=js(stage/'mirror_family/MANIFEST.json')
manifest={x['run_id']:x for x in manifest}
check('B inputs',460,len(manifest))
npz={}; npz_bad=[]
import numpy as np
for rid,m in manifest.items():
    pp=use(m['instance_path']);check('B input hash '+rid,m['instance_sha256'],sha(pp),where=str(pp))
    with np.load(pp,allow_pickle=False) as z:npz[rid]={k:z[k].copy() for k in z.files}
records=[]; groups=[]; route_errors=[]; csv_errors=[]
for family in ['mirror_family','grover_depth','active_adjacent_p3']:
    rr=rows(stage/family/'ALL_SEEDS.csv',['run_id','variant','mode','rep'])
    variants=sorted({x['variant'] for x in rr}); groups.extend({'family':family,'variant':v,'mode':mo,'rows':sum(x['variant']==v and x['mode']==mo for x in rr)} for v,mo in sorted({(x['variant'],x['mode']) for x in rr}))
    for v in variants:
        for rid,m in manifest.items():
            pp=stage/family/'RUNS'/v/rid/'MEASUREMENTS.json' if family=='mirror_family' else stage/family/'RUNS'/v.replace('GROVER_','')/rid/'RESULT.json' if family=='grover_depth' else stage/family/'RUNS'/rid/'RESULT.json'
            d=js(pp)
            for x in d['records']:
                if x.get('mode','OPTIMIZED')!='OPTIMIZED':continue
                z=npz[rid];rt=x['route_indices'];cost=sum((F(str(z['travel'][i,j])) for i,j in zip(rt,rt[1:])),F(0));reported=F(str(x.get('sampled_best_seconds',x.get('road_seconds'))))
                valid=rt[0]==rt[-1]==0 and sorted(rt[1:-1])==list(range(1,m['n']+1))
                if not valid or abs(float(cost-reported))>1e-7:route_errors.append((family,v,rid,x['rep'],str(cost),str(reported)))
                records.append({'family':family,'variant':v,'run_id':rid,'rep':x['rep'],'input_sha256':m['instance_sha256'],'route_indices':json.dumps(rt,separators=(',',':')),'objective_seconds':float(reported),'source_path':str(use(pp)),'source_sha256':sha(use(pp))})
    lookup={(x['run_id'],x['variant'],str(x['rep'])):x for x in rr if x['mode']=='OPTIMIZED'}
    for x in records:
        if x['family']!=family:continue
        y=lookup[(x['run_id'],x['variant'],str(x['rep']))]
        if abs(float(F(y['sampled_best_seconds']))-x['objective_seconds'])>1e-7:csv_errors.append((family,x['variant'],x['run_id'],x['rep']))
check('B optimized reference rows',36800,len(records));check('B route cost/permutation mismatches',0,len(route_errors),where=str(route_errors[:5]));check('B CSV/raw mismatches',0,len(csv_errors),where=str(csv_errors[:5]))
check('B reference primary key unique',36800,len({(x['family'],x['variant'],x['run_id'],x['rep']) for x in records}))
table('B_PLAN_REFERENCES.csv',records);table('B_MEASUREMENT_GROUPS.csv',groups)
statsB={'physical_by_scale':dict(collections.Counter(m['scale_id'] for m in manifest.values())),'customers_by_scale':{m['scale_id']:m['n'] for m in manifest.values()},'input_hashes_verified':len(manifest),'plan_references':len(records),'unique_input_route_pairs':len({(x['input_sha256'],x['route_indices']) for x in records}),'full_run_signatures':None,'raw_cost_errors':route_errors,'csv_raw_errors':csv_errors}
bs=[]
for v in sorted({x['variant'] for x in records}):
    xx=[x for x in records if x['variant']==v];bs.append({'variant':v,'observations':len(xx),'physical':len({x['run_id'] for x in xx}),'route_pairs':len({(x['input_sha256'],x['route_indices']) for x in xx})})
table('B_ROUTE_COUNTS.csv',bs);dump('B_RECALCULATED.json',statsB)
# C: arithmetic from original parameters, component rows, saved per-trajectory DC.
t8=U/'review_outputs/material_ev_stage2_20261026/run02';t9=U/'review_outputs/t09_open_data_model_20261029/run01';bridge=U/'review_outputs/t08_t09_conditional_bridge_20261030/run01'
sc=js(t8/'SCENARIOS.json')['scenarios'];mass={}
for s in sc:
    p={k:F(str(v['value'])) for k,v in s['parameters'].items()};q=p['gross_energy']/p['voltage'];mp=q/p['q_ref']/p['utilization'];mn=q*p['np_ratio']/p['q_negative'];mass[s['scenario_id']]=float(mp/p['f_positive']+mn/p['f_negative']+s['cell_topology']['n_cells']*p['cell_other_mass']+p['pack_other_mass']+p['additional_mass'])
delta=mass['COND_LP_REF']-mass['COND_S200_REF'];check('T08 expected mass delta',5.448297415076922,delta,1e-10)
pack=rows(t9/'PACK_20KWH_SENSITIVITY.csv')
err=collections.defaultdict(float)
for x in pack:
    f=lambda k:F(x[k]);Q=f('gross_design_Wh')/f('mean_voltage_design_V');mp=Q/f('q_reference_Ah_kg')/f('positive_utilization');mn=Q*f('NP_after_formation')/f('negative_q_Ah_kg')/(1-f('negative_unavailable_fraction'));fp=F('.96') if x['series'].startswith('A_') else F('.75');ap=f('positive_face_area_m2');an=f('negative_face_area_m2');ep=f('positive_porosity');en=f('negative_porosity')
    e={'positive_active_kg':mp,'negative_active_kg':mn,'positive_coating_kg':mp/fp,'negative_coating_kg':mn/F('.98'),'Al_mass_kg':ap/2*f('Al_thickness_m')*2699,'Cu_mass_kg':an/2*f('Cu_thickness_m')*8960,'separator_dry_mass_kg':max(ap,an)*f('separator_areal_mass_kg_m2'),'liquid_mass_kg':(mp/fp/4458*ep/(1-ep)+mn/F('.98')/2200*en/(1-en)+max(ap,an)*F('.000025')*F('.41')+f('extra_liquid_volume_m3'))*1300}
    e['known_cell_components_sum_kg']=sum(e[k] for k in ['positive_coating_kg','negative_coating_kg','Al_mass_kg','Cu_mass_kg','separator_dry_mass_kg','liquid_mass_kg'])
    for k,val in e.items():err[k]=max(err[k],abs(float(val)-float(x[k])))
for k,e in err.items():check('T09 component residual '+k,0,e,1e-8,'PACK_20KWH_SENSITIVITY.csv:'+k)
bounds=rows(bridge/'T09_MASS_BOUNDARIES.csv',['scenario_id']);response=rows(bridge/'DC_MASS_RESPONSE.csv',['pair_id','probe_id','physical_instance_id','rolling_case','reference_running_mass_kg'])
ener=rows(t8/'MATERIAL_ENERGY.csv',['dataset','physical_instance_id','method','rolling_case','scenario_id'])
ec={(x['physical_instance_id'],x['rolling_case'],x['scenario_id']):x for x in ener if x['dataset']=='CLASSICAL'}
cstats=[]
for rolling in sorted({x['rolling_case'] for x in ener}):
    keys=[k for k in ec if k[1]==rolling and k[2]=='COND_LP_REF'];base=sum(float(ec[k]['net_DC_Wh']) for k in keys);ds=[float(ec[k]['net_DC_Wh'])-float(ec[(k[0],rolling,'COND_S200_REF')]['net_DC_Wh']) for k in keys];rates=[d/float(ec[k]['net_DC_Wh'])*100 for k,d in zip(keys,ds)]
    cstats.append({'rolling_case':rolling,'n':len(keys),'base_sum_Wh':base,'saving_sum_Wh':sum(ds),'weighted_percent':sum(ds)/base*100,'individual_mean_percent':sum(rates)/len(rates)})
check('T08 lower expected weighted rate',.4125790100606282,cstats[0]['weighted_percent'],1e-10)
maxres=collections.defaultdict(float)
for x in response:
    n=lambda k:float(x[k]);maxres['DC_subtraction']=max(maxres['DC_subtraction'],abs(n('baseline_DC_Wh')-n('S_DC_Wh')-n('DC_saving_Wh')));maxres['mass_boundary']=max(maxres['mass_boundary'],abs(n('known_mass_boundary_kg')-n('unknown_mass_difference_probe_kg')-n('net_mass_saving_probe_kg')));maxres['rate']=max(maxres['rate'],abs(n('DC_saving_Wh')/n('baseline_DC_Wh')*100-n('individual_saving_percent')))
    parts=sum(n('W'+str(i)+'_baseline_mask_DC_saving_Wh') for i in range(1,5))+n('branch_correction_Wh');maxres['component_sum']=max(maxres['component_sum'],abs(parts-n('DC_saving_Wh')))
for k,v in maxres.items():check('bridge '+k,0,v,1e-8)
agg=rows(bridge/'T08_T09_DC_COMPARISON.csv',['series','design_policy','probe_id','rolling_case','scale_id','reference_running_mass_kg'])
aggerr=0
for x in agg:
    if x['series']!='T09_CONDITIONAL_REFERENCE_MASS_SENSITIVITY':continue
    group=[y for y in response if y['design_policy']==x['design_policy'] and y['probe_id']==x['probe_id'] and y['rolling_case']==x['rolling_case'] and (x['scale_id']=='ALL' or y['scale_id']==x['scale_id']) and y['reference_running_mass_kg']==x['reference_running_mass_kg']]
    if group:
        w=sum(float(y['DC_saving_Wh']) for y in group)/sum(float(y['baseline_DC_Wh']) for y in group)*100;aggerr=max(aggerr,abs(w-float(x['energy_weighted_saving_percent'])))
check('bridge weighted group residual',0,aggerr,1e-9)
statsC={'mass_T08':mass,'delta_T08_kg':delta,'T08_DC':cstats,'T09_rows':len(pack),'T09_complete_pack_missing':sum(not x['complete_pack_mass_kg'] for x in pack),'T09_overlap_states':dict(collections.Counter(x['overlap_condition'] for x in pack)),'T09_component_max_error':dict(err),'bridge_rows':len(response),'bridge_unique_trajectory_hashes':len({x['trajectory_sha256'] for x in response}),'bridge_max_residual':dict(maxres),'known_boundaries':sorted({(x['design_policy'],x['known_mass_boundary_kg']) for x in response}),'aggregate_residual':aggerr}
dump('C_RECALCULATED.json',statsC)
dump('CSV_SCHEMA_AUDIT.json',schemas);dump('CHECKS.json',checks)
table('SOURCE_FILES.csv',list(inventory.values()))
# Verify all read inputs unchanged, with no mutation of source files.
changed=[p for p,x in inventory.items() if sha(Path(p))!=x['sha256']]
dump('PRESERVATION_CHECK.json',{'checked':len(inventory),'changed':changed,'tracked_diff':subprocess.check_output(['git','diff','--stat'],cwd=R,text=True)})
print(json.dumps({'A':statsA,'B':statsB,'C':statsC,'checks':dict(collections.Counter(x['status'] for x in checks)),'sources':len(inventory),'changed':changed},ensure_ascii=False,indent=2))
