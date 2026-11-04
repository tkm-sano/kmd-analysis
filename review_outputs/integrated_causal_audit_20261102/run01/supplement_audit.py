"""Additional read-only evidence checks. No research module imported."""
from pathlib import Path
from fractions import Fraction as F
import csv,json,hashlib,collections,gzip,math,xml.etree.ElementTree as ET
O=Path(__file__).resolve().parent;R=O.parents[2];U=Path('/home/takuma/kmd-analysis-pre-clean-20261102-112222/untracked');B=Path('/home/takuma/kmd-analysis-preservation-20261014-173544-a64e484c/backup');L=B.parent/'relocated';S=U/'review_outputs/staged_qaoa_validation_20261102'
inv={};checks=[]
def use(p):
 p=Path(p)
 if not p.is_file():
  for b in [R,U,B,L]:
   if p.is_relative_to(b):rel=p.relative_to(b);break
  else:raise FileNotFoundError(p)
  p=next(b/rel for b in [R,U,B,L] if (b/rel).is_file())
 if str(p) not in inv:
  with p.open('rb') as h:hh=hashlib.file_digest(h,'sha256').hexdigest()
  inv[str(p)]={'path':str(p),'sha256':hh,'bytes':p.stat().st_size}
 return p
def js(p):return json.loads(use(p).read_text())
def rows(p):
 with use(p).open() as h:return list(csv.DictReader(h))
def ck(name,expected,actual,tol=1e-8,where=''):
 ok=abs(expected-actual)<=tol if isinstance(expected,(float,int)) and isinstance(actual,(float,int)) else expected==actual
 checks.append(dict(name=name,expected=expected,actual=actual,status='PASS' if ok else 'FAIL',location=where))
def dump(n,d):(O/n).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def table(n,a):
 with (O/n).open('w',newline='') as h:w=csv.DictWriter(h,fieldnames=list(a[0]));w.writeheader();w.writerows(a)
# Native events original XML, keeping model completion distinct from stop end.
ops=rows(U/'review_outputs/cpx01_d11_validation_20261017/operations_2808.csv');aquality=[]
for pid in sorted({x['PID'] for x in ops}):
 x=next(x for x in ops if x['PID']==pid);c=js(x['classical_source']);q=js(x['quantum_source']);best=q['best_final_feasible_route'];opt=F(str(q['exact_physical_optimum_s']));value=F(best['road_travel_objective_s']) if best else None
 aquality.append({'PID':pid,'acquired':best is not None,'objective_seconds':str(value) if value is not None else '', 'reference_optimum_seconds':str(opt),'optimal_match_exact':value==opt if value is not None else '', 'gap_percent':float((value-opt)/opt*100) if value is not None else '', 'status':q['execution_status']})
table('A_QUALITY_RECALCULATED.csv',aquality)
ar=rows(U/'review_outputs/causal_engineering_audit_20261027/run01/A_NATIVE_TASK_COMPLETION.csv')
for i,x in enumerate(ar,2):
 el=ET.parse(use(x['stop_source'])).getroot().findall('stopinfo')[int(x['stop_order'])-1]
 ck('native started row '+str(i),float(el.attrib['started']),float(x['native_stop_reached_s']),where=x['stop_source'])
 ck('native ended row '+str(i),float(el.attrib['ended']),float(x['native_stop_end_s']),where=x['stop_source'])
# Exact-reference provenance is retained; no new solver is run.
refs=rows(S/'CLASSICAL_EXACT_COMPARISON.csv');refmap={x['run_id']:x for x in refs}
plans=rows(O/'B_PLAN_REFERENCES.csv');manifest={x['run_id']:x for x in js(S/'mirror_family/MANIFEST.json')}
metrics=[];times=[];source_binding=[];complete=[];raw_objectives={}
for family,variant in sorted({(x['family'],x['variant']) for x in plans}):
 sub=[x for x in plans if x['family']==family and x['variant']==variant];walls=[];cpus=[];rss=[];states=collections.Counter();fit_hashes=0
 for rid,m in manifest.items():
  base=S/family/'RUNS'/variant/rid if family=='mirror_family' else S/family/'RUNS'/variant.replace('GROVER_','')/rid if family=='grover_depth' else S/family/'RUNS'/rid
  result=js(base/('MEASUREMENTS.json' if family=='mirror_family' else 'RESULT.json'))
  fit=js(base/'FIT.json') if family!='active_adjacent_p3' else result
  states[result['status']]+=1
  for record in result['records']:
   if record.get('mode','OPTIMIZED')=='OPTIMIZED':raw_objectives[(variant,rid,str(record['rep']))]=F(str(record.get('sampled_best_seconds',record.get('road_seconds'))))
  if 'wall_seconds' in fit:walls.append(fit['wall_seconds'])
  if 'CPU_seconds' in fit or 'cpu_seconds' in fit:cpus.append(fit.get('CPU_seconds',fit.get('cpu_seconds')))
  if 'peak_RSS_bytes' in fit:rss.append(fit['peak_RSS_bytes'])
  if 'instance_sha256' in fit:ck('fit input binding '+variant+'/'+rid,m['instance_sha256'],fit['instance_sha256']);fit_hashes+=1
  for rel,expected in fit.get('sources',{}).items():
   pp=S/family/'SOURCE_SNAPSHOT'/rel
   if pp.is_file():
    actual=inv.get(str(pp),{}).get('sha256')
    if actual is None:use(pp);actual=inv[str(pp)]['sha256']
    if actual!=expected:
     candidates=list((S/family).glob('SOURCE_AT_*/'+rel));match=[]
     for old in candidates:
      use(old)
      if inv[str(old)]['sha256']==expected:match.append(str(old))
     source_binding.append({'variant':variant,'run_id':rid,'path':str(pp),'expected':expected,'actual':actual,'status':'PASS_HISTORICAL_SNAPSHOT_FOUND' if match else 'HOLD_VERSION_CHAIN_REVIEW','matching_historical_paths':';'.join(match)})
   else:source_binding.append({'variant':variant,'run_id':rid,'path':str(pp),'expected':expected,'actual':'MISSING_IN_FAMILY_SNAPSHOT','status':'HOLD_VERSION_CHAIN_REVIEW','matching_historical_paths':''})
 times.append({'variant':variant,'cases':460,'raw_status_counts':json.dumps(states),'wall_scope':'fit only, except ACTIVE full case; shared across 10 measurement seeds','wall_n':len(walls),'wall_sum_s':sum(walls),'wall_mean_s':sum(walls)/len(walls) if walls else '', 'CPU_n':len(cpus),'CPU_sum_s':sum(cpus),'peak_RSS_n':len(rss),'peak_RSS_max_bytes':max(rss) if rss else '', 'input_fit_bindings_checked':fit_hashes})
 for scale in ['R0','R1','R2','R3','R4','R5']:
  xx=[x for x in sub if x['run_id'].startswith(scale+'_')];gaps=[];matches=0;improve=0;seconds=[]
  for x in xx:
   ref=refmap[x['run_id']];obj=raw_objectives[(variant,x['run_id'],str(x['rep']))];ini=F(ref['classical_initial_seconds']);ex=ref['global_exact_optimum_seconds']
   improve+=float(ini-obj)>1e-7
   if ex:
    exact=F(ex);gaps.append(float((obj-exact)/exact*100));matches+=obj==exact
   seconds.append(float(obj-ini))
  metrics.append({'variant':variant,'scale':scale,'physical':len(xx)//10,'observations':len(xx),'exact_reference_observations':len(gaps),'optimal_match_exact_fraction':matches,'mean_exact_gap_percent':sum(gaps)/len(gaps) if gaps else '', 'improve_initial_observations_tolerance_1e_7_seconds':improve,'mean_route_minus_initial_seconds':sum(seconds)/len(seconds)})
table('B_QUALITY_RECALCULATED.csv',metrics);table('B_SAVED_TIMING_SCOPES.csv',times);table('B_SOURCE_BINDING_GAPS.csv',source_binding or [{'status':'NONE'}])
# T09 baseline pair differences calculated from original component totals.
pack=rows(U/'review_outputs/t09_open_data_model_20261029/run01/PACK_20KWH_SENSITIVITY.csv');bounds=rows(U/'review_outputs/t08_t09_conditional_bridge_20261030/run01/T09_MASS_BOUNDARIES.csv');pairs=collections.defaultdict(list)
for x in bounds:
 if x['pair_id']:pairs[x['pair_id']].append(x)
diffs=[]
for pid,xx in pairs.items():
 if len(xx)!=2:continue
 lp=next(x for x in xx if x['material_condition']=='LP');ss=next(x for x in xx if x['material_condition']=='S200');li=int(lp['scenario_id'].split('_')[-1])-1;si=int(ss['scenario_id'].split('_')[-1])-1
 delta=float(pack[li]['known_cell_components_sum_kg'])-float(pack[si]['known_cell_components_sum_kg']);ck('T09 raw known pair '+pid,float(lp['known_LP_minus_S_mass']),delta)
 diffs.append({'pair_id':pid,'policy':lp['design_policy'],'LP_csv_line':li+2,'S_csv_line':si+2,'raw_LP_known_kg':pack[li]['known_cell_components_sum_kg'],'raw_S_known_kg':pack[si]['known_cell_components_sum_kg'],'delta_kg':delta})
table('C_RAW_PAIR_DIFFERENCES.csv',diffs)
# Hash all 460 compressed trajectories; calculate only one representative scalar DC.
resp=rows(U/'review_outputs/t08_t09_conditional_bridge_20261030/run01/DC_MASS_RESPONSE.csv');traces={x['source_file']:x for x in resp}
for rel,x in traces.items():
 p=use(R/rel);ck('trajectory hash '+x['physical_instance_id'],x['trajectory_sha256'],inv[str(p)]['sha256'])
first=next(iter(traces.values()));p=use(R/first['source_file'])
with gzip.open(p,'rt') as h:rr=list(csv.DictReader(h))
print('trajectory columns',rr[0].keys())
# Accept known canonical time/speed field names, fail explicitly for unknown schema.
tk=next(k for k in ['timestamp_s','time','time_s','timestep','t'] if k in rr[0]);vk=next(k for k in ['speed','speed_m_s','v'] if k in rr[0])
def scalar(tv,m,pressure):
 w=[]
 for (t0,v0),(t1,v1) in zip(tv,tv[1:]):
  dt=t1-t0;assert dt==1
  ds=v1*dt;W1=m*9.80665*(.005+(.01+.0095*(3.6*v1/100)**2)/pressure)*ds;W2=.5*1.2041*1.175*v1*v1*ds;W3=.5*m*(v1*v1-v0*v0);W4=.5*61*(v1*v1-v0*v0)
  w.append(max(math.fsum([W1,W2,W3,W4]),0)/(.9*3600))
 return math.fsum(w)
tv=[(float(x[tk]),float(x[vk])) for x in rr];mass=float(first['reference_running_mass_kg']);sdc=scalar(tv,mass,float(first['pressure_bar']));ck('representative trajectory scalar DC',float(first['baseline_DC_Wh']),sdc,1e-7,where=str(p))
fixture=scalar([(0,0),(1,10),(2,10),(3,0)],1200,4.5)
dump('SUPPLEMENT_SUMMARY.json',{'checks':dict(collections.Counter(x['status'] for x in checks)),'B_source_version_gap_records':len(source_binding),'B_raw_statuses':times,'trajectory_hashes_checked':len(traces),'representative_scalar_DC_Wh':sdc,'fixture_stop_accelerate_cruise_decelerate_Wh':fixture,'raw_pair_count':len(diffs)})
dump('SUPPLEMENT_CHECKS.json',checks);table('SUPPLEMENT_SOURCE_FILES.csv',list(inv.values()))
changed=[]
for p,x in inv.items():
 with Path(p).open('rb') as h:hh=hashlib.file_digest(h,'sha256').hexdigest()
 if hh!=x['sha256']:changed.append(p)
dump('SUPPLEMENT_PRESERVATION.json',{'checked':len(inv),'changed':changed})
print('done',len(checks),'checks',len(source_binding),'version gaps',len(inv),'inputs',changed)
