"""Read-only arithmetic reconciliation of latest completed trials. No experiments run."""
from pathlib import Path
from fractions import Fraction
from collections import defaultdict,Counter
import csv,json,hashlib,statistics
from zipfile import ZipFile
import xml.etree.ElementTree as ET
R=Path(__file__).resolve().parents[1];ROOT=Path('/home/takuma/kmd-analysis')
S2=ROOT/'review_outputs/quantum_ev_step2_analysis_trial_20261104_155535';S3=ROOT/'review_outputs/quantum_ev_step3_synthesis_trial_20261104_174309';OLD=ROOT/'review_outputs/no_sumo_full_analysis_20261102/run01';E=R/'evidence';checks=[]
def rows(p):return list(csv.DictReader(p.open()))
def write(name,rs):
 with (E/name).open('w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=list(rs[0]));w.writeheader();w.writerows(rs)
def ck(name,a,b,source,tol=None):
 ok=abs(float(a)-float(b))<tol if tol else a==b
 checks.append(dict(item=name,actual=a,expected=b,status='PASS' if ok else 'FAIL',source=source));assert ok,checks[-1]
b=rows(OLD/'B_PLAN_REFERENCES_36800.csv');classical={v['problem_id']:v for v in rows(OLD/'B_AUXILIARY_CLASSICAL_IMPROVEMENTS.csv') if v['method']=='ITERATED_GREEDY_ADJACENT_SWAP'}
ck('primary_baselines',len(classical),460,'B_AUXILIARY_CLASSICAL_IMPROVEMENTS.csv')
ck('saved_candidates',len(b),36800,'B_PLAN_REFERENCES_36800.csv')
by=defaultdict(list);positive=0;initial_positive=set()
for v in b:
 c=classical[v['problem_id']];assert c['input_sha256']==v['input_sha256']
 j=Fraction(v['objective_fraction']);jc=Fraction(c['classical_best_seconds']);d=jc-j
 positive+=d>0
 if Fraction(v['classical_initial_fraction'])>j:initial_positive.add(v['problem_id'])
 by[(v['scale'],v['config_id'],v['problem_id'])].append(float(d))
ck('positive_vs_primary_greedy',positive,0,'Fraction(JC-JQ); same input SHA')
ck('legacy_initial_improved_inputs',len(initial_positive),7,'legacy initial is auxiliary, not primary')
stored=rows(S3/'data/PATH1_STATISTICAL_RESULTS.csv');agg=[]
for scale,n in zip(['R0','R1','R2','R3','R4','R5'],[3,4,5,25,100,125]):
 for cfg in sorted({v['config_id'] for v in b}):
  vals=[statistics.fmean(x) for (s,c,p),x in by.items() if s==scale and c==cfg]
  val=statistics.fmean(vals);z=next(v for v in stored if v['scale']==scale and v['config_id']==cfg and v['classical_method']=='ITERATED_GREEDY_ADJACENT_SWAP')
  ck('mean_'+scale+'_'+cfg,val,float(z['input_mean_delta_J_mean']),str(S3/'data/PATH1_STATISTICAL_RESULTS.csv'),1e-7)
  agg.append(dict(scale=scale,n=n,config_id=cfg,inputs=len(vals),mean_primary_delta_s=val,primary='JC-JQ; positive=improvement',source=str(S3/'data/PATH1_STATISTICAL_RESULTS.csv')))
write('PRIMARY_COMPARISON_RECONCILED.csv',agg)
ref=rows(S2/'EXACT_REFERENCE_STATUS.csv');accepted=[v for v in ref if v['accepted_exact_available']=='True'];types=Counter(v['reference_evidence_class'] for v in accepted)
ck('accepted_reference',len(accepted),414,'EXACT_REFERENCE_STATUS.csv; includes conditional saved-MIP tier')
ck('unproved_reference',len(ref)-len(accepted),46,'EXACT_REFERENCE_STATUS.csv')
print('Reference evidence types:',dict(types))
ck('saved_MIP_only',sum('MIP' in v['reference_evidence_class'] for v in accepted),41,'EXACT_REFERENCE_STATUS.csv')
# Controlled diagnostic count is number of learning runs whose rep0 best is optimal.
ctrl=rows(S3/'data/QAOA_CONTROLLED_CELL_SUMMARY.csv');ck('controlled_cells',len(ctrl),96,'QAOA_CONTROLLED_CELL_SUMMARY.csv')
ck('learning_fits',sum(int(v['independent_learning_fits']) for v in ctrl),9312,'96 cells x97 starts')
selected=[]
for state,count in [('BASIS_INITIAL',0),('UNIFORM_SUPPORT',97)]:
 v=next(v for v in ctrl if v['problem_id']=='R1_020' and v['support']=='FULL_PERMUTATION' and v['initial_state']==state and v['mixer']=='PROJECTOR' and v['layers']=='1' and v['method']=='QAOA')
 ck('diagnostic_'+state,int(v['primary_optimal_rep0_count']),count,'QAOA controlled cell; rep0 per learning run')
 ck('diagnostic_starts_'+state,int(v['independent_learning_fits']),97,'same chosen diagnostic input')
 selected.append(v)
write('DIAGNOSTIC_SELECTED_CELLS.csv',selected)
k=rows(S3/'data/DC_MASS_KERNEL_INDEPENDENT.csv');ck('DC_mass_cases',len(k),920,'460 trajectories x2 rolling coefficients')
ck('DC_distinct_trajectories',len({v['trajectory_sha256'] for v in k}),460,'same frozen saved trajectories')
ck('DC_Chen_free',all(v['Chen_capacity_input']=='NONE' for v in k),True,'DC_MASS_KERNEL_INDEPENDENT.csv')
ck('DC_mass_interval',all(float(v['mass_lo_kg'])==1000 and float(v['mass_hi_kg'])==1250 for v in k),True,'Step2 declared interval; not a measured EV range')
ck('DC_positive_right_derivative',sum(float(v['right_derivative_lo_Wh_kg'])>0 for v in k),920,'fixed model lower endpoint right derivative')
ck('DC_nondecreasing_slope',all(float(v['left_derivative_hi_Wh_kg'])+1e-9>=float(v['right_derivative_lo_Wh_kg']) for v in k),True,'piecewise convex positive-part model')
summ=[]
for case in ['CRR_LOWER_BOUND','CRR_UPPER_BOUND']:
 vals=[float(v['right_derivative_lo_Wh_kg']) for v in k if v['rolling_case']==case];z=next(v for v in rows(S3/'data/DC_MASS_KERNEL_SUMMARY.csv') if v['rolling_case']==case)
 for name,value in [('min',min(vals)),('mean',statistics.fmean(vals)),('max',max(vals))]:ck(case+'_'+name,value,float(z['slope_'+name]),'DC_MASS_KERNEL_SUMMARY.csv',1e-9)
 summ.append(dict(case=case,trajectories=len(vals),min_Wh_kg=min(vals),mean_Wh_kg=statistics.fmean(vals),max_Wh_kg=max(vals),mass_evaluation_kg=1000,range_scope='trajectory spread, not CI',source=str(S3/'data/DC_MASS_KERNEL_SUMMARY.csv')))
write('DC_SLOPE_RECONCILED.csv',summ)
# Corrected Step3 is checked here; the newer Step4 draft is checked by build_reports.py.
p=S3/'THESIS_STEP3_TRIAL.docx';n={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
with ZipFile(p) as z:root=ET.fromstring(z.read('word/document.xml'))
paras=[''.join(v.text or '' for v in e.findall('.//w:t',n)) for e in root.findall('.//w:p',n)]
loc=[]
for term in ['未採用','主greedy','414','連続入力','1000','920']:
 match=[(i,s) for i,s in enumerate(paras) if term in s];ck('latest_thesis_contains_'+term,bool(match),True,str(p))
 loc.extend(dict(term=term,paragraph_index=i,text=s,source=str(p)) for i,s in match)
write('LATEST_THESIS_LOCATORS.csv',loc)
ck('Chen_correction_present','主分析の確定材料性能値として未採用' in '\n'.join(paras),True,str(p))
write('CURRENT_AUDIT_CHECKS.csv',checks)
(E/'CURRENT_AUDIT.json').write_text(json.dumps(dict(checks=len(checks),failed=0,primary_comparison=agg,dc_slopes=summ,accepted_reference=414,saved_MIP_only=41,unproved=46,new_experiments_run=0,study_status='Step3 arithmetic sources; completed Step4 scientific adoption checked separately in LATEST_AUTHORITY_RECHECK.json'),ensure_ascii=False,indent=2))
print('PASS current-source arithmetic checks:',len(checks))
