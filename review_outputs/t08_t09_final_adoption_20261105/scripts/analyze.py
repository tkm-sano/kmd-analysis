from pathlib import Path
import os,sys,json,hashlib,importlib.util,copy
os.environ['OPENBLAS_NUM_THREADS']='1'
import numpy as np,pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path('/home/takuma/kmd-analysis');O=Path(__file__).resolve().parents[1];U=Path('/home/takuma/kmd-analysis-pre-clean-20261102-112222/untracked');T9=U/'review_outputs/t09_open_data_model_20261029/run01';T8=U/'review_outputs/material_ev_stage2_20261026/run02'
for d in ['data','evidence','figures']: (O/d).mkdir(exist_ok=True)
sys.path.insert(0,str(R/'src'))
from kmd_quantitative.energy.controlled_dc import evaluate
sources={};checks=[]
def read(p):
 p=Path(p);sources[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest();return p

def csv(name,rows):pd.DataFrame(rows).to_csv(O/name,index=False)
def check(name,ok,detail=''):
 checks.append(dict(check=name,status='PASS' if ok else 'FAIL',detail=detail))
 if not ok:raise AssertionError((name,detail))
# Read every source used; no archived runner with writing side effects is executed.
for p in [T9/'model.py',T9/'analyze.py',T9/'PARAMETER_SOURCES.csv',T9/'RUN_CONFIG.json',T8/'SCENARIOS.json',R/'review_outputs/quantum_ev_step5_20261105/THESIS_FULL_TEXT.md',R/'review_outputs/no_sumo_alternative_design_20261102/run01/CHEN2020_TEXT.txt',U/'docs/research/EV_QUANTUM_APPLICABILITY_BASELINE_REVIEW_20261023.md',U/'review_outputs/t09_remaining_acceptance_20261029/run01/INPUT_EVIDENCE.csv',R/'src/kmd_quantitative/energy/frozen_sources/run_full_controlled_dc.py']:read(p)
spec=importlib.util.spec_from_file_location('t09_model_audit',T9/'model.py');mod=importlib.util.module_from_spec(spec);sys.modules[spec.name]=mod;spec.loader.exec_module(mod)
evidence=pd.read_csv(U/'review_outputs/t09_remaining_acceptance_20261029/run01/INPUT_EVIDENCE.csv').fillna('')
ledger=[]
for r in evidence.to_dict('records'):
 ledger.append(dict(parameter_id=r['input_id'],parameter=r['quantity'],value=r['value'],unit=r['unit'],primary_source=r['source'],locator=r['source_location'],acquisition=r['evidence_kind'],original_conditions=r['measurement_or_design_conditions'],target_conditions=r['material'],decision='HOLD' if r['target_status']=='HOLD' else 'CONDITIONAL GO',uncertainty=r['applicability'],sensitivity_required='YES',calculation_path='q/u/V -> active/coating -> area/pore/foil/liquid -> known mass -> delta mass -> frozen DC; unknown BOM remains NULL'))
t08=pd.read_csv(read(R/'review_outputs/quantum_ev_step4_evidence_decisions_20261104_183654/evidence/T08_PARAMETER_ADOPTION.csv')).fillna('')
for r in t08.to_dict('records'):ledger.append(dict(parameter_id=r['scenario_id']+'/'+r['parameter'],parameter=r['parameter'],value=r['value'],unit=r['unit'],primary_source=r['source'],locator=r['basis'],acquisition=r['evidence_status'],original_conditions='Chen: Li half-cell, 1C100cycles for q; 0.5C first cycle separate',target_conditions='20kWh hypothetical graphite full-cell pack',decision='CONDITIONAL GO',uncertainty='Reference scenario only; practical adoption HOLD; not initial measured full-cell capacity',sensitivity_required='YES',calculation_path='T08 mass equation -> replace pack once -> controlled DC'))
for r in pd.read_csv(T9/'PARAMETER_SOURCES.csv').fillna('').to_dict('records'):ledger.append(dict(parameter_id='T09/'+r['parameter'],parameter=r['parameter'],value=r['values'],unit=r['units'],primary_source=r['source'],locator=r['source'],acquisition=r['evidence_class'],original_conditions=r['applicability'],target_conditions='conditional T09 reference/probes',decision='CONDITIONAL GO',uncertainty=r['applicability']+'; target practical adoption HOLD',sensitivity_required='YES',calculation_path='T09 geometry/component subtotal; complete pack NULL'))
freeze=json.loads(read(R/'01_research_design/methodology/CONTROLLED_MASS_TO_DC_MODEL_FREEZE.json').read_text())
(O/'evidence/DC_FREEZE_SNAPSHOT.json').write_text(json.dumps(freeze,ensure_ascii=False,indent=2))
csv('data/PARAMETER_ADOPTION.csv',ledger)
base=dict(q=195.959596,u=1.,V=3.5,fp=.75,fn=.98,qn=360.,np=1.1,rhop=4458.,rhon=2200.,L=.1,ep=.25,en=.25,al=15e-6,cu=10e-6,sep=.013275,ts=25e-6,es=.41,rhol=1300.,wet=1.,sat=1.,excess=0.,cellother=.190,packother=15.,extra=0.,nf=1.,unavail=0.)
qLP=171.875

def calc(p,model,policy='fixed_loading'):
 Q=20000/p['V'];mp=Q/(p['q']*p['u']);mn=Q*p['np']/(p['qn']*(1-p['unavail']));pc=mp/p['fp'];nc=mn/p['fn']
 if model=='T08':return dict(positive=pc,negative=nc,other=100*p['cellother']+p['packother']+p['extra']),None
 A=mp/p['L'] if policy=='fixed_loading' else 20000/3.5/qLP/p['L'];An=A*p['nf'];As=max(A,An)
 vp=pc/p['rhop']*p['ep']/(1-p['ep']);vn=nc/p['rhon']*p['en']/(1-p['en'])
 return dict(positive=pc,negative=nc,Al=A/2*p['al']*2699,Cu=An/2*p['cu']*8960,separator=As*p['sep'],liquid=((vp+vn+As*p['ts']*p['es'])*p['wet']*p['sat']+p['excess'])*p['rhol']),dict(A=A,An=An,tp=pc/p['rhop']/(1-p['ep'])/A,tn=nc/p['rhon']/(1-p['en'])/An)
# Verify all original 183 rows through preserved model functions and saved columns.
old=pd.read_csv(read(T9/'PACK_20KWH_SENSITIVITY.csv'));repro=[]
for i,r in old.iterrows():
 pg=mod.geometry(r.positive_active_kg,r.positive_active_kg/r.positive_coating_kg,r.actual_positive_active_loading_kg_m2,r.positive_porosity,solid_mixture_density_kg_m3=4458)
 ng=mod.geometry(r.negative_active_kg,.98,r.negative_active_loading_kg_m2,r.negative_porosity,solid_mixture_density_kg_m3=2200)
 a=mod.foil_mass(r.positive_face_area_m2,2,r.Al_thickness_m,2699);c=mod.foil_mass(r.negative_face_area_m2,2,r.Cu_thickness_m,8960);asep=max(r.positive_face_area_m2,r.negative_face_area_m2)
 liq=mod.liquid_mass(pg['pore_volume_m3']+ng['pore_volume_m3']+asep*25e-6*.41,1,1,r.extra_liquid_volume_m3,1300)
 sub=r.positive_coating_kg+r.negative_coating_kg+a+c+asep*r.separator_areal_mass_kg_m2+liq
 err=abs(sub-r.known_cell_components_sum_kg);repro.append(dict(row=i+1,error_kg=err,complete_pack_is_null=pd.isna(r.complete_pack_mass_kg),overlap=r.overlap_condition))
 check('T09 original row '+str(i+1),err<1e-8 and pd.isna(r.complete_pack_mass_kg))
csv('evidence/T09_REPRODUCTION.csv',repro)
# One-factor S-only probes, LP held fixed. Ranges explicitly hypothetical unless source noted.
axes={'q':[qLP,180,195.959596,210], 'V':[3,3.2,3.5,3.8], 'u':[.8,.9,1], 'fp':[.75,.94,.96], 'fn':[.96,.98], 'np':[1,1.1,1.2], 'qn':[300,350,360], 'rhop':[3566.4,4458,5349.6], 'rhon':[1760,2200,2640], 'L':[.02,.1,.2], 'ep':[.25,.35,.45], 'en':[.25,.35,.45], 'al':[10e-6,15e-6,20e-6], 'cu':[8e-6,10e-6,15e-6], 'sep':[.008,.013275,.020], 'rhol':[1040,1300,1560], 'cellother':[.095,.190,.285], 'packother':[7.5,15,22.5], 'extra':[0,5.448297415076934,10], 'excess':[0,.001,.005], 'nf':[1,1.05,1.1], 'unavail':[0,.05], 'wet':[.8,1], 'sat':[.8,1]}
cases=[]
for model,policy in [('T08','fixed_loading'),('T09','fixed_loading'),('T09','fixed_area_LP')]:
 lp=base|{'q':qLP};bl=sum(calc(lp,model,policy)[0].values())
 for axis,vals in {'baseline':[0],**axes}.items():
  if model=='T08' and axis in ['rhop','rhon','L','ep','en','al','cu','sep','rhol','excess','nf','wet','sat']:continue
  if model=='T09' and axis in ['cellother','packother','extra']:continue
  for val in vals:
   p=base.copy()
   if axis!='baseline':p[axis]=val
   parts,geo=calc(p,model,policy);s=sum(parts.values());dm=bl-s
   cases.append(dict(case_id=f'{model}_{policy}_{axis}_{val}',model=model,policy=policy,axis=axis,value=val,range_origin='hypothetical ±20% (new)' if axis in ['rhop','rhon','rhol'] else 'new hypothetical' if axis in ['wet','sat'] or (axis=='q' and val==210) else 'prior probes or documented reference; applicability in ledger',q_LP=qLP,q_S=p['q'],u_S=p['u'],V_S=p['V'],LP_mass_or_known_kg=bl,S_mass_or_known_kg=s,delta_mass_kg=dm,LP_complete_pack_kg=bl if model=='T08' else None,S_complete_pack_kg=s if model=='T08' else None,LP_cell_sum_kg=bl-15 if model=='T08' else None,S_cell_sum_kg=s-p['packother']-p['extra'] if model=='T08' else None,delta_mass_percent=100*dm/bl,delta_q_Ah_kg=p['q']-qLP,delta_q_percent=100*(p['q']/qLP-1),delta_effective_q_percent=100*(p['q']*p['u']/qLP-1),mass_scope='conditional full pack estimate' if model=='T08' else 'known subtotal; no complete pack or absolute running mass',**{'S_'+k+'_kg':v for k,v in parts.items()}))
# Voltage-utilization interaction; same S-only contrast as T08; T09 physical subtotal remains incomplete.
for u in np.linspace(.8,1,9):
 for v in np.linspace(3,3.8,9):
  p=base|{'u':u,'V':v};bl=sum(calc(base|{'q':qLP},'T08')[0].values());s=sum(calc(p,'T08')[0].values())
  cases.append(dict(case_id=f'T08_UV_{u}_{v}',model='T08',policy='fixed_loading',axis='u_V',value=v,u_S=u,V_S=v,q_LP=qLP,q_S=base['q'],LP_mass_or_known_kg=bl,S_mass_or_known_kg=s,delta_mass_kg=bl-s,LP_complete_pack_kg=bl,S_complete_pack_kg=s,mass_scope='conditional full pack estimate',range_origin='prior 9x9 hypothetical probes'))
csv('data/MASS_SENSITIVITY.csv',cases)
LP=sum(calc(base|{'q':qLP},'T08')[0].values());SS=sum(calc(base,'T08')[0].values());b=LP-SS
check('T08 LP original',abs(LP-96.14565479871602)<1e-10);check('T08 S original',abs(SS-90.69735738363909)<1e-10)
# DC all unique saved CLASSICAL trajectories. Compression retains always-positive and switching branches exactly on tested mass interval.
saved=pd.read_csv(read(R/'review_outputs/no_sumo_full_analysis_20261102/run01/C_T08_ENERGY_FULL.csv'));saved=saved[saved.dataset=='CLASSICAL'];nonpack=1043.888888888889
results=[];op=[];mc=pd.DataFrame(cases);t08cases=mc[mc.model=='T08'].to_dict('records');ml=np.array([nonpack+c['LP_mass_or_known_kg'] for c in t08cases]);ms=np.array([nonpack+c['S_mass_or_known_kg'] for c in t08cases]);low=min(1000,ml.min(),ms.min());high=max(1250,ml.max(),ms.max())
for ni,(h,g) in enumerate(saved.groupby('trajectory_sha256')):
 p=Path(g.iloc[0].trajectory_path)
 if not p.exists():
  p=U/p.relative_to(R) if p.is_relative_to(R) else p
 df=pd.read_csv(read(p),usecols=['timestamp_s','speed_m_s']);t=df.timestamp_s.to_numpy();v=df.speed_m_s.to_numpy();cur=v[1:];dv=cur**2-v[:-1]**2;ds=cur*np.diff(t)
 check('trajectory '+h,np.all(np.diff(t)==1) and np.all(v>=0))
 for rc,pressure in [('CRR_LOWER_BOUND',4.5),('CRR_UPPER_BOUND',2.6)]:
  a=(9.80665*(.005+(.01+.0095*(3.6*cur/100)**2)/pressure)*ds+.5*dv)/3600;c=(.5*61*dv+.5*1.2041*1.175*cur**2*ds)/3600
  al=a*low+c;ah=a*high+c;always=(al>0)&(ah>0);switch=(al>0)!=(ah>0);aa=a[switch];cc=c[switch];ca=a[always].sum();cb=c[always].sum()
  def energy(m):return (ca*m+cb+np.maximum(np.asarray(m)[:,None]*aa+cc,0).sum(axis=1))/.9
  eb=energy(ml);es=energy(ms);end=energy(np.array([nonpack+LP,nonpack+SS]));minimum_slope=(ca+aa[(aa*low+cc)>0].sum())/.9
  for idx,m in enumerate([nonpack+LP,nonpack+SS]):
   direct,_=evaluate(t,v,freeze,pressure,{'running_mass_kg':m});check('frozen endpoint '+h+rc+str(idx),abs(direct['net_DC_Wh']-end[idx])<1e-7)
   sid=['COND_LP_REF','COND_S200_REF'][idx];obs=float(g[(g.rolling_case==rc)&(g.scenario_id==sid)].net_DC_Wh.iloc[0]);check('saved endpoint '+h+rc+str(idx),abs(obs-end[idx])<1e-7)
  for ci,(case,e1,e2) in enumerate(zip(t08cases,eb,es)):
   dm=case['delta_mass_kg'];de=e1-e2;qr=case.get('delta_q_percent',np.nan)/100
   results.append(dict(case_id=case['case_id'],trajectory_sha256=h,rolling_case=rc,LP_vehicle_running_kg=ml[ci],S_vehicle_running_kg=ms[ci],LP_DC_Wh=e1,S_DC_Wh=e2,delta_DC_Wh=de,DC_saving_percent=100*de/e1,mass_to_DC_Wh_per_kg=de/dm if abs(dm)>1e-10 else None,relative_q_to_DC_transfer=(de/e1)/qr if pd.notna(qr) and abs(qr)>1e-12 else None,scope='T08 hypothetical full pack replacement; same saved trajectory'))
  op.append(dict(trajectory_sha256=h,rolling_case=rc,distance_km=ds.sum()/1000,delta_mass_kg=b,LP_DC_Wh=end[0],S_DC_Wh=end[1],delta_DC_Wh=end[0]-end[1],Wh_per_kg=(end[0]-end[1])/b,min_mass_derivative=minimum_slope,verified_interval_low=low,verified_interval_high=high))
 if ni%100==0:print('trajectories',ni,flush=True)
rd=pd.DataFrame(results);rd.to_csv(O/'data/DC_TRANSMISSION.csv.gz',index=False,compression='gzip');csv('data/OPERATION_RESPONSE.csv',op)
summary=[]
for (cid,rc),g in rd.groupby(['case_id','rolling_case']):
 summary.append(dict(case_id=cid,rolling_case=rc,n=len(g),LP_sum_Wh=g.LP_DC_Wh.sum(),S_sum_Wh=g.S_DC_Wh.sum(),delta_sum_Wh=g.delta_DC_Wh.sum(),mean_delta_Wh=g.delta_DC_Wh.mean(),min_delta_Wh=g.delta_DC_Wh.min(),max_delta_Wh=g.delta_DC_Wh.max(),weighted_saving_percent=100*g.delta_DC_Wh.sum()/g.LP_DC_Wh.sum(),mean_relative_q_to_DC_transfer=g.relative_q_to_DC_transfer.mean()))
csv('data/DC_SUMMARY.csv',summary)
ustar=qLP/base['q'];vstar=20000*(1/(base['q']*.75)+1.1/(360*.98))/(LP-34)
bounds=[dict(model='T08',variable='q_S',boundary=qLP,unit='Ah/kg',conditions='uS=1,V=3.5,same fractions/anode/fixed masses'),dict(model='T08',variable='u_S',boundary=ustar,unit='1',conditions='qS=195.959596; LP u1/V3.5'),dict(model='T08',variable='V_S',boundary=vstar,unit='V',conditions='qS195.959596,u1; LP V3.5; negative mass changes with V'),dict(model='T08',variable='extra_S_minus_LP',boundary=b,unit='kg',conditions='baseline reference only')]
for policy in ['fixed_loading','fixed_area_LP']:
 bl=sum(calc(base|{'q':qLP},'T09',policy)[0].values());ss=sum(calc(base,'T09',policy)[0].values());bounds.append(dict(model='T09',variable='unknown_S_minus_LP',boundary=bl-ss,unit='kg',conditions=policy+'; complete pack remains unknown'))
csv('data/BOUNDARIES.csv',bounds)
# Source preservation is checked at the end, against hashes captured before computation.
for p,h in sources.items():check('preserved '+p,hashlib.sha256(Path(p).read_bytes()).hexdigest()==h)
csv('evidence/SOURCE_MANIFEST.csv',[dict(path=p,sha256=h) for p,h in sources.items()]);csv('evidence/COMPUTATIONAL_CHECKS.csv',checks)
# Publication-ready standalone figures.
fig,ax=plt.subplots(figsize=(9,3));ax.axis('off');labels=['q:171.875 ->195.959596\n+14.01% (derived reference)',f'T08 pack\n{LP:.3f} -> {SS:.3f} kg\nSaving {b:.3f} kg',f'Running mass\n{nonpack+LP:.3f} -> {nonpack+SS:.3f} kg','Frozen DC\n460 trajectories x 2 Crr\nSee DC_SUMMARY.csv']
for i,label in enumerate(labels):ax.text(.02+i*.25,.5,label,transform=ax.transAxes,fontsize=8,bbox=dict(boxstyle='round',facecolor='#e4edf7')); 
for x in [.22,.47,.72]:ax.annotate('',xy=(x+.025,.53),xytext=(x,.53),xycoords='axes fraction',arrowprops=dict(arrowstyle='->'))
fig.savefig(O/'figures/TRANSMISSION.pdf',bbox_inches='tight');fig.savefig(O/'figures/TRANSMISSION.png',dpi=180,bbox_inches='tight');plt.close(fig)
fig,axs=plt.subplots(1,2,figsize=(10,4));uv=mc[mc.axis=='u_V'].pivot(index='u_S',columns='V_S',values='delta_mass_kg');im=axs[0].contourf(uv.columns,uv.index,uv.values,15,cmap='coolwarm');axs[0].contour(uv.columns,uv.index,uv.values,[0],colors='black');axs[0].set(xlabel='S mean full-cell voltage (V)',ylabel='S utilization');fig.colorbar(im,ax=axs[0],label='LP-S conditional pack mass (kg)')
for pol in ['fixed_loading','fixed_area_LP']:
 s=mc[(mc.model=='T09')&(mc.policy==pol)&(mc.axis=='L')];axs[1].plot(s.value*100,s.delta_mass_kg,'o-',label=pol)
axs[1].axhline(0,color='k');axs[1].set(xlabel='Cathode active loading (mg/cm2)',ylabel='LP-S known subtotal (kg)');axs[1].legend();fig.tight_layout();fig.savefig(O/'figures/BOUNDARIES.pdf');fig.savefig(O/'figures/BOUNDARIES.png',dpi=180);plt.close(fig)
report=dict(trajectories=int(saved.trajectory_sha256.nunique()),original_T09_rows=len(old),mass_cases=len(cases),dc_rows=len(rd),checks=len(checks),failures=0,T08_LP_kg=LP,T08_S_kg=SS,delta_kg=b,u_boundary=ustar,V_boundary=vstar,source_preservation='PASS',scientific_practical_adoption='HOLD',T09_complete_pack='HOLD',min_dc_slope=min(x['min_mass_derivative'] for x in op))
(O/'evidence/RUN_RESULT.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
