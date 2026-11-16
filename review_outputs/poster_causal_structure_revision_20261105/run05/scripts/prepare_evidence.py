"""Read and re-express saved tables; no scientific experiments or bootstrap reruns."""
from pathlib import Path
from collections import Counter
import csv,json
R=Path(__file__).resolve().parents[1];ROOT=Path('/home/takuma/kmd-analysis');S=ROOT/'review_outputs/quantum_ev_step5_20261105';E=R/'evidence'
def read(p):return list(csv.DictReader(p.open(encoding='utf-8-sig')))
def save(name,rs):
 with (E/name).open('w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=list(rs[0]));w.writeheader();w.writerows(rs)
rs=read(S/'data/INPUT_UNIT_STATISTICS.csv');checks=[]
def ck(n,ok):checks.append(dict(item=n,status='PASS' if ok else 'FAIL'));assert ok,n
meta=json.loads((S/'data/SUMMARY.json').read_text())
ck('saved sample hierarchy',meta['n_inputs']==460 and meta['n_groups']==25 and meta['n_parents']==26 and meta['n_reps']==10 and meta['n_plans']==36800)
cfgs=['MEAN_P2','CVAR01_P2','CVAR10_P2','COHERENT2_P2','COHERENT4_P2','ACTIVE_ADJACENT_P3_GRID']
def row(level,scale,cfg,metric):
 v=[r for r in rs if r['level']==level and r['scale']==scale and r['config_id']==cfg and r['metric']==metric];assert len(v)==1,(level,scale,cfg,metric);return v[0]
table=[]
for scale,n in zip(['R0','R1','R2','R3','R4','R5'],[3,4,5,25,100,125]):
 baseline=row('input_mean_by_scale_config',scale,'MEAN_P2','relative_gap_percent')
 for cfg in cfgs:
  z=row('input_mean_by_scale_config',scale,cfg,'relative_gap_percent')
  ck('local identical '+scale+'/'+cfg,all(abs(float(z[k])-float(baseline[k]))<1e-10 for k in ['mean','sd','median','q1','q3']))
 for cfg,display in [('MEAN_P2','限定5/隣接1（各条件同値）'),('GROVER_P2','GM-QAOA 層2'),('GROVER_P3','GM-QAOA 層3')]:
  a=row('input_mean_by_scale_config',scale,cfg,'relative_gap_percent');b=row('input_mean_by_scale_config',scale,cfg,'delta_s')
  table.append(dict(scale=scale,delivery_stops=n,inputs=int(a['n']),config=cfg,display=display,mean_relative_percent=float(a['mean']),SD_relative_points=float(a['sd']),median_relative_percent=float(a['median']),IQR_relative_points=float(a['q3'])-float(a['q1']),P05_relative_percent=float(a['p05']),P95_relative_percent=float(a['p95']),mean_delta_s=float(b['mean']),SD_delta_s=float(b['sd']),median_delta_s=float(b['median']),IQR_delta_s=float(b['q3'])-float(b['q1']),P05_delta_s=float(b['p05']),P95_delta_s=float(b['p95']),definition='JQ-JC; negative=improvement; input mean of10 measurements',source=str(S/'data/INPUT_UNIT_STATISTICS.csv')))
save('SCALE_METHOD_STATISTICS.csv',table)
full=[]
for cfg in cfgs+['GROVER_P2','GROVER_P3']:
 for m in ['delta_s','relative_gap_percent']:
  a=row('input_mean_by_config','',cfg,m);full.append(a)
  ck('all config median zero '+cfg+'/'+m,abs(float(a['median']))<1e-12)
save('CONFIG_INPUT_DISTRIBUTIONS.csv',full)
save('FULL_INPUT_STATISTICS.csv',rs)
counts=read(S/'data/IMPROVED_EQUAL_WORSENED.csv');save('IMPROVED_EQUAL_WORSENED.csv',counts)
allcounts={r['classification']:int(r['count']) for r in counts if r['level']=='all_plans'}
ck('classification counts',allcounts=={'improved':0,'equal':28200,'worsened':8600})
exist=read(S/'data/FULL_SUPPORT_EXISTENCE_BY_INPUT.csv')
better=[r for r in exist if r['A_full_support_status']=='REFERENCE_BETTER_IN_FULL_SUPPORT'];weak=[r for r in better if r['reference_class']=='SAVED_EXACT_MIP_EQUALITY_NO_EXTERNAL_VIPR'];strong=[r for r in better if r not in weak]
ex=dict(strong_better=len(strong),conditional_better=len(weak),greedy_equal=sum(r['A_full_support_status']=='GREEDY_EQUALS_REFERENCE' for r in exist),unproved=sum(r['A_full_support_status']=='UNPROVED_JSTAR' for r in exist))
ck('existence tiers',ex==dict(strong_better=135,conditional_better=41,greedy_equal=238,unproved=46));save('FULL_SUPPORT_EXISTENCE.csv',exist)
# Step2 interval sign was JC-JQ. Reverse signs and bounds, and check every point against Step5.
source=ROOT/'review_outputs/quantum_ev_step2_analysis_trial_20261104_155535/PATH1_UNCERTAINTY_INTERVALS.csv';interval=[]
for a in read(source):
 if a['classical_method']!='ITERATED_GREEDY_ADJACENT_SWAP' or a['metric']!='mean_delta_J_s':continue
 scale=a['scale'];cfg=a['config_id'];b=row('input_mean_by_config','',cfg,'delta_s') if scale=='ALL' else row('input_mean_by_scale_config',scale,cfg,'delta_s')
 point=-float(a['point']);lo=-float(a['upper95']);hi=-float(a['lower95'])
 ck('interval point sign '+scale+'/'+cfg+'/'+a['kind'],abs(point-float(b['mean']))<1e-7)
 interval.append(dict(scale=scale,config=cfg,kind=a['kind'],mean_delta_s=point,lower95_s=lo,upper95_s=hi,resamples=a['resamples'],seed=a['seed'],clusters_present=a['clusters_present'],sampling_unit=a['unit'],definition='JQ-JC; bounds reversed from saved JC-JQ; not real-fleet CI',source=str(source),original_point=a['point'],original_lower95=a['lower95'],original_upper95=a['upper95']))
save('SAVED_RESAMPLING_SENSITIVITY.csv',interval)
M=ROOT/'review_outputs/t08_t09_final_adoption_20261105';material=json.loads((M/'evidence/RUN_RESULT.json').read_text())
ck('material calculation and practical scope',material['failures']==0 and material['original_T09_rows']==183 and material['scientific_practical_adoption']=='HOLD' and material['T09_complete_pack']=='HOLD')
save('MATERIAL_PARAMETER_ADOPTION.csv',read(M/'data/PARAMETER_ADOPTION.csv'))
save('MATERIAL_SENSITIVITY_ORIGINS.csv',read(M/'data/SENSITIVITY_RANGE_ORIGINS.csv'))
save('MATERIAL_FINAL_AUDIT.csv',read(M/'evidence/FINAL_AUDIT.csv'))
summary=dict(definition='DeltaJ=JQ-JC (positive=worsening)',counts=allcounts,existence=ex,materials=material,statistical_units='input first;25 demand groups/26 parents;10 measurements per fixed input/config fit',interval_note='saved group-resampling sensitivity and fixed-fit measurement sensitivity; no new bootstrap; not real-fleet confidence intervals',checks=checks,experiments_run=0)
(E/'DATA_BINDING.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2));save('DATA_BINDING_CHECKS.csv',checks)
print('Bound saved tables:',len(table),'scale-method rows;',len(interval),'saved interval rows;',len(checks),'checks PASS')
