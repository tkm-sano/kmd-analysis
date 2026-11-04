"""Independent readback of editorial figures/tables and protected source hashes.
No imports of primary analysis, plotting or drafting code.
"""
from evidence import *
from fractions import Fraction as Q
from PIL import Image
import pandas as pd
import numpy as np

def main():
 t=time.monotonic();checks=[]
 def ck(name,expected,actual,tol=0,locator=''):
  ok=abs(float(expected)-float(actual))<=tol if isinstance(expected,(int,float,Q)) and isinstance(actual,(int,float,Q)) else expected==actual
  checks.append({'check':name,'expected':str(expected),'actual':str(actual),'tolerance':tol,'locator':locator,'status':'PASS' if ok else 'FAIL'})
 p=pd.read_csv(use(F/'A_POLICY_DECISIONS_2808.csv'));s=pd.read_csv(use(F/'A_DELIVERY_COMPLETION_BY_STOP.csv'));ar=pd.read_csv(use(F/'A_MECHANISM_COMPARISON.csv'));a=pd.read_csv(use(F/'A_SUMMARY_BY_CONDITION.csv'))
 ck('A policy route changes drawn105',105,int(p.route_changed_vs_C.sum()));ck('A conditions with64quantum',21,int((a.quantum_adopted==64).sum()));ck('A per condition denominator556',True,bool((a.denominator_PE==556).all()));ck('A policy stop refs',11232,int((s.comparison_scope=='POLICY78').sum()));ck('A unavailable arms',1920,int((~ar.availability_feasible).sum()))
 # Reaggregate plotted mechanism lines directly from arm rows, independent of summary.
 for cid,rr in ar.groupby('condition_id'):
  means=rr.groupby('arm').mean_completion_s.mean();plot=pd.read_csv(O/'tables/F5_4_PLOT_DATA.csv').set_index('condition_id').loc[cid]
  for arm in ['QC','CQ','QQ']:ck('A mechanism plotted delta',means[arm]-means['CC'],float(plot[arm+'-CC']),1e-9,cid+arm)
 # Independent per-condition summation of policy pair differences.
 pa=pd.read_csv(use(F/'A_PAIRED_PER_PROBLEM.csv'));pa=pa[pa.series_id=='A_POLICY']
 for x in a.itertuples():
  rr=pa[pa.condition_id==x.condition_id];ck('A policy mean result',float(rr.delta_mean_completion_s.mean()),x.delta_mean_completion_s,1e-9,x.condition_id)
 # Fixed-OD waiting readback can be verified using a relational self-join.
 ss=s[(s.comparison_scope=='MECHANISM64')&s.arm.isin(['CC','CQ'])];left=ss[ss.arm=='CC'];right=ss[ss.arm=='CQ'];m=left.merge(right,on=['condition_id','problem_id','task_id','stop_order'],suffixes=('_C','_Q')).sort_values(['condition_id','problem_id','stop_order']);m['absorbed']=m.waiting_s_C-m.waiting_s_Q;m['cumulative']=m.groupby(['condition_id','problem_id']).absorbed.cumsum();ww=pd.read_csv(O/'tables/A_WAIT_ABSORPTION_BY_STOP.csv').sort_values(['condition_id','problem_id','stop_order']);ck('A wait plotted accounting rows',len(m),len(ww));ck('A waiting independent max residual',0,float(np.max(np.abs((m.complete_s_Q-m.complete_s_C).to_numpy()-ww.completion_change_s.to_numpy()))),1e-8)
 b=pd.read_csv(use(F/'B_PLAN_REFERENCES_36800.csv'));sm=pd.read_csv(O/'tables/T5-1_B_OBJECTIVE.csv');ck('B full references',36800,len(b));cov=pd.read_csv(use(F/'B_EXACT_REFERENCE_COVERAGE.csv'));ck('B global reference inputs',407,int(cov.exact_reference_available.sum()));ck('B missing gaps',4240,int(b.global_gap_percent.isna().sum()))
 for x in sm.itertuples():
  rr=b[(b.scale==x.scale)&(b.config_id==x.config_id)];per=rr.groupby('problem_id').delta_objective_vs_initial_s.mean();ck('B plotted source mean',float(per.mean()),x.mean_delta_objective_s,1e-8,x.scale+x.config_id)
 for cfg in ['GROVER_P2','GROVER_P3']:
  rr=b[b.config_id==cfg];ck('B improved input count7',7,len(rr[rr.improves_initial].problem_id.unique()));ck('B improv70',70,int(rr.improves_initial.sum()))
 # Four representative T09 rows: separate rational arithmetic, no primary evaluator.
 rr=rows(F/'C_T09_COMPONENTS_183.csv');out=[]
 for n in [30,31,102,103]:
  x=rr[n];f=lambda k:Q(x[k]);charge=f('gross_design_Wh')/f('mean_voltage_design_V');cp=charge/(f('q_reference_Ah_kg')*f('positive_utilization')*Q('.75'));cn=charge*f('NP_after_formation')/(f('negative_q_Ah_kg')*(1-f('negative_unavailable_fraction'))*Q('.98'));ap=f('positive_face_area_m2');an=f('negative_face_area_m2');ep=f('positive_porosity');en=f('negative_porosity');total=cp+cn+ap*f('Al_thickness_m')*2699/2+an*f('Cu_thickness_m')*8960/2+max(ap,an)*f('separator_areal_mass_kg_m2')+(cp/Q(4458)*ep/(1-ep)+cn/Q(2200)*en/(1-en)+max(ap,an)*Q('.000025')*Q('.41')+f('extra_liquid_volume_m3'))*1300
  ck('C representative known mass independent',f('known_sum_recalculated_kg'),total,1e-8,x['condition_id']);out.append({'condition_id':x['condition_id'],'source_row':x['source_row'],'LP_or_S':x['material'],'known_mass_independent_kg':float(total),'source_sum_kg':x['known_sum_recalculated_kg'],'status':'PASS_CONDITIONAL_COMPONENT_ACCOUNTING'})
 ck('C loading boundary',9.722608121107783,out[0]['known_mass_independent_kg']-out[1]['known_mass_independent_kg'],1e-8);ck('C area boundary',5.977891152148871,out[2]['known_mass_independent_kg']-out[3]['known_mass_independent_kg'],1e-8);table('tables/C_REPRESENTATIVE_INDEPENDENT_COMPONENTS.csv',out)
 qLP=Q('171.875');qS=Q('195.959596');delta=Q(20000)/Q('3.5')*(1/qLP-1/qS)/Q('.75');ck('C T08 independent mass difference',5.448297415076922,delta,1e-9)
 bridge=pd.read_csv(use(F/'C_BRIDGE_MASS_DC_FULL.csv'));ck('C algebraic b-delta',0,float(np.max(np.abs(bridge.known_mass_boundary_kg-bridge.unknown_mass_difference_probe_kg-bridge.net_mass_saving_probe_kg))),1e-10)
 # Each bridge plotting point has the actual original 460-row denominator.
 bp=pd.read_csv(O/'tables/FA_1_PLOT_DATA.csv')
 for x in bp.itertuples():
  z=bridge[(bridge.design_policy==x.design)&(bridge.reference_running_mass_kg==x.mass_kg)&(bridge.rolling_case==x.rolling_case)&(bridge.unknown_mass_difference_probe_kg==x.unknown_mass_difference_probe_kg)];ck('C bridge plotted denominator',460,len(z));ck('C bridge plotted rate',100*math.fsum(z.recomputed_saving_Wh)/math.fsum(z.recomputed_baseline_DC_Wh),x.weighted_percent,1e-10,str(x.Index))
 ints=rows(F/'CLUSTER_SENSITIVITY_INTERVALS.csv');ck('statistics1176',1176,len(ints));ck('statistics group unit',True,all('25_SOURCE' in x['cluster_unit'] for x in ints));ck('statistics no tests',True,all(x['test_count']=='0' for x in ints));ck('statistics 10000 resamples',True,all(x['resamples']=='10000' for x in ints))
 fm=rows(O/'FIGURE_SOURCE_MAPPING.csv');ck('figures ten',10,len(fm))
 for x in fm:
  for f in x['files'].split(';'):
   pth=O/f;ck('figure exists',True,pth.is_file(),locator=f)
   if pth.suffix=='.png':
    with Image.open(pth) as im:im.verify()
   if pth.suffix=='.svg':ck('SVG outlined Japanese glyphs',True,'<path' in pth.read_text(),locator=f)
 for name,count in [('TA-1_ALL_36_POLICIES.csv',36),('T5-1_B_OBJECTIVE.csv',48),('T5-2_B_EXACT.csv',48),('T5-4_T08_DC.csv',2),('TA-2_C_BRIDGE.csv',56),('TA-3_SUPPLEMENT_INTERVALS.csv',1176)]:ck('table expected rows '+name,count,len(rows(O/'tables'/name)))
 # Compare all read original files to hashes pinned when first read, not generated outputs.
 pinned={}
 for q in O.glob('*_SOURCES.json'):
  for x in json.loads(q.read_text()):
   if not Path(x['path']).is_relative_to(O):pinned[x['path']]=x
 for x in rows(O/'BASELINE_PINNED_SOURCES.csv'):
  if not Path(x['path']).is_relative_to(O):pinned[x['path']]=x
 protected=[]
 for pth,x in sorted(pinned.items()):
  actual=sha(pth);protected.append({'path':pth,'expected_sha256':x['sha256'],'final_sha256':actual,'status':'PASS_UNCHANGED' if actual==x['sha256'] else 'FAIL_CHANGED'});ck('protected SHA unchanged',x['sha256'],actual,locator=pth)
 table('PRESERVATION_CHECKS.csv',protected);initial=js(O/'INITIAL_STATE.json');diff=subprocess.check_output(['git','diff','HEAD','--binary'],cwd=R,text=True);ck('tracked git diff unchanged',initial['git_diff'],diff);ck('HEAD unchanged',initial['HEAD'],subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip());ck('DOCX unchanged',initial['docx_sha256'],sha(DOC));(O/'GIT_DIFF_FINAL.patch').write_text(diff);(O/'GIT_STATUS_FINAL.txt').write_text(subprocess.check_output(['git','status','--short'],cwd=R,text=True));table('PACKAGE_VALIDATION_CHECKS.csv',checks);fails=[x for x in checks if x['status']=='FAIL'];finish('PACKAGE_VALIDATION',t,{'checks':len(checks),'failures':len(fails),'protected_original_files':len(protected),'figures':len(fm),'scientific_runs':0,'docx_unchanged':sha(DOC)==initial['docx_sha256']})
 if fails:raise RuntimeError('Package validation FAIL')
if __name__=='__main__':main()
