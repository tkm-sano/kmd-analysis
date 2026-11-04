from pathlib import Path
from fractions import Fraction as F
import pandas as pd,numpy as np,json,hashlib,datetime
O=Path(__file__).resolve().parents[1];R=O.parents[1];U=Path('/home/takuma/kmd-analysis-pre-clean-20261102-112222/untracked');P=R/'review_outputs/no_sumo_full_analysis_20261102/run01';T=R/'review_outputs/quantum_ev_conditions_full_trial_20261104_125659';S=U/'review_outputs/staged_qaoa_validation_20261102';T9=U/'review_outputs/t09_open_data_model_20261029/run01';BR=U/'review_outputs/t08_t09_conditional_bridge_20261030/run01';C=U/'review_outputs/cpu_matched_classical_swaps_r0_r5_20261101';W=U/'review_outputs/unified_no_windows_r0_r8_20261022'
prov=pd.read_csv(O/'SOURCE_PROVENANCE.csv',keep_default_na=False).to_dict('records');known={x['path'] for x in prov};checks=[]
def use(p,role):
 p=Path(p);assert p.is_file(),p
 if str(p) not in known:
  st=p.stat();prov.append(dict(path=str(p),version='saved frozen source; SHA256 identifies version',sha256=hashlib.file_digest(p.open('rb'),'sha256').hexdigest(),bytes=st.st_size,mtime_utc=datetime.datetime.fromtimestamp(st.st_mtime,datetime.timezone.utc).isoformat(),role=role,reference=role,storage='repository' if p.is_relative_to(R) else 'external preservation'));known.add(str(p))
 return p
def ck(k,v,source,detail=''):checks.append(dict(check=k,status='PASS' if bool(v) else 'FAIL',source=str(source),detail=str(detail)))
for root in [C/'SOURCE_SNAPSHOT',W/'SOURCE_SNAPSHOT',U/'review_outputs/material_ev_stage2_20261026/run02/SOURCE_SNAPSHOT']:
 for p in root.rglob('*.py'):use(p,'frozen upstream implementation')
for n in ['PROTOCOL.json','MANIFEST.json','CPU_BUDGETS.json','DOMAIN_CERTIFICATES.json']:use(C/n,'classical approximate execution protocol')
for n in ['T09_MASS_BOUNDARIES.csv','MASS_COMPONENT_BRIDGE.csv','DC_MASS_RESPONSE.csv','DC_BRANCH_DOMAINS.csv','T08_T09_DC_COMPARISON.csv','integrate.py']:use(BR/n,'T09 component boundary generation')
for n in ['PACK_CASE_INDEX.csv','PARAMETER_SOURCES.csv','RUN_CONFIG.json']:use(T9/n,'T09 row and parameter provenance')
aux=pd.read_csv(P/'B_AUXILIARY_CLASSICAL_IMPROVEMENTS.csv',keep_default_na=False);meta={x['run_id']:x for x in json.loads((C/'MANIFEST.json').read_text())};initial=pd.read_csv(P/'B_CLASSICAL_INITIAL_BASELINES.csv',keep_default_na=False).set_index('problem_id');rawrows=[]
for pid,g in aux.groupby('problem_id'):
 m=meta[pid];ip=Path(m['instance_path']);ip=ip if ip.is_file() else U/ip.relative_to(R);use(ip,'classical approximation original NPZ')
 with np.load(ip,allow_pickle=False) as z:travel=z['travel'];demand=z['demand']
 for x in g.to_dict('records'):
  path=use(C/'RUNS'/pid/x['method']/'RESULT.json','classical approximate saved route result');d=json.loads(path.read_text());route=d['route_indices'];score=sum((F(str(travel[i,j])) for i,j in zip(route,route[1:])),F(0));ok=route[0]==route[-1]==0 and sorted(route[1:-1])==list(range(1,len(travel))) and float(np.sum(demand))<=216 and float(score)+102*(len(travel)-1)<=32400
  ck('JC original NPZ hash',hashlib.file_digest(ip.open('rb'),'sha256').hexdigest()==d['instance_sha256']==x['input_sha256'],path)
  ck('JC original route exact score and table',score==F(d['best_road_seconds'])==F(x['classical_best_seconds']),path)
  ck('JC original feasibility',ok,path)
  ck('JC shared initial route',d['initial_route']==json.loads(initial.loc[pid,'initial_route']) and F(d['initial_road_seconds'])==F(x['initial_road_seconds']),path)
  rawrows.append({'problem_id':pid,'method':x['method'],'raw_result_path':str(path),'input_sha256':d['instance_sha256'],'route_score_fraction':str(score),'feasible':ok,'seed':d['seed'],'current8_budget_matched':False})
pd.DataFrame(rawrows).to_csv(O/'evidence/CLASSICAL_APPROXIMATION_ROUTE_CHECK.csv',index=False)
# T09 independently recalculate geometry/materials from model inputs and source constants.
t9=pd.read_csv(P/'C_T09_COMPONENTS_183.csv',keep_default_na=False);detail=[]
for x in t9.to_dict('records'):
 def f(k):return F(str(x[k]))
 Q=f('gross_design_Wh')/f('mean_voltage_design_V');mp=Q/f('q_reference_Ah_kg')/f('positive_utilization');fp=F('.96') if x['series']=='A_PUBLIC_ELECTRODE_REFERENCE' else F('.75');pc=mp/fp;mn=Q*f('NP_after_formation')/f('negative_q_Ah_kg')/(1-f('negative_unavailable_fraction'));nc=mn/F('.98')
 area=f('positive_face_area_m2');an=f('negative_face_area_m2');sep=max(area,an);liquid=(pc/F(4458)*f('positive_porosity')/(1-f('positive_porosity'))+nc/F(2200)*f('negative_porosity')/(1-f('negative_porosity'))+sep*F('25e-6')*F('.41')+f('extra_liquid_volume_m3'))*1300
 values={'positive_active_kg':mp,'positive_coating_kg':pc,'negative_active_kg':mn,'negative_coating_kg':nc,'Al_mass_kg':area/2*f('Al_thickness_m')*2699,'Cu_mass_kg':an/2*f('Cu_thickness_m')*8960,'separator_dry_mass_kg':sep*f('separator_areal_mass_kg_m2'),'liquid_mass_kg':liquid}
 for k,v in values.items():
  err=abs(float(v)-float(x[k]));ck('T09 independent component',err<1e-8,x['condition_id'],f'{k}: {err}kg');detail.append(dict(condition_id=x['condition_id'],component=k,recomputed_kg=float(v),stored_kg=x[k],absolute_error_kg=err))
 ck('T09 area active loading identity',abs(float(mp/area)-float(x['actual_positive_active_loading_kg_m2']))<1e-12,x['condition_id'])
pd.DataFrame(detail).to_csv(O/'evidence/T09_COMPONENT_READBACK.csv',index=False)
bd=pd.read_csv(BR/'T09_MASS_BOUNDARIES.csv',keep_default_na=False);links=[];zero=pd.read_csv(O/'PATH2_BOUNDARY_DEFINITION_TABLE.csv',keep_default_na=False)
for pair in ['B015','B051']:
 g=bd[bd.pair_id==pair];lp=g[g.material_condition=='LP'].iloc[0];ss=g[g.material_condition=='S200'].iloc[0];a=t9[t9.condition_id==lp.scenario_id].iloc[0];b=t9[t9.condition_id==ss.scenario_id].iloc[0];diff=float(a.known_cell_components_sum_kg)-float(b.known_cell_components_sum_kg)
 ck('T09 pair boundary from original row',abs(diff-float(ss.unknown_mass_boundary))<1e-10,BR/'T09_MASS_BOUNDARIES.csv',pair)
 ck('T09 existing trial boundary agreement',abs(diff-float(zero[zero.boundary.str.startswith(pair)].value.iloc[0]))<1e-10,T/'PATH2_BOUNDARY_RESULTS.csv',pair)
 links.append(dict(pair_id=pair,LP_condition_id=lp.scenario_id,S_condition_id=ss.scenario_id,design_policy=lp.design_policy,LP_known_kg=a.known_cell_components_sum_kg,S_known_kg=b.known_cell_components_sum_kg,b_kg=diff,LP_q=a.q_reference_Ah_kg,S_q=b.q_reference_Ah_kg,LP_u=a.positive_utilization,S_u=b.positive_utilization,voltage_V=a.mean_voltage_design_V,loading_probe_kg_m2=a.positive_active_loading_input_kg_m2,LP_porosity=a.positive_porosity,negative_porosity=a.negative_porosity,source=str(BR/'T09_MASS_BOUNDARIES.csv')))
pd.DataFrame(links).to_csv(O/'evidence/T09_BOUNDARY_PAIR_LINKAGE.csv',index=False)
# Explicit timing and algorithm line locators.
loc=[]
for p,words in [(W/'SOURCE_SNAPSHOT/scripts/run_unified_no_windows.py',['def classical','wall=time.perf_counter();cpu=time.process_time()','solver.heuristic','wall_seconds=time.perf_counter()-wall']), (W/'SOURCE_SNAPSHOT/src/kmd_quantitative/routing/solver.py',['def heuristic','sweeps','nearest','best']), (C/'SOURCE_SNAPSHOT/scripts/run_cpu_matched_classical_swaps.py',['CPU_scope=','start=time.perf_counter();c=time.process_time()','used=time.process_time()-c','wall=time.perf_counter()-start'])]:
 use(p,'timing boundary and classical algorithm')
 for i,l in enumerate(p.read_text().splitlines(),1):
  if any(w in l for w in words):loc.append(f'{p}:{i}: {l.strip()}')
(O/'evidence/RUNTIME_CODE_LOCATORS.txt').write_text('\n'.join(loc)+'\n')
# Runtime improve actual upstream approximate measurement scope, count verified raw records.
rt=pd.read_csv(O/'PATH1_RUNTIME_SCOPE_INVENTORY.csv',keep_default_na=False)
for col in ['actual_CPU_seconds','wall_seconds']:
 rt.loc[len(rt)]=dict(component='classical approximation historical solve',saved_file=str(C/'RUNS/<problem_id>/<method>/RESULT.json'),column_or_pointer=col,start_point='run_cpu_matched_classical_swaps.py:101 before NPZ read/validation/integer preprocessing',end_point=':157 after final exact route validation before RESULT serialization',measurement_type='measured CPU wall/process',execution_environment='CPU fixed affinity; initial shared; old swap budget',comparison_control='old whole-roster swap only; current staged8 unmatched',available_records=920,total_records=920,missing_records=0,scope='includes NPZ/preprocess/search/verification; excludes imports/shared initial/reference/serialization',source_code=str(C/'SOURCE_SNAPSHOT/scripts/run_cpu_matched_classical_swaps.py'))
for i in rt.index[rt.component=='classical initial construction']:
 rt.loc[i,'start_point']='run_unified_no_windows.py:153 after input load/check';rt.loc[i,'end_point']=':157 after solver.heuristic(sweeps=3)+nw.validate, before certificate';rt.loc[i,'scope']='three-sweep deterministic heuristic and validation; excludes input read, imports, certificate, artifact IO';rt.loc[i,'source_code']=str(W/'SOURCE_SNAPSHOT/scripts/run_unified_no_windows.py')
rt.to_csv(O/'PATH1_RUNTIME_SCOPE_INVENTORY.csv',index=False)
# Parameter units are concrete and include omitted structural constants/fractions.
dic=pd.read_csv(O/'PATH2_INPUT_PARAMETER_DICTIONARY.csv',keep_default_na=False)
def unit(k):
 if 'Ah_kg' in k:return 'Ah/kg'
 if 'kg_m2' in k:return 'kg/m^2'
 if k.endswith('_Wh'):return 'Wh'
 if k.endswith('_V'):return 'V'
 if k.endswith('_m3'):return 'm^3/pack'
 if k.endswith('_m'):return 'm'
 if k=='area_policy':return 'category'
 if k=='physical_cell_count_design':return 'count'
 return '1'
for i,x in dic[dic.model=='T09'].iterrows():dic.loc[i,'unit']=unit(x.parameter)
extra=[]
for x in t9.to_dict('records'):
 for k,v,un in [('f_positive',.96 if x['series']=='A_PUBLIC_ELECTRODE_REFERENCE' else .75,'1'),('f_negative',.98,'1')]:extra.append(dict(model='T09',condition_id=x['condition_id'],parameter=k,value=v,unit=un,basis='dry coating active mass fraction excluding foil; explicit packrow calls',evidence_status='MODEL_INPUT',source=str(T9/'analyze.py'),adoption='CONDITIONAL/HOLD',file=str(T9/'analyze.py'),locator='packrow calls:365-400'))
for k,v,un in [('positive_solid_density',4458,'kg/m^3'),('negative_solid_density',2200,'kg/m^3'),('Al_density',2699,'kg/m^3'),('Cu_density',8960,'kg/m^3'),('liquid_density',1300,'kg/m^3'),('separator_thickness',25e-6,'m'),('separator_porosity',.41,'1'),('wettable_fraction',1,'1'),('saturation',1,'1')]:extra.append(dict(model='T09',condition_id='ALL',parameter=k,value=v,unit=un,basis='explicit geometry transfer/design assumption',evidence_status='MODEL_INPUT',source=str(T9/'analyze.py'),adoption='CONDITIONAL/HOLD',file=str(T9/'analyze.py'),locator='cfg/packrow:300-343'))
pd.concat([dic,pd.DataFrame(extra)],ignore_index=True).to_csv(O/'PATH2_INPUT_PARAMETER_DICTIONARY.csv',index=False)
# Correct boundary source definitions and explicit common conditions from original pairs.
for i,x in zero.iterrows():
 if str(x.boundary).startswith('B'):
  pair=x.boundary.split()[0];link=next(y for y in links if y['pair_id']==pair);zero.loc[i,'base_parameter_source']=str(T9/'RUN_CONFIG.json')+';'+str(BR/'T09_MASS_BOUNDARIES.csv');zero.loc[i,'source']=str(BR/'integrate.py')+';'+str(T9/'analyze.py');zero.loc[i,'fixed_conditions']=f"{pair}: {link['LP_condition_id']}/{link['S_condition_id']}; qLP171.875 qS195.959596; u=1,V3.5,gross20kWh,NP1.1,positive fraction.75,negative fraction.98; loading.1kg/m2; porosity positive.25/negative.25; {link['design_policy']}; see linkage CSV"
zero.to_csv(O/'PATH2_BOUNDARY_DEFINITION_TABLE.csv',index=False)
# Specific manuscript audit categories without treating history as violation.
text=(O/'evidence/tmp_RsrchMstrDc_1026_results_integrated_TEXT.txt').read_text().splitlines();cats=[]
for pids,section,action,status in [([11,23,27,45],'目的・問い/指標','二経路の寄与条件へ本文更新候補;定時率は主指標から除外','CONDITIONAL'),([281],'方法','A旧主指標の履歴であることを見出しと参照で区別','CONDITIONAL'),([444],'結果','A旧結果を保持;新研究の主効果の根拠に昇格しない','CONDITIONAL'),([856,1284],'考察・限界','未実証接続として保持;目的の旧記述から結論を再構成しない','PASS'),([1026,1180,1260,1268,2319],'旧節/付録・旧結果台帳','削除しない;歴史的補足と表示','PASS')]:
 for pid in pids:
  found=[l for l in text if l.startswith(f'p{pid}\\t') or l.startswith(f'p{pid}\t')];cats.append(dict(file=str(R/'tmp_RsrchMstrDc_1026_results_integrated.docx'),locator=f'XML paragraph p{pid} (including tables)',section=section,trial_action=action,status=status,excerpt=found[0][:2200] if found else 'see full extracted XML text'))
pd.DataFrame(cats).to_csv(O/'evidence/POLICY_CLASSIFIED_LOCATORS.csv',index=False)
pd.DataFrame(prov).to_csv(O/'SOURCE_PROVENANCE.csv',index=False);pd.DataFrame(checks).to_csv(O/'evidence/SUPPLEMENT_CHECKS.csv',index=False)
summary={'sources':len(prov),'checks':len(checks),'failures':sum(x['status']=='FAIL' for x in checks),'classical_raw_routes':len(rawrows),'T09_component_checks':len(detail),'T09_pair_links':links}
(O/'evidence/SUPPLEMENT_SUMMARY.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2,default=str));print(json.dumps(summary,ensure_ascii=False,indent=2,default=str));assert not any(x['status']=='FAIL' for x in checks)
