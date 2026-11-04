from pathlib import Path
import os,sys,csv,json,hashlib,datetime,subprocess,collections,zipfile,xml.etree.ElementTree as ET
from fractions import Fraction as F
import numpy as np,pandas as pd
O=Path(__file__).resolve().parents[1];R=O.parents[1];P=R/'review_outputs/no_sumo_full_analysis_20261102/run01';T=R/'review_outputs/quantum_ev_conditions_full_trial_20261104_125659'
U=Path('/home/takuma/kmd-analysis-pre-clean-20261102-112222/untracked');S=U/'review_outputs/staged_qaoa_validation_20261102';T8=U/'review_outputs/material_ev_stage2_20261026/run02';T9=U/'review_outputs/t09_open_data_model_20261029/run01'
sources={};checks=[];relocations=[];HEAD=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R).decode().strip()
def use(p,role='source',expected=''):
 p=Path(p).resolve()
 if not p.is_file():
  original=p
  roots=[R,U,Path('/home/takuma/kmd-analysis-preservation-20261014-173544-a64e484c/backup'),Path('/home/takuma/kmd-analysis-preservation-20261014-173544-a64e484c/relocated')]
  candidates=[alt/p.relative_to(root) for root in roots if p.is_relative_to(root) for alt in roots]
  matches=[q for q in candidates if q.is_file()]
  assert matches,original
  p=matches[0].resolve();relocations.append({'recorded_path':str(original),'actual_path':str(p)})
 assert p.is_file(),p
 if str(p) not in sources:
  st=p.stat();sources[str(p)]={'path':str(p),'version':HEAD if p.is_relative_to(R) and str(p.relative_to(R)) in tracked else 'saved working copy; SHA256 is version identity','sha256':hashlib.file_digest(p.open('rb'),'sha256').hexdigest(),'bytes':st.st_size,'mtime_utc':datetime.datetime.fromtimestamp(st.st_mtime,datetime.timezone.utc).isoformat(),'role':role,'reference':role,'storage':'repository' if p.is_relative_to(R) else 'external preservation'}
 if expected:ck('hash matches stored source',sources[str(p)]['sha256']==expected,str(p))
 return p
def js(p,role='source'):return json.loads(use(p,role).read_text())
def df(p,role='source'):return pd.read_csv(use(p,role),keep_default_na=False,low_memory=False)
def out(n,v):
 p=O/n;p.parent.mkdir(exist_ok=True,parents=True)
 if isinstance(v,pd.DataFrame):v.to_csv(p,index=False)
 else:p.write_text(json.dumps(v,ensure_ascii=False,indent=2,default=str)+'\n')
def ck(k,v,where='',detail=''):checks.append({'check':k,'status':'PASS' if bool(v) else 'FAIL','source':where,'detail':str(detail)})
tracked=set(subprocess.check_output(['git','ls-files','-z'],cwd=R).decode().split('\0'))
# Pin primary narrative/implementation versions and source snapshots before inspecting values.
for root in [R/'docs/research',R/'docs/thesis',R/'01_research_design/methodology',R/'src/kmd_quantitative',P,T]:
 for p in root.iterdir() if root in [P,T] else root.rglob('*'):
  if p.is_file() and p.suffix in ['.md','.csv','.json','.py','.tex'] and '__pycache__' not in p.parts:use(p,'research design / existing result / implementation')
for p in [R/'README.md',R/'docs/QUANTITATIVE_GUIDE.md',T8/'SCENARIOS.json',T8/'SENSITIVITY_INPUTS.json',T8/'T08.json',T8/'MATERIAL_ENERGY.csv',T9/'model.py',T9/'analyze.py',T9/'RUN_CONFIG.json',T9/'PARAMETER_SOURCES.csv',T9/'PACK_20KWH_SENSITIVITY.csv',T9/'CELL_MASS_ACCOUNTING_MODEL.md',T9/'ELECTRODE_GEOMETRY_MODEL.md',T9/'VERIFICATION_REPORT.md',S/'ENVIRONMENT.json',R/'review_outputs/poster_policy_revision_20261104/run03/01_POLICY_AND_SCOPE.txt']:use(p)
for family in ['mirror_family','grover_depth','active_adjacent_p3']:
 for p in (S/family/'SOURCE_SNAPSHOT').rglob('*.py'):use(p,'frozen execution source')
 for n in ['PROTOCOL.json','SOURCE_HASHES.json']:use(S/family/n,'algorithm frozen protocol')
# AGENTS discovery: ancestor files and repo scan pruning environments/tools; record actual absence.
ag=[]
for parent in [R,*R.parents]:
 p=parent/'AGENTS.md'
 if p.is_file():ag.append(str(use(p)))
for root,ds,fs in os.walk(R):
 ds[:]=[d for d in ds if d not in ['.git','.conda','.venv','tools','rendering_tools','lo_root','node_modules','__pycache__'] and Path(root)/d!=O]
 if 'AGENTS.md' in fs:ag.append(str(use(Path(root)/'AGENTS.md')))
out('evidence/AGENTS_DISCOVERY.json',{'found':sorted(set(ag)),'excluded':'environment and third-party tool directories'})
plans=df(P/'B_PLAN_REFERENCES_36800.csv');fits=df(P/'B_RESOURCES_PER_FIT.csv');cov=df(P/'B_EXACT_REFERENCE_COVERAGE.csv');bases=df(P/'B_CLASSICAL_INITIAL_BASELINES.csv');aux=df(P/'B_AUXILIARY_CLASSICAL_IMPROVEMENTS.csv')
meta={x['run_id']:x for x in js(S/'mirror_family/MANIFEST.json')};arrays={};raw={};maxerr=0.;mis=0;rawmis=0;valid=0;exactmis=0
for pid in plans.problem_id.unique():
 m=meta[pid];p=use(m['instance_path'],'B original NPZ',m['instance_sha256'])
 with np.load(p,allow_pickle=False) as z:arrays[pid]={k:z[k].copy() for k in z.files}
for x in plans.to_dict('records'):
 k=x['source_path']
 if k not in raw:
  use(k,'B saved measurement',x['source_sha256']);d=js(k);raw[k]={int(v['rep']):v for v in d['records'] if v.get('mode','OPTIMIZED')=='OPTIMIZED'}
 rec=raw[k][int(x['measurement_rep'])];rt=json.loads(x['route_indices']);a=arrays[x['problem_id']]
 score=sum((F(str(a['travel'][i,j])) for i,j in zip(rt,rt[1:])),F(0));err=abs(float(score)-float(x['objective_s']));maxerr=max(maxerr,err);mis+=score!=F(x['objective_fraction']);rawmis+=score!=F(str(rec.get('sampled_best_seconds',rec.get('road_seconds')))) or rt!=rec['route_indices'];valid+=rt[0]==rt[-1]==0 and sorted(rt[1:-1])==list(range(1,len(a['travel']))) and float(np.sum(a['demand']))<=216 and float(score)+102*int(x['n_customers'])<=32400
 if x['exact_optimum_fraction']!='':exactmis+=abs(float(x['global_gap_percent'])-100*float((score-F(x['exact_optimum_fraction']))/F(x['exact_optimum_fraction'])))>1e-9
ck('B size and unique PK',len(plans)==36800 and not plans.duplicated(['problem_id','config_id','measurement_rep']).any());ck('B input settings reps',plans.groupby('problem_id').size().eq(80).all() and plans.groupby(['problem_id','config_id']).size().eq(10).all());ck('B exact rational objective from NPZ',mis==0,detail=mis);ck('B raw route and objective agreement',rawmis==0,detail=rawmis);ck('B all saved best plans feasible',valid==36800,detail=valid);ck('B existing global gap arithmetic',exactmis==0,detail=exactmis)
# Actual certificates: distinguish exact status and specific termination, never impute.
coverage=[]
for x in cov.to_dict('records'):
 p=use(x['certificate_path'],'B exact/reference certificate',x['certificate_sha256']);d=js(p);available=str(x['exact_reference_available'])=='True';n=meta[x['problem_id']]['n']
 ck('B saved certificate exact availability',available==(d.get('exact_optimum_seconds') is not None),str(p))
 aa=aux[aux.problem_id==x['problem_id']]
 coverage.append({**x,'n_customers':n,'classical_initial_available':True,'classical_approximation_methods':';'.join(sorted(aa.method.unique())),'classical_approximation_rows':len(aa),'current8_runtime_budget_matched':False,'certificate_termination':d.get('termination',''),'proved_optimal':d.get('proved_optimal',''),'time_limit_reached':d.get('time_limit_reached',''),'specific_missing_reason':'' if available else d.get('termination','NO_PROVED_EXACT_REFERENCE'),'affected_metrics':'' if available else 'global_optimality_gap;global_optimal_match','quality_pairing_status':'CONDITIONAL: same NPZ/objective; feasibility and current budget pairing to be frozen in Step2','missing_value_policy':'NULL; no imputation'})
out('PATH1_REFERENCE_COVERAGE.csv',pd.DataFrame(coverage))
ck('B exact references 407 missing 53',sum(str(x['exact_reference_available'])=='True' for x in coverage)==407 and len(coverage)==460)
for x in fits.to_dict('records'):use(x['fit_source_path'],'B fit timing',x['fit_source_sha256'])
for x in bases.to_dict('records'):use(x['source_path'],'B classical initial result')
for path,h in aux[['source_path','source_sha256']].drop_duplicates().itertuples(index=False,name=None):use(path,'classical approximate comparison',h)
# Verify published input-seed table independently; no inferential analysis performed.
st=df(T/'PATH1_INPUT_SEED_STATISTICS.csv');re=[];err=[]
for (pid,cfg),g in plans.groupby(['problem_id','config_id']):
 a=g.objective_s.astype(float).to_numpy();row=st[(st.problem_id==pid)&(st.config_id==cfg)].iloc[0];values={'n':len(a),'mean_objective_s':float(a.mean()),'sd_objective_s':0. if np.all(a==a[0]) else float(a.std(ddof=1)),'min_objective_s':float(a.min()),'max_objective_s':float(a.max())}
 for k,v in values.items():
  if abs(v-float(row[k]))>1e-8:err.append((pid,cfg,k,v,row[k]))
ck('Existing input-seed statistics reproduce',len(err)==0,str(T/'PATH1_INPUT_SEED_STATISTICS.csv'),f'{len(st)} rows; errors={len(err)}')
out('evidence/STATISTICS_READBACK.json',{'rows':len(st),'unit':'problem_id x config_id; ten measurement repetitions of one fit','formula':'mean, sample SD ddof1 (constant arrays forced0), min,max','errors':err,'missing_handling':'objective rows complete; exact-reference missing not represented by this table'})
out('evidence/B_SCALE_COUNTS.csv',plans.groupby(['scale','n_customers']).agg(inputs=('problem_id','nunique'),saved_plan_references=('problem_id','size')).reset_index())
out('evidence/B_CONFIG_COUNTS.csv',plans.groupby(['config_id','family']).agg(inputs=('problem_id','nunique'),saved_plan_references=('problem_id','size')).reset_index())
out('evidence/B_MISSING_CERTIFICATE_REASONS.csv',pd.DataFrame(coverage).query('specific_missing_reason != ""').groupby(['scale','specific_missing_reason']).size().reset_index(name='inputs'))
# Timing inventory: code boundaries plus counted column availability.
runt=[]
def runtime(component,file,col,start,end,scope,available,total,kind='measured CPU wall/process',control='HOLD unmatched current8 end-to-end',environment='CPU; per-fit environment incomplete',source=''):
 runt.append(dict(component=component,saved_file=str(file),column_or_pointer=col,start_point=start,end_point=end,measurement_type=kind,execution_environment=environment,comparison_control=control,available_records=available,total_records=total,missing_records=total-available,scope=scope,source_code=source))
for fam,script,start,end,scope in [('mirror_family','run_staged_mirror_qaoa.py','fit():172 after load/model/scale/initial state setup','fit():212 before result JSON serialization','includes optimizer, MPS evolution, tighter precision checks, optimized+fixed state saving; excludes load, initial classical, measurement'),('grover_depth','run_staged_grover_depth.py','fit():70 after input load','fit():103 before FIT JSON write','includes stored training-cost read, optimizer and progress writes; excludes old p1/training pool generation, validation and measurement'),('active_adjacent_p3','run_staged_active_p3.py','worker():59 before input load','worker():94 before RESULT JSON write','includes load, grid, state evolution, BOTH optimized/fixed measurements+verification+NPZ writes; not fit-only')]:
 g=fits[fits.family==fam];src=str(S/fam/'SOURCE_SNAPSHOT/scripts'/script)
 for col in ['fit_wall_s','fit_CPU_s']:runtime('QAOA fit composite' if fam!='active_adjacent_p3' else 'active grid composite',P/'B_RESOURCES_PER_FIT.csv',col,start,end,scope,int(g[col].ne('').sum()),len(g),source=src)
for col in ['wall_seconds','CPU_seconds']:runtime('classical initial construction',P/'B_CLASSICAL_INITIAL_BASELINES.csv',col,'initial timer in old whole-roster runner (see evidence/RUNTIME_CODE_LOCATORS.txt)','initial construction timer stop; excludes current fit','INITIAL_ONLY',int(bases[col].ne('').sum()),len(bases),source='old whole-roster source locator; see evidence/RUNTIME_CODE_LOCATORS.txt')
res=df(P/'B_SAVED_RESOURCES_LONG.csv')
for (scope,field),g in res[res.resource_field.str.contains('seconds')].groupby(['scope','resource_field']):runtime('saved simulator substage',P/'B_SAVED_RESOURCES_LONG.csv',field,'json_pointer per record; code-defined substage','json_pointer per record; not total time',scope,len(g),len(g),source='frozen family SOURCE_SNAPSHOT scripts')
for c in ['preprocessing separate','classical approximation current8 solve','simulation separated from optimizer','measurement separate (mirror/Grover)','solution verification separate','postprocessing separate','data transfer/QPU queue']:
 runtime(c,'','NOT_SAVED','not instrumented separately','not instrumented separately','HOLD no separable current8 measurement',0,3680,kind='unmeasured; no estimate assigned')
out('PATH1_RUNTIME_SCOPE_INVENTORY.csv',pd.DataFrame(runt))
# T08 formula and explicit parameter provenance.
sc=js(T8/'SCENARIOS.json');bud=js(T8/'T08.json')['budgets'];params=[]
for scenario in sc['scenarios']:
 for k,v in scenario['parameters'].items():params.append({'model':'T08','condition_id':scenario['scenario_id'],'parameter':k,**{z:v.get(z,'') for z in ['value','unit','basis','evidence_status','source','adoption']},'file':str(T8/'SCENARIOS.json'),'locator':f"scenarios[{scenario['scenario_id']}].parameters.{k}"})
 p={k:float(v['value']) for k,v in scenario['parameters'].items()};q=p['gross_energy']/p['voltage'];m=q/(p['q_ref']*p['utilization']*p['f_positive'])+q*p['np_ratio']/(p['q_negative']*p['f_negative'])+scenario['cell_topology']['n_cells']*p['cell_other_mass']+p['pack_other_mass']+p['additional_mass'];ck('T08 independent mass formula',abs(m-bud[scenario['scenario_id']]['pack_mass_kg'])<1e-10,str(T8/'T08.json'),m)
# retain all row-specific T09 parameters with exact column name and unit suffix; don't flatten variable ranges.
t9=df(P/'C_T09_COMPONENTS_183.csv');paramcols=['q_reference_Ah_kg','positive_utilization','mean_voltage_design_V','gross_design_Wh','usable_design_Wh','area_policy','positive_active_loading_input_kg_m2','actual_positive_active_loading_kg_m2','negative_active_loading_kg_m2','positive_porosity','negative_porosity','NP_after_formation','negative_q_Ah_kg','negative_unavailable_fraction','negative_area_factor','independent_negative_loading_probe_kg_m2','Al_thickness_m','Cu_thickness_m','separator_areal_mass_kg_m2','extra_liquid_volume_m3','physical_cell_count_design']
for x in t9.to_dict('records'):
 for k in paramcols:params.append({'model':'T09','condition_id':x['condition_id'],'parameter':k,'value':x[k],'unit':'encoded in parameter column; dimensionless for ratios/policy/count','basis':'row-specific design input; not observed complete-pack property','evidence_status':'MODEL_INPUT; parameter sources separately recorded','source':str(T9/'PARAMETER_SOURCES.csv'),'adoption':'CONDITIONAL/HOLD','file':str(P/'C_T09_COMPONENTS_183.csv'),'locator':f"condition_id={x['condition_id']}; column={k}"})
 known=sum(float(x[k]) for k in ['positive_coating_kg','negative_coating_kg','Al_mass_kg','Cu_mass_kg','separator_dry_mass_kg','liquid_mass_kg']);ck('T09 known subtotal arithmetic',abs(known-float(x['known_cell_components_sum_kg']))<1e-8,x['condition_id']);ck('T09 complete pack NULL retained',x['complete_pack_mass_kg']=='',x['condition_id'])
freeze=js(R/'01_research_design/methodology/CONTROLLED_MASS_TO_DC_MODEL_FREEZE.json')
for k in ['g','rho','CdA','rotational_equivalent_mass','eta_prop','Crr_model','integration_rule','grade_model','regen_model','auxiliary_scope','turn_loss_scope']:
 params.append({'model':'Controlled-DC','condition_id':'FROZEN','parameter':k,'value':json.dumps(freeze[k],ensure_ascii=False),'unit':'see frozen typed parameter','basis':'fixed model input','evidence_status':'ASSUMED/FROZEN','source':str(R/'01_research_design/methodology/CONTROLLED_MASS_TO_DC_MODEL_FREEZE.json'),'adoption':'CONDITIONAL','file':str(R/'01_research_design/methodology/CONTROLLED_MASS_TO_DC_MODEL_FREEZE.json'),'locator':k})
out('PATH2_INPUT_PARAMETER_DICTIONARY.csv',pd.DataFrame(params))
# Boundaries are checked from parameters; arbitrary nonzero targets excluded from main boundary table.
bounds=df(T/'PATH2_BOUNDARY_RESULTS.csv');zero=bounds[bounds.kind=='ZERO_EFFECT_NOT_TARGET'].copy();zero['source']=str(T/'scripts/analyze.py');zero['base_parameter_source']=str(T8/'SCENARIOS.json');zero['value_type']='deterministic model calculation'
zero['b_definition']=['not applicable','LP positive coating minus S positive coating; common negative/fixed components cancel','not applicable','LP known coating+Al+Cu+separator+liquid minus S same boundary','LP known coating+Al+Cu+separator+liquid minus S same boundary']
zero['delta_definition']=['not applicable','S additional mass minus LP additional mass; excludes all components already in b','not applicable','S unknown casing+tabs+foil margins+pack structure minus LP same','S unknown casing+tabs+foil margins+pack structure minus LP same']
zero['fixed_conditions']=['qLP=171.875; qS=195.959596; sameV=3.5; no added mass','u=1,V=3.5,gross20kWh,N/P1.1,fpos.75,fneg.98,negq360,n100; fixed19+15kg','qS=195.959596,u1,LP V3.5; negative changes with V; fixed34kg','B015 design; see pair linkage table','B051 design; see pair linkage table']
zero['formula']=['u*=qLP/qS','b=E/V/fpos*(1/qLP-1/qS); DeltaM=b-delta','V*=E*(1/(qS*u*fpos)+NP/(qneg*fneg))/(M_LP-34)','b=knownLP-knownS; DeltaM=b-delta','b=knownLP-knownS; DeltaM=b-delta']
out('PATH2_BOUNDARY_DEFINITION_TABLE.csv',zero)
a={k:v['value'] for k,v in sc['scenarios'][0]['parameters'].items()};b={k:v['value'] for k,v in sc['scenarios'][1]['parameters'].items()};bmass=bud['COND_LP_REF']['pack_mass_kg']-bud['COND_S200_REF']['pack_mass_kg'];ustar=a['q_ref']/b['q_ref'];vstar=20000*(1/(b['q_ref']*.75)+1.1/(360*.98))/(bud['COND_LP_REF']['pack_mass_kg']-34)
for key,value in [('additional_mass_S_minus_LP',bmass),('utilization_at_qS',ustar),('mean_full_cell_voltage',vstar)]:ck('T08 boundary regeneration',abs(float(zero.loc[zero.input_variable==key,'value'].iloc[0])-value)<1e-10,key,value)
# C trace provenance and one-trajectory, two-Crr four-endpoint independent kernel verification.
energy=df(P/'C_T08_ENERGY_FULL.csv');cl=energy[energy.dataset=='CLASSICAL'];traces=cl[['trajectory_path','trajectory_sha256']].drop_duplicates()
for path,h in traces.itertuples(index=False,name=None):use(path,'C saved classical trajectory',h)
ck('C classical 460 distinct traces',len(traces)==460)
sys.path.insert(0,str(R/'src'));from kmd_quantitative.energy.controlled_dc import evaluate
first=cl.iloc[0];t=pd.read_csv(first.trajectory_path,usecols=['timestamp_s','speed_m_s']);tvals=t.timestamp_s.to_numpy();v=t.speed_m_s.to_numpy()
for rolling,pbar in [('CRR_LOWER_BOUND',4.5),('CRR_UPPER_BOUND',2.6)]:
 for sid in ['COND_LP_REF','COND_S200_REF']:
  saved=cl[(cl.trajectory_sha256==first.trajectory_sha256)&(cl.rolling_case==rolling)&(cl.scenario_id==sid)].iloc[0];calc,_=evaluate(tvals,v,freeze,pbar,{'running_mass_kg':float(saved.running_mass_kg)});ck('C one trajectory frozen kernel',abs(calc['net_DC_Wh']-float(saved.net_DC_Wh))<1e-7,first.trajectory_path,f'{rolling}/{sid}: {calc["net_DC_Wh"]}')
paired=cl.pivot(index=['trajectory_sha256','rolling_case'],columns='scenario_id',values='net_DC_Wh').astype(float);rat=[]
for rolling,g in paired.groupby(level='rolling_case'):
 lp=g['COND_LP_REF'];s=g['COND_S200_REF'];rat.append({'rolling_case':rolling,'trajectories':len(g),'baseline_sum_Wh':lp.sum(),'saving_sum_Wh':(lp-s).sum(),'total_weighted_saving_percent':100*(lp-s).sum()/lp.sum(),'mean_individual_saving_percent':(100*(lp-s)/lp).mean(),'calculation_kind':'model calculation from saved trajectories; not measured energy'})
out('evidence/C_ENDPOINT_RATIO_READBACK.csv',pd.DataFrame(rat))
# Actual manuscripts: every paragraph and table text is searchable with stable locators.
ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'};docs=[]
for p in [R/'tmp_RsrchMstrDc_1026_results_integrated.docx',R/'tmp_RsrchMstrDc_1026_revised.docx',R/'review_outputs/thesis_docx_integration_20261103/run01/revisions/v07_results_integrated.docx',T/'THESIS_TRIAL.docx']:
 use(p,'manuscript candidate; original vs separate trial distinguished');z=zipfile.ZipFile(p);xml=ET.fromstring(z.read('word/document.xml'));txt=[]
 for i,node in enumerate(xml.findall('.//w:p',ns)):txt.append(f'p{i}\t'+''.join(x.text or '' for x in node.findall('.//w:t',ns)))
 outname='evidence/'+('prior_trial_' if p.parent==T else 'v07_' if p.name.startswith('v07') else '')+p.stem+'_TEXT.txt';(O/outname).write_text('\n'.join(txt));docs.append({'path':str(p),'sha256':sources[str(p.resolve())]['sha256'],'paragraphs_including_tables':len(txt),'text_output':outname})
out('evidence/MANUSCRIPT_VERSIONS.json',docs)
# policy occurrences: sections retained, classify role later; include terms beyond primary label.
hits=[];terms=['定時配達率','期限内需要充足率','需要充足','0.25%','量子優位']
scan=[R/'README.md',*list((R/'docs').rglob('*.md')),*list((R/'docs/thesis').rglob('*.tex')),T/'RQ_REDESIGN_TRIAL.md',T/'THESIS_SECTIONS_TRIAL.md',*list((O/'evidence').glob('*TEXT.txt'))]
for p in scan:
 if not p.is_file():continue
 if not p.is_relative_to(O):use(p,'policy consistency audit text')
 heading=''
 for i,line in enumerate(p.read_text(errors='replace').splitlines(),1):
  if line.startswith('#'):heading=line[:200]
  found=[term for term in terms if term in line]
  if found:hits.append({'path':str(p),'line':i,'section':heading,'terms':';'.join(found),'text':line[:2400],'proposed_action':'retain history if old result/limitation; propose revise if current purpose/RQ/method/result claim; see POLICY_CONSISTENCY_AUDIT.md'})
out('evidence/POLICY_OCCURRENCES.csv',pd.DataFrame(hits))
out('evidence/PATH_RELOCATION_MAP.csv',pd.DataFrame(relocations));out('evidence/NUMERICAL_CHECKS.csv',pd.DataFrame(checks));out('SOURCE_PROVENANCE.csv',pd.DataFrame(sources.values()))
out('evidence/AUDIT_SUMMARY.json',{'sources':len(sources),'checks':len(checks),'failures':sum(x['status']=='FAIL' for x in checks),'B_NPZ_fraction_mismatches':mis,'B_float_csv_max_error_s':maxerr,'raw_sources':len(raw),'B_saved_best_feasible':valid,'input_seed_table_rows':len(st),'C_classical_traces':len(traces),'T08_mass_saving_kg':bmass,'utilization_boundary':ustar,'voltage_boundary_V':vstar,'policy_occurrences':len(hits),'scope':'readback arithmetic only; no new fits, simulations, exact solves, inference'})
print(json.dumps(json.loads((O/'evidence/AUDIT_SUMMARY.json').read_text()),indent=2));assert not any(x['status']=='FAIL' for x in checks)
