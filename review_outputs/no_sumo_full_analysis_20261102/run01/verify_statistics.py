"""Independent grouped result and interval readback; does not import statistics_tables."""
import os
os.environ['OPENBLAS_NUM_THREADS']='1'
from common import *
import common as audit_io
import numpy as np
def grouped(xx,keys):
 z=collections.defaultdict(list)
 for x in xx:z[tuple(x[k] for k in keys)].append(x)
 return z
def main():
 start=time.monotonic();pol=rows(O/'A_POLICY_DECISIONS_2808.csv');base=rows(O/'A_CLASSICAL_BASELINE_2808.csv');ap=rows(O/'A_PAIRED_PER_PROBLEM.csv');bp=rows(O/'B_PLAN_REFERENCES_36800.csv');bi=rows(O/'B_INPUT_SEED_AGGREGATES.csv');ct=rows(O/'C_T08_PAIRED_DIFFERENCES.csv');cb=rows(O/'C_BRIDGE_MASS_DC_FULL.csv');ci=rows(O/'CLUSTER_SENSITIVITY_INTERVALS.csv');clusters=sorted({x['group_id'] for x in pol});j={x:i for i,x in enumerate(clusters)};count=0;errors=[]
 def ck(k,e,a,tol=1e-8):
  nonlocal count
  count+=1
  if not math.isclose(float(e),float(a),abs_tol=tol,rel_tol=1e-11):errors.append({'check':k,'expected':e,'actual':a,'tol':tol})
 pm=grouped(pol,['condition_id']);bm=grouped(base,['condition_id']);aps=grouped(ap,['series_id','comparison_id']);br=grouped(bp,['problem_id','config_id']);bsm=grouped(bi,['config_id']);cts=grouped(ct,['condition_id']);cbs=grouped(cb,['pair_id','probe_id','rolling_case','reference_running_mass_kg']);poly={(x['condition_id'],x['problem_id']):x for x in pol};basely={(x['condition_id'],x['problem_id']):x for x in base}
 for x in rows(O/'A_SUMMARY_BY_CONDITION.csv'):
  rr=pm[(x['condition_id'],)];bb=bm[(x['condition_id'],)];den=math.fsum(float(y['denominator_PE']) for y in rr);on=math.fsum(float(y['on_time_PE']) for y in rr);bon=math.fsum(float(y['on_time_PE']) for y in bb);ck('A summary PE rate',100*on/den,x['PE_on_time_percent']);ck('A summary PE difference',100*(on-bon)/den,x['delta_F_PE_pp']);ck('A adoption count',sum(y['adopted_method']=='QUANTUM' for y in rr),x['quantum_adopted'])
 for x in bi:
  rr=br[(x['problem_id'],x['config_id'])];ck('B seed mean',np.mean([float(y['delta_objective_vs_initial_s']) for y in rr]),x['mean_delta_objective_s']);ck('B seed SD',np.std([float(y['objective_s']) for y in rr],ddof=1),x['seed_objective_sd_s']);ck('B rep denominator',10,x['measurement_reps'])
 for x in rows(O/'B_SUMMARY_BY_SCALE_AND_METHOD.csv'):
  rr=[y for y in bi if y['config_id']==x['config_id'] and (x['scale']=='ALL' or y['scale']==x['scale'])];valid=[y for y in rr if y['mean_global_gap_percent']!=''];ck('B summary delta',np.mean([float(y['mean_delta_objective_s']) for y in rr]),x['mean_delta_objective_s']);ck('B summary exact denominator',len(valid),x['exact_reference_inputs']);ck('B summary gap',np.mean([float(y['mean_global_gap_percent']) for y in valid]),x['mean_global_gap_percent']);ck('B summary physical denominator',len(rr),x['physical_inputs'])
 nums=[];dens=[]
 for x in ci:
  series=x['series_id'];cond=x['condition_id'];metric=x['metric'];rr=[];field=metric;denfield=None;multiplier=1
  if series=='A_POLICY':
   if metric=='delta_F_PE_pp':
    rr=[{'group_id':y['group_id'],'value':100*(float(y['on_time_PE'])-float(basely[(cond,y['problem_id'])]['on_time_PE'])),'den':float(y['denominator_PE'])} for y in pm[(cond,)]];field='value';denfield='den'
   else:rr=aps[('A_POLICY',cond)]
  elif series=='A_MECHANISM':rr=aps[('A_MECHANISM',cond)]
  elif series=='B':rr=[y for y in bsm[(cond,)] if x['scale']=='ALL' or y['scale']==x['scale']]
  elif series=='C_T08':
   rr=cts[(cond,)];field='saving_DC_Wh'
   if metric=='weighted_saving_percent':multiplier=100;denfield='baseline_DC_Wh'
  elif series=='C_BRIDGE':
   rr=cbs[tuple(cond.split('|'))];field='recomputed_saving_Wh'
   if metric=='weighted_saving_percent':multiplier=100;denfield='recomputed_baseline_DC_Wh'
  n=np.zeros(25);d=np.zeros(25)
  for y in rr:
   if y[field] in ('',None):continue
   index=j[y['group_id']];n[index]+=multiplier*float(y[field]);d[index]+=float(y[denfield]) if denfield else 1
  ck('interval point '+series+cond+metric,n.sum()/d.sum(),x['point']);nums.append(n);dens.append(d)
 rng=np.random.Generator(np.random.PCG64(20261102));w=rng.multinomial(25,[1/25]*25,10000);nn=w@np.stack(nums,axis=1);dd=w@np.stack(dens,axis=1);bs=np.divide(nn,dd,out=np.full_like(nn,np.nan),where=dd>0)
 for k,x in enumerate(ci):
  good=bs[np.isfinite(bs[:,k]),k];ck('interval lower',np.quantile(good,.025),x['lower95']);ck('interval upper',np.quantile(good,.975),x['upper95']);ck('undefined replicates',10000-len(good),x['undefined_resamples'])
 # Output replays include every primary CSV, not just aggregate equality.
 replays=[]
 for p in sorted((O/'replay').glob('*.csv')):
  target=O/p.name;equal=target.is_file() and sha(target)==sha(p);replays.append({'file':p.name,'original_sha256':sha(target) if target.is_file() else None,'replay_sha256':sha(p),'status':'PASS_BYTE_IDENTICAL' if equal else 'FAIL'});ck('replay hash '+p.name,1,int(equal),0)
 table('REPLAY_OUTPUT_HASH_CHECK.csv',replays);table('STATISTICS_VERIFICATION_ERRORS.csv',errors);summary={'checks':count,'errors':len(errors),'bootstrap_contrasts_recalculated':len(ci),'replay_primary_files':len(replays),'replay_mismatches':sum(x['status']=='FAIL' for x in replays),'metrics':audit_io.metric(start),'scope':'Independent summaries/10k cluster intervals; primary CSV byte replay'};dump('STATISTICS_VERIFICATION.json',summary);dump('STAT_VERIFY_SOURCES.json',list(SRC.values()));print(json.dumps(summary))
 if errors:raise RuntimeError('Statistics independent mismatch')
if __name__=='__main__':main()
