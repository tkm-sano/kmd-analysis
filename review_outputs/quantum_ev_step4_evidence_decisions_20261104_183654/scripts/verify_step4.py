from pathlib import Path
import os,sys,json,csv,hashlib,time,math,collections,subprocess,shutil
from fractions import Fraction as F
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ[k]='1'
os.environ['PYTHONDONTWRITEBYTECODE']='1'
O=Path(__file__).resolve().parents[1];R=O.parents[1];U=Path('/home/takuma/kmd-analysis-pre-clean-20261102-112222/untracked');S2=R/'review_outputs/quantum_ev_step2_analysis_trial_20261104_155535';S3=R/'review_outputs/quantum_ev_step3_synthesis_trial_20261104_174309';W=R/'review_outputs/quantum_ev_thesis_step3_integration_20261104_173959';T8=U/'review_outputs/material_ev_stage2_20261026/run02';T9=U/'review_outputs/t09_open_data_model_20261029/run01';T6=U/'review_outputs/material_ev_stage1_20261024/run03'
import numpy as np,pandas as pd
checks=[];sources={};t0=time.perf_counter()
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def pin(p,role,locator=''):
 p=Path(p).resolve();assert p.is_file(),p
 if str(p)not in sources:sources[str(p)]=dict(path=str(p),sha256=sha(p),bytes=p.stat().st_size,role=role,locator=locator)
 return p
def ck(name,ok,detail=''):
 checks.append(dict(check=name,pass_=bool(ok),detail=str(detail)))
 if not ok:raise AssertionError((name,detail))
def js(p,role='保存一次成果物'):
 return json.load(pin(p,role).open())
def frame(p,role='保存数値出力'):return pd.read_csv(pin(p,role))
# Historical adoption, where a task status PASS is not input adoption.
review=pin(U/'docs/research/EV_QUANTUM_APPLICABILITY_BASELINE_REVIEW_20261023.md','2026-10-23主設計入力採用保留','§5.1,§6,§7,§10.2,実行ゲート')
pin(U/'docs/research/MATERIAL_EV_STAGE1_20261024.md','Stage1採否運用仕様','材料台帳の採否')
for name in ['REPORT.md','ARTIFACT_MANIFEST.json']:
 p=T6.parent/name
 if p.is_file():pin(p,'Stage1 run版の履歴')
reg=js(T6/'T06.json');ck('T06 task status PASS not input adoption',reg['status']=='PASS' and all(x['adoption']=='HOLD'for x in reg['records']))
sc=js(T8/'SCENARIOS.json');adopt=[]
for s in sc['scenarios']:
 for k,v in s['parameters'].items():
  adopt.append(dict(scenario_id=s['scenario_id'],parameter=k,value=v['value'],unit=v['unit'],evidence_status=v['evidence_status'],adoption=v['adoption'],basis=v['basis'],source=v['source']))
ck('All T08 numeric parameter adoption remains HOLD',all(x['adoption']=='HOLD'for x in adopt))
t7=js(T8/'T07.json');t8=js(T8/'T08.json');ck('T07 numerical PASS scientific HOLD',t7['status']=='PASS'and t7['scientific_adoption']=='ALL_HOLD');ck('T08 numerical PASS scientific HOLD',t8['status']=='PASS'and str(t8['scientific_adoption']).startswith('HOLD'))
for name in ['T12.json','T13.json','T14.json','RUN_START.json','RUN_END.json','MATERIAL_COMPONENTS.csv','MATERIAL_ENERGY.csv','TRANSMISSION.csv']:
 pin(T8/name,'T08条件付き実行・出力の一次記録')
for name in ['T09_FINAL_ACCEPTANCE.md','RUN_CONFIG.json','PARAMETER_SOURCES.csv','PACK_20KWH_SENSITIVITY.csv','CELL_MASS_ACCOUNTING_MODEL.md','VERIFICATION.json','model.py','analyze.py','T09_ACCEPTANCE_MATRIX.csv']:
 pin(T9/name,'T09構造モデルと未達受入記録')
# Re-extract original paper, not a summary of a summary.
pdf=pin(U/'review_outputs/causal_engineering_audit_20261027/run01/SOURCES/chen2020.pdf','Chen2020原著PDF','Fig5g pp7–8;Methods pp10–11')
ck('Copied original paper byte-identical',sha(pdf)==sha(O/'evidence/CHEN2020_PRIMARY.pdf'))
text=(O/'evidence/CHEN2020_REEXTRACTED.txt').read_text()
for token in ['70.4%','99.0%','121 mA','194','7.5:1.5:1','CR2025','lithium foil','room temperature','VASP']:
 ck('Primary paper text '+token,token in text)
# Fraction arithmetic from the executed (rounded) q references.
p=sc['scenarios'][0]['parameters'];sp=sc['scenarios'][1]['parameters'];ql=F(str(p['q_ref']['value']));qs=F(str(sp['q_ref']['value']));ck('LP derived q',ql==F(121)/F('.704'));ck('S executed q six decimals',qs==F('195.959596'))
E=F(str(p['gross_energy']['value']));V=F(str(p['voltage']['value']));qn=F(str(p['q_negative']['value']));r=F(str(p['np_ratio']['value']));fp=F(str(p['f_positive']['value']));fn=F(str(p['f_negative']['value']));fixed=F(100)*F(str(p['cell_other_mass']['value']))+F(str(p['pack_other_mass']['value']))
def mass(q,u=F(1),voltage=V):return E/voltage*(1/(q*u*fp)+r/(qn*fn))+fixed
ml=mass(ql);ms=mass(qs);b=ml-ms;ustar=ql/qs;vstar=E*(1/(qs*fp)+r/(qn*fn))/(ml-fixed)
ck('T08 saved LP mass',abs(float(ml)-t8['budgets']['COND_LP_REF']['pack_mass_kg'])<1e-10);ck('T08 saved S mass',abs(float(ms)-t8['budgets']['COND_S200_REF']['pack_mass_kg'])<1e-10)
bound=frame(S2/'PATH2_BOUNDARY_ANALYSIS.csv')
for cid,val in [('T08_DEFAULT_MASS',b),('T08_DEFAULT_UTILIZATION',ustar),('T08_DEFAULT_VOLTAGE',vstar)]:ck('T08 exact saved boundary '+cid,abs(float(val)-bound.loc[bound.condition_id==cid,'boundary_value'].iloc[0])<1e-10)
# T09 component model independent restatement of the executed accounting.
def comp(q,policy):
 Q=E/V;mp=Q/q;pc=mp/fp;nc=Q*r/qn/fn;area=(mp if policy=='fixed_loading'else Q/ql)/F('.1')
 return dict(positive_coating=pc,negative_coating=nc,Al=area/2*F('15e-6')*2699,Cu=area/2*F('10e-6')*8960,separator=area*F('.013275'),liquid=(pc/4458*F('.25')/F('.75')+nc/2200*F('.25')/F('.75')+area*F('25e-6')*F('.41'))*1300)
t9s=frame(S2/'PATH2_T09_COMMON_INPUT_SENSITIVITY.csv');t9b={}
for policy in ['fixed_loading','fixed_area_LP']:
 x=sum(comp(ql,policy).values())-sum(comp(qs,policy).values());row=t9s[(t9s.policy==policy)&(t9s.uS==1)&(t9s.V_common==3.5)].iloc[0];ck('T09 saved known difference '+policy,abs(float(x)-row.b_known_kg)<1e-10);t9b[policy]=float(x)
for col in ['complete_pack_mass_LP_kg','complete_pack_mass_S_kg']:ck('T09 162 complete mass null '+col,t9s[col].isna().all())
originalt9=frame(T9/'PACK_20KWH_SENSITIVITY.csv');nullcols=[c for c in originalt9.columns if 'complete_pack' in c];ck('Original T09 complete pack null',len(originalt9)==183 and bool(nullcols)and all(originalt9[c].isna().all()for c in nullcols))
# A compatibility check is conditional on T09 transferred foil/separator parameters, not a universal infeasibility theorem.
lowloading=[]
for name,q in [('LP',ql),('S200',qs)]:
 for load in [F('.01'),F('.02')]:
  area=E/V/q/load;al=area/2*F('15e-6')*2699;sep=area*F('.013275');lowloading.append(dict(material=name,loading_kg_m2=float(load),face_area_m2=float(area),Al_kg=float(al),separator_kg=float(sep),Al_plus_separator_kg=float(al+sep),T08_all_other_cell_parts_kg=19,exceeds_19kg=al+sep>19,scope='Chen reported loading plus transferred T09 foil and separator assumptions; not actual Chen foil specification'))
ck('Conditional low-loading compatibility issue',all(x['exceeds_19kg']for x in lowloading))
# Primary path1 CSVs, distinct from material validity.
paired=frame(S2/'PATH1_PAIRED_COMPARISONS.csv');main=paired[paired.primary_comparison];ck('36800 main plans feasible and no improvement',len(main)==36800 and main.feasible.all()and not main.improves.any()and main.problem_id.nunique()==460)
for row in main.itertuples():ck('Main DeltaJ Fraction',F(row.JC_fraction)-F(row.JQ_fraction)==F(row.delta_J_fraction),row.problem_id)
g=main[(main.scale=='R5')&(main.config_id=='GROVER_P2')].groupby('problem_id').delta_J_s.mean();r5=dict(mean_s=g.mean(),sd_s=g.std(ddof=1),n=len(g))
refs=frame(S2/'EXACT_REFERENCE_STATUS.csv');rc=refs.reference_evidence_class.value_counts().to_dict();ck('Reference evidence stratification',len(refs)==460 and refs.accepted_exact_available.sum()==414 and rc['SAVED_EXACT_MIP_EQUALITY_NO_EXTERNAL_VIPR']==41 and rc['UNPROVED_VALID_BOUNDS']==46)
raw=frame(S2/'experiments/QAOA_MAIN_MEASUREMENTS.csv');ck('Controlled measurements count',len(raw)==93120);sel=raw[(raw.problem_id=='R1_020')&(raw.support=='FULL_PERMUTATION')&(raw.initial_state=='BASIS_INITIAL')&(raw.mixer=='GRAPH_SWAP')&(raw.method=='QAOA')&(raw.measurement_rep==0)]
w=[]
for layer,num in [(1,58),(2,78)]:
 rr=sel[sel.layers==layer];k=int(rr.optimal_match.sum());n=len(rr);z=1.959963984540054;ph=k/n;den=1+z*z/n;center=(ph+z*z/(2*n))/den;half=z*math.sqrt(ph*(1-ph)/n+z*z/(4*n*n))/den;ck('Raw optimal attainment p'+str(layer),k==num and n==97);w.append(dict(layer=layer,k=k,n=n,lower=center-half,upper=center+half))
ck('Controlled no main improvement',not raw.improves_greedy.any());runtime=frame(S2/'PATH1_RUNTIME_RESULTS.csv');ck('Runtime row count',len(runtime)==9603)
pin(S2/'scripts/controlled_qaoa.py','追加統制の実装、誤解しやすい確率列名の意味');pin(S2/'PATH1_SUPPORT_AUDIT.csv','mirror/active支持診断');pin(S2/'PATH1_UNCERTAINTY_INTERVALS.csv','group補助感度区間');pin(S2/'PATH1_REFERENCE_STRENGTH_SENSITIVITY.csv','373強化参照の層別感度')
# Endpoint aggregation still depends on Chen-derived mass, regardless of correct arithmetic.
op=frame(S2/'PATH2_OPERATION_CONDITION_ANALYSIS.csv');end=[]
for case,gg in op.groupby('rolling_case'):
 ck('Endpoint all mass difference matches q-derived b',np.max(np.abs(gg.delta_mass_kg-float(b)))<1e-10)
 end.append(dict(rolling_case=case,n=len(gg),sum_ratio_percent=100*gg.delta_DC_Wh.sum()/gg.baseline_DC_Wh.sum(),mean_rate_percent=gg.individual_saving_percent.mean(),sd_pp=gg.individual_saving_percent.std(ddof=1)))
pin(S2/'scripts/path2_analysis.py','全格子・T09・運転層別のq依存を確認','mass,t09,main qLP/qS import')
for f in ['PATH2_SENSITIVITY_SUMMARY.csv','PATH2_GROUP_SENSITIVITY_INTERVALS.csv','PATH2_OPERATION_STRATA.csv']:pin(S2/f,'Chen依存参考結果、科学的採用とは別')
# Material-free physical kernel check at declared mass endpoints. No qLP/qS used here.
sys.path.insert(0,str(R/'src'));from kmd_quantitative.energy.controlled_dc import evaluate
freeze=js(R/'01_research_design/methodology/CONTROLLED_MASS_TO_DC_MODEL_FREEZE.json','物理定数と対象外境界の凍結仕様')
pin(R/'src/kmd_quantitative/energy/controlled_dc.py','不変核へのalias');pin(R/'src/kmd_quantitative/energy/frozen_sources/run_full_controlled_dc.py','凍結Controlled-DC科学核')
saved=frame(S3/'data/DC_MASS_KERNEL_INDEPENDENT.csv');dc=[]
for h,gg in saved.groupby('trajectory_sha256'):
 path=pin(gg.trajectory_path.iloc[0],'材料を使わない保存速度入力','timestamp_s,speed_m_s');ck('Saved trajectory SHA',sha(path)==h)
 d=pd.read_csv(path,usecols=['timestamp_s','speed_m_s']);t=d.timestamp_s.to_numpy();v=d.speed_m_s.to_numpy();ck('Trajectory contract',np.all(np.diff(t)==1)and np.isfinite(v).all()and np.all(v>=0));cur=v[1:];ds=cur*np.diff(t);dv=cur**2-v[:-1]**2
 for case,pressure in [('CRR_LOWER_BOUND',4.5),('CRR_UPPER_BOUND',2.6)]:
  rr=gg[gg.rolling_case==case].iloc[0];crr=.005+(.01+.0095*(3.6*cur/100)**2)/pressure;a=(9.80665*crr*ds+.5*dv)/3600;c=(.5*61*dv+.5*1.2041*1.175*cur**2*ds)/3600;z=a*1000+c;zh=a*1250+c;slope=(a[z>0].sum()+a[(z==0)&(a>0)].sum())/.9;high=(a[zh>0].sum()+a[(zh==0)&(a<0)].sum())/.9
  ck('Positive nondecreasing DC derivative',slope>0 and high>=slope-1e-10,h)
  for mass,zz,col in [(1000,z,'DC_lo_Wh'),(1250,zh,'DC_hi_Wh')]:
   e=np.maximum(zz,0).sum()/.9;actual,_=evaluate(t,v,freeze,pressure,{'running_mass_kg':mass});ck('Material-free affine versus frozen DC',abs(e-actual['net_DC_Wh'])<1e-7,h);ck('Saved Step3 material-free endpoint',abs(e-rr[col])<1e-7,h)
  ck('Saved Step3 material-free slope',abs(slope-rr.right_derivative_lo_Wh_kg)<1e-10,h)
  dc.append(dict(trajectory_sha256=h,rolling_case=case,mass_lo_kg=1000,mass_hi_kg=1250,right_derivative_lo_Wh_kg=slope,left_derivative_hi_Wh_kg=high,Chen_input_used=False))
# Final source selection records: both independent Step3 editions must be compared, not chosen by mtime.
for f in ['CHEN_2020_ADOPTION_CORRECTION.md','CHEN_DEPENDENCY_AUDIT.csv','PATH2_MAIN_VS_REFERENCE_RESULTS.md','data/SOURCE_COPY_INTERPRETATION.md','STEP4_HANDOFF.md','STEP3_CLAIM_REGISTER.csv']:pin(S3/f,'Step3補正済み解釈版（上流一次証拠と照合）')
for f in ['CLAIM_EVIDENCE_LEDGER.csv','FINAL_AUDIT_REPORT.md','THESIS_SECTIONS_TRIAL.md','NUMERICAL_AUDIT_RESULT.json','NUMERICAL_AUDIT_CHECKS.csv','scripts/audit_evidence.py']:pin(W/f,'別Step3 Word統合版の既存採用表記・数値監査（科学的入力採用は再判定）')
def savecsv(name,data):
 with(O/name).open('w',newline='')as f:w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
savecsv('evidence/VERIFICATION_CHECKS.csv',checks);savecsv('evidence/T08_PARAMETER_ADOPTION.csv',adopt);savecsv('evidence/LOW_LOADING_COMPATIBILITY.csv',lowloading);savecsv('evidence/DC_MATERIAL_FREE_RECHECK.csv',dc);savecsv('evidence/SOURCE_LEDGER.csv',list(sources.values()))
summary=dict(checks=len(checks),failures=sum(not x['pass_']for x in checks),wall_s=time.perf_counter()-t0,LP_q_inverse=float(ql),S_q_exact_inverse=float(F(194)/F('.99')),S_q_executed=float(qs),LP_mass=float(ml),S_mass=float(ms),T08_b_kg=float(b),u_boundary=float(ustar),V_boundary=float(vstar),T09_known_b=t9b,R5=r5,reference_classes=rc,controlled_Wilson=w,C_endpoint=end,DC_material_free={case:dict(n=len(gg),min_slope_Wh_kg=gg.right_derivative_lo_Wh_kg.min())for case,gg in pd.DataFrame(dc).groupby('rolling_case')},new_scientific_experiments=0)
(O/'evidence/VERIFICATION_RESULT.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2));print(json.dumps(summary,ensure_ascii=False,indent=2))
