from pathlib import Path
import pandas as pd,json,hashlib,math,shutil
from fractions import Fraction as F
O=Path(__file__).resolve().parents[1];R=O.parents[1];S2=R/'review_outputs/quantum_ev_step2_analysis_trial_20261104_155535';S1=R/'review_outputs/quantum_ev_step1_design_trial_20261104_153058';sources={};checks=[]
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def pin(p,expected=None):
 p=Path(p);assert p.is_file(),p;h=sha(p)
 if expected:assert h==expected,(p,h,expected)
 sources[str(p)]={'path':str(p),'sha256':h,'bytes':p.stat().st_size,'mtime_ns':p.stat().st_mtime_ns,'version':'content SHA256; prior trial frozen version'};return p
def df(p):return pd.read_csv(pin(p),keep_default_na=False,low_memory=False)
def ck(n,v):checks.append(dict(check=n,status='PASS' if v else 'FAIL'));assert v,n
# Read and hash every Step2 artifact rather than inheriting its closure report.
for x in pd.read_csv(S2/'OUTPUT_SHA256_MANIFEST.csv').to_dict('records'):pin(S2/x['path'],x['sha256'])
# Preserve the older primary sources represented by Step2.
for x in pd.read_csv(S2/'SOURCE_PROVENANCE.csv').to_dict('records'):pin(x['path'],x['final_sha256'])
for p in S1.glob('*'):
 if p.is_file() and p.suffix in ['.md','.csv','.json']:pin(p)
for n in ['README.md','EXECUTIVE_SUMMARY.md','STEP3_HANDOFF.md','STATISTICAL_METHODS.md','PATH1_STATISTICAL_REPORT.md','PATH1_UNCERTAINTY_ANALYSIS.md','QAOA_CONTROLLED_EXPERIMENT_REPORT.md','PATH1_RUNTIME_SCOPE_COMPARISON.md','PATH2_MODEL_UNCERTAINTY.md','PATH2_STATISTICAL_REPORT.md','STATISTICAL_VALIDITY_AUDIT.md','UNRESOLVED_ITEMS.md','FINAL_AUDIT_REPORT.md']:(O/'evidence'/('S2_'+n)).write_text(pin(S2/n).read_text())
p=df(S2/'PATH1_PAIRED_COMPARISONS.csv');p=p[p.primary_comparison];ck('B unique36800 PK',len(p)==36800 and not p.duplicated(['problem_id','config_id','measurement_rep']).any());ck('B460x8x10 and feasible',p.problem_id.nunique()==460 and p.config_id.nunique()==8 and p.groupby(['problem_id','config_id']).size().eq(10).all() and p.feasible.all());ck('primary strict improvement0',all(F(x)<=0 for x in p.delta_J_fraction));ck('delta sign equation',all(F(c)-F(q)==F(d) for c,q,d in zip(p.JC_fraction,p.JQ_fraction,p.delta_J_fraction)))
g=p[(p.scale=='R5')&(p.config_id=='GROVER_P2')].groupby('problem_id').delta_J_s.mean();ck('R5 mean and SD',len(g)==70 and abs(g.mean()+5983.70645268941)<1e-8 and abs(g.std(ddof=1)-1314.3645367770923)<1e-8)
support=df(S2/'PATH1_SUPPORT_AUDIT.csv');ck('460mirror orbit equals initial',len(support)==460 and support.matching_orbit_min_equals_initial.all());ck('greedy<=initial all plans',all(F(c)<=F(i) for c,i in zip(p.JC_fraction,p.initial_fraction)))
ref=df(S2/'EXACT_REFERENCE_STATUS.csv');ck('414 references46 missing41MIP',ref.exact_fraction.ne('').sum()==414 and ref.exact_fraction.eq('').sum()==46 and (ref.reference_evidence_class=='SAVED_EXACT_MIP_EQUALITY_NO_EXTERNAL_VIPR').sum()==41)
c=df(S2/'QAOA_CONTROLLED_CELL_SUMMARY.csv');fit=df(S2/'QAOA_CONTROLLED_EXPERIMENT_RESULTS.csv');ck('9312fits96cells97starts',len(fit)==9312 and len(c)==96 and c.independent_learning_fits.eq(97).all())
for depth,k in [(1,58),(2,78)]:
 x=c[(c.problem_id=='R1_020')&(c.support=='FULL_PERMUTATION')&(c.initial_state=='BASIS_INITIAL')&(c.mixer=='GRAPH_SWAP')&(c.layers==depth)&(c.method=='QAOA')].iloc[0];ck('controlled k97 p'+str(depth),x.primary_optimal_rep0_count==k)
 z=1.959963984540054;n=97;ph=k/n;den=1+z*z/n;h=z*math.sqrt(ph*(1-ph)/n+z*z/(4*n*n))/den;mid=(ph+z*z/(2*n))/den;ck('Wilson interval recomputation p'+str(depth),abs(x.primary_optimal_Wilson95_lower-(mid-h))<1e-12)
energy=df(S2/'PATH2_SENSITIVITY_RESULTS.csv');end=energy[(energy.model=='T08')&(energy.case_id=='Q48')];summary=df(S2/'PATH2_SENSITIVITY_SUMMARY.csv');out=[]
for rc,h in end.groupby('rolling_case'):
 ratio=100*math.fsum(h.delta_DC_Wh)/math.fsum(h.baseline_DC_Wh);mean=h.individual_saving_percent.mean();sd=h.individual_saving_percent.std(ddof=1);stored=summary[(summary.model=='T08')&(summary.case_id=='Q48')&(summary.rolling_case==rc)].iloc[0];ck('920 paired energy aggregation '+rc,len(h)==460 and abs(ratio-stored.total_weighted_saving_percent)<1e-10);out.append(dict(Crr=rc,n=460,total_ratio_percent=ratio,individual_mean_percent=mean,individual_SD_pp=sd))
qL=F('171.875');qS=F('195.959596');mass=lambda q,u=F(1),V=F('3.5'):20000/V*(1/(q*u*F('.75'))+F('1.1')/(360*F('.98')))+34
b=mass(qL)-mass(qS);u=qL/qS;V=20000*(1/(qS*F('.75'))+F('1.1')/(360*F('.98')))/(mass(qL)-34);ck('T08 mass/capacity/voltage boundaries',abs(float(b)-5.448297415076934)<1e-12 and abs(float(u)-.8770940719841043)<1e-15 and abs(float(V)-3.193155683779789)<1e-14)
ck('DC zero at mass cancellation',energy[(energy.model=='T08')&(energy.case_id=='CANCEL+0')].delta_DC_Wh.abs().max()<1e-10)
op=df(S2/'PATH2_OPERATION_CONDITION_ANALYSIS.csv');ck('positive slope920 in range1000to1250',len(op)==920 and (op.min_derivative_Wh_kg>0).all());t9=df(S2/'PATH2_T09_COMMON_INPUT_SENSITIVITY.csv');ck('T09 completed pack NULL',t9.complete_pack_mass_LP_kg.eq('').all() and t9.complete_pack_mass_S_kg.eq('').all())
# Pin source code and actual execution logs for traceability, not only narrative reports.
for name in ['path1_statistics.py','controlled_qaoa.py','path2_analysis.py','support_and_verification.py','exact_recheck.py']:pin(S2/'scripts'/name)
for name in ['path1_statistics.log','qaoa_main.log','path2_analysis.log','exact_full.log']:pin(S2/'logs'/name)
pd.DataFrame(sources.values()).to_csv(O/'STEP3_SOURCE_MANIFEST.csv',index=False);pd.DataFrame(checks).to_csv(O/'evidence/NUMERICAL_RECHECK.csv',index=False);pd.DataFrame(out).to_csv(O/'data/DC_ENDPOINT_RECHECK.csv',index=False)
(O/'evidence/VERIFIED_VALUES.json').write_text(json.dumps({'B_inputs':460,'B_plans':36800,'positive_improvements':0,'R5_mean_delta_s':g.mean(),'R5_input_SD_s':g.std(ddof=1),'T08_b_kg':float(b),'u_boundary':float(u),'V_boundary':float(V),'checks':len(checks),'source_files':len(sources)},indent=2))
for name in ['PATH1_STATISTICAL_RESULTS.csv','QAOA_CONTROLLED_CELL_SUMMARY.csv','PATH1_RUNTIME_SUMMARY.csv','PATH2_SENSITIVITY_SUMMARY.csv','PATH2_BOUNDARY_ANALYSIS.csv','PATH2_T09_COMMON_INPUT_SENSITIVITY.csv','PATH2_OPERATION_STRATA.csv','CONTRIBUTION_CONDITION_TABLE.csv','PATH1_UNCERTAINTY_INTERVALS.csv','PATH2_GROUP_SENSITIVITY_INTERVALS.csv']:shutil.copyfile(S2/name,O/'data'/name)
print((O/'evidence/VERIFIED_VALUES.json').read_text())
