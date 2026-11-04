from common import *
sys.path.insert(0,str(R/'src'))
from kmd_quantitative.energy.controlled_dc import evaluate

def mass(q,u=1,V=3.5,fixed=34,extra=0):
 q,u,V,fixed,extra=map(lambda x:F(str(x)),[q,u,V,fixed,extra]);Q=F(20000)/V;return Q/(q*u*F('.75'))+Q*F('1.1')/(360*F('.98'))+fixed+extra

def t09(q,u,V,policy,por=F('.25'),loading=F('.1')):
 Q=F(20000)/F(str(V));mp=Q/(F(str(q))*F(str(u)));pc=mp/F('.75');mn=Q*F('1.1')/360;nc=mn/F('.98');area=mp/loading if policy=='fixed_loading' else Q/F('171.875')/loading;an=area;sep=area
 parts=dict(positive_coating_kg=pc,negative_coating_kg=nc,Al_mass_kg=area/2*F('15e-6')*2699,Cu_mass_kg=an/2*F('1e-5')*8960,separator_dry_mass_kg=sep*F('.013275'),liquid_mass_kg=(pc/4458*por/(1-por)+nc/2200*por/(1-por)+sep*F('25e-6')*F('.41'))*1300)
 return parts

def main():
 t0=time.perf_counter();os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});freeze=js(R/'01_research_design/methodology/CONTROLLED_MASS_TO_DC_MODEL_FREEZE.json');sc=js(T8/'SCENARIOS.json');qLP=sc['scenarios'][0]['parameters']['q_ref']['value'];qS=sc['scenarios'][1]['parameters']['q_ref']['value'];LP=mass(qLP);SS=mass(qS);b=LP-SS;nonpack=F('1043.888888888889');lo,hi=1000.,1250.;bounds=[];cases=[]
 for j,q in enumerate(np.linspace(qLP,qS,49)):cases.append(dict(model='T08',case_id=f'Q{j:02d}',axis='q_only',q=float(q),u=1.,V=3.5,fixed=34.,delta=0.,LP=LP,S=mass(q),scope='simplified conditional pack'))
 for ui,u in enumerate(np.linspace(.8,1,9)):
  for vi,V in enumerate(np.linspace(3.,3.8,9)):
   sm=mass(qS,u,V);bb=LP-sm;cases.append(dict(model='T08',case_id=f'UV{ui}_{vi}',axis='u_V',q=qS,u=float(u),V=float(V),fixed=34.,delta=0.,LP=LP,S=sm,scope='LP held at V3.5; S V varied'))
   bounds.append(dict(model='T08',condition_id=f'UV{ui}_{vi}',u=u,V=V,b_kg=float(bb),delta_zero_effect_kg=float(bb),formula='b=M_LP−M_S_without_extra; DeltaM=b−delta',b_scope='both dry coatings plus common34kg; V change also changes negative mass',delta_scope='S extra mass minus LP extra mass; no component overlap',unit='kg',status='CONDITIONAL_MODEL'))
 for fixed in [17.,34.,51.]:cases.append(dict(model='T08',case_id=f'FIXED{fixed:g}',axis='common_fixed_mass',q=qS,u=1.,V=3.5,fixed=fixed,delta=0.,LP=mass(qLP,fixed=fixed),S=mass(qS,fixed=fixed),scope='same fixed mass applied to both materials'))
 for diff in [-1,0,1]:
  delta=b+diff;cases.append(dict(model='T08',case_id=f'CANCEL{diff:+d}',axis='additional_mass',q=qS,u=1.,V=3.5,fixed=34.,delta=float(delta),LP=LP,S=SS+delta,scope='T08 additional mass difference; zero mass at diff0'))
 # T09 common-input structural sensitivity. Keep unknown BOM null.
 t9rows=[]
 for policy in ['fixed_loading','fixed_area_LP']:
  for ui,u in enumerate(np.linspace(.8,1,9)):
   for vi,V in enumerate(np.linspace(3.,3.8,9)):
    pp=t09(qLP,1,V,policy);sp=t09(qS,u,V,policy);bb=sum(pp.values(),F(0))-sum(sp.values(),F(0));bcoating=pp['positive_coating_kg']+pp['negative_coating_kg']-sp['positive_coating_kg']-sp['negative_coating_kg'];row=dict(model='T09',policy=policy,condition_id=f'{policy}_U{ui}_V{vi}',qLP=qLP,qS=qS,uS=u,V_common=V,LP_known_kg=float(sum(pp.values())),S_known_kg=float(sum(sp.values())),b_known_kg=float(bb),T08_comparable_coating_b_kg=float(bcoating),unknown_LP_kg=None,unknown_S_kg=None,complete_pack_mass_LP_kg=None,complete_pack_mass_S_kg=None,known_boundary='coatings+Al+Cu+separator+liquid',status='CONDITIONAL_KNOWN_COMPONENTS_ONLY')
    for k in pp:row['delta_'+k]=float(pp[k]-sp[k])
    t9rows.append(row);bounds.append(dict(model='T09',condition_id=row['condition_id'],u=u,V=V,b_kg=float(bb),delta_zero_effect_kg=float(bb),formula='b=knownLP−knownS; DeltaM=b−delta',b_scope=row['known_boundary'],delta_scope='S−LP unknown casing/tabs/foil margins/pack structure; NULL as physical quantity',unit='kg',status='CONDITIONAL_MODEL_STRUCTURE'))
 pairlinks=frame(S1/'evidence/T09_BOUNDARY_PAIR_LINKAGE.csv')
 for pair,policy in [('B015','fixed_loading'),('B051','fixed_area_LP')]:
  pa=t09(qLP,1,3.5,policy);sa=t09(qS,1,3.5,policy);bb=sum(pa.values())-sum(sa.values());saved=float(pairlinks[pairlinks.pair_id==pair].b_kg.iloc[0]);ck('T09 common-input endpoint reproduces original b',abs(float(bb)-saved)<1e-10,pair)
  for offset in [None,-1,0,1]:
   delta=F(0) if offset is None else bb+offset;dm=bb-delta;cases.append(dict(model='T09_MASS_PROBE',case_id=pair+('_D0' if offset is None else f'_C{offset:+d}'),axis='unknown_mass_difference',q=qS,u=1.,V=3.5,fixed=None,delta=float(delta),LP=LP,S=LP-dm,scope='running-mass probe at T08 reference, not complete T09 pack'))
 table('PATH2_T09_COMMON_INPUT_SENSITIVITY.csv',t9rows)
 # Analytic T08 boundary values explicitly from original parameters.
 ustar=F(str(qLP))/F(str(qS));vstar=F(20000)*(1/(F(str(qS))*F('.75'))+F('1.1')/(360*F('.98')))/(LP-34)
 for name,var,val,unit_ in [('T08_DEFAULT_MASS','delta',b,'kg'),('T08_DEFAULT_UTILIZATION','u',ustar,'1'),('T08_DEFAULT_VOLTAGE','V',vstar,'V')]:bounds.append(dict(model='T08',condition_id=name,variable=var,boundary_value=float(val),unit=unit_,formula='see mass() closed form; all other original controls fixed',status='CONDITIONAL_ZERO_EFFECT_BOUNDARY'))
 existing=frame(S1/'PATH2_BOUNDARY_DEFINITION_TABLE.csv')
 for var,val in [('additional_mass_S_minus_LP',b),('utilization_at_qS',ustar),('mean_full_cell_voltage',vstar)]:ck('T08 analytic boundary matches source',abs(float(val)-float(existing[existing.input_variable==var].value.iloc[0]))<1e-10,var)
 table('PATH2_BOUNDARY_ANALYSIS.csv',bounds)
 energy=frame(P/'C_T08_ENERGY_FULL.csv');cl=energy[energy.dataset=='CLASSICAL'];rows=[];ops=[];kernels={};minslopes=[]
 for number,(h,g) in enumerate(cl.groupby('trajectory_sha256'),1):
  x=g.iloc[0];p=pin(x.trajectory_path,'old C saved speed',h);df=pd.read_csv(p,usecols=['timestamp_s','speed_m_s']);ts=df.timestamp_s.to_numpy();v=df.speed_m_s.to_numpy();cur=v[1:];dv=cur**2-v[:-1]**2;ds=cur*np.diff(ts);ck('saved trajectory timestamps and nonnegative speeds',np.all(np.diff(ts)==1) and np.all(v>=0),p)
  ck('C common nonpack running mass',abs(float(x.running_mass_kg)-float(LP)-float(nonpack))<1e-8,p)
  for rolling,pressure in [('CRR_LOWER_BOUND',4.5),('CRR_UPPER_BOUND',2.6)]:
   crr=.005+(.01+.0095*(3.6*cur/100)**2)/pressure;aa=(9.80665*crr*ds+.5*dv)/3600;bb=(.5*61*dv+.5*1.2041*1.175*cur**2*ds)/3600;al=aa*lo+bb;ah=aa*hi+bb;always=(al>0)&(ah>0);sw=(al>0)!=(ah>0);ca=float(aa[always].sum());cb=float(bb[always].sum());sa=aa[sw].copy();sb=bb[sw].copy()
   def fun(ms):
    ms=np.atleast_1d(ms);return (ca*ms+cb+np.maximum(ms[:,None]*sa[None,:]+sb[None,:],0).sum(axis=1))/.9
   kernels[(h,rolling)]=(ca,cb,sa,sb);slope=(ca+sa[sa*lo+sb>0].sum())/.9;ck('positive DC mass derivative throughout interval',slope>0,p,f'{rolling}:{slope}Wh/kg');minslopes.append(slope)
   massLP=float(nonpack+LP);massS=float(nonpack+SS);eLP,eS=fun([massLP,massS]);rLP,zLP=evaluate(ts,v,freeze,pressure,{'running_mass_kg':massLP});rS,zS=evaluate(ts,v,freeze,pressure,{'running_mass_kg':massS})
   ck('compact energy agrees with frozen kernel LP',abs(eLP-rLP['net_DC_Wh'])<1e-7,p);ck('compact energy agrees with frozen kernel S',abs(eS-rS['net_DC_Wh'])<1e-7,p)
   for sid,e in [('COND_LP_REF',eLP),('COND_S200_REF',eS)]:ck('new endpoint matches saved energy',abs(e-float(g[(g.rolling_case==rolling)&(g.scenario_id==sid)].net_DC_Wh.iloc[0]))<1e-7,p)
   mbs=np.array([float(nonpack+c['LP']) for c in cases]);mss=np.array([float(nonpack+c['S']) for c in cases]);ck('all new running masses within verified monotonic interval',mbs.min()>=lo and mss.min()>=lo and mbs.max()<=hi and mss.max()<=hi,p)
   bases=fun(mbs);alts=fun(mss)
   for c,eb,es,mb,ms in zip(cases,bases,alts,mbs,mss):
    dm=c['LP']-c['S'];de=eb-es;relative_mass=float(dm)/mb;relative_energy=de/eb;denq=(c['q']*c['u']-qLP)/qLP
    if dm==0:ck('mass cancellation gives exact DC cancellation',abs(de)<1e-10,p,c['case_id'])
    else:ck('mass/DC signs agree on verified interval',float(dm)*de>0,p,c['case_id'])
    rows.append(dict(model=c['model'],case_id=c['case_id'],axis=c['axis'],trajectory_sha256=h,physical_instance_id=x.physical_instance_id,parent_id=x.parent_id,group_id=x.group_id,scale=x.scale_id,rolling_case=rolling,q_Ah_kg=c['q'],utilization=c['u'],voltage_V=c['V'],common_fixed_mass_kg=c['fixed'],additional_or_unknown_delta_kg=c['delta'],baseline_pack_or_probe_kg=float(c['LP']),alternate_pack_or_probe_kg=float(c['S']),delta_mass_fraction=str(dm),delta_mass_kg=float(dm),baseline_running_mass_kg=mb,alternate_running_mass_kg=ms,baseline_DC_Wh=eb,alternate_DC_Wh=es,delta_DC_Wh=de,individual_saving_percent=100*relative_energy,transfer_K_EM=relative_energy/relative_mass if dm!=0 else None,transfer_K_Eq=relative_energy/denq if c['axis']=='q_only' and denq!=0 else None,mass_scope=c['scope'],value_type='deterministic frozen-trajectory model calculation'))
   mask=zLP['wheel']>0;parts={key:float((zLP[key]-zS[key])[mask].sum())/.9 for key in ['roll','translational','rotational','aero']};branch=eLP-eS-sum(parts.values())
   ops.append(dict(trajectory_sha256=h,physical_instance_id=x.physical_instance_id,parent_id=x.parent_id,group_id=x.group_id,scale=x.scale_id,rolling_case=rolling,distance_km=ds.sum()/1000,restarts=int(np.sum((v[:-1]<=1e-9)&(v[1:]>1e-9))),moving_mean_speed_m_s=float(v[v>0].mean()),positive_dv2=float(np.maximum(dv,0).sum()),baseline_DC_Wh=eLP,alternate_DC_Wh=eS,delta_DC_Wh=eLP-eS,individual_saving_percent=100*(eLP-eS)/eLP,delta_mass_kg=float(b),relative_mass_saving_percent=100*float(b)/massLP,transfer_K_EM=((eLP-eS)/eLP)/(float(b)/massLP),W1_mask_delta_Wh=parts['roll'],W3_mask_delta_Wh=parts['translational'],W2_mask_delta_Wh=parts['aero'],W4_mask_delta_Wh=parts['rotational'],branch_correction_Wh=branch,min_derivative_Wh_kg=slope,mass_interval_min_kg=lo,mass_interval_max_kg=hi,branch_switch_count=int(np.sum((zLP['wheel']>0)!=(zS['wheel']>0)))))
  if number%100==0:print('C trajectories',number,flush=True)
 res=pd.DataFrame(rows);operation=pd.DataFrame(ops);table('PATH2_SENSITIVITY_RESULTS.csv',res);table('PATH2_OPERATION_CONDITION_ANALYSIS.csv',operation)
 summaries=[]
 for keys,g in res.groupby(['model','case_id','axis','rolling_case'],sort=True):
  q=g.iloc[0];summaries.append(dict(zip(['model','case_id','axis','rolling_case'],keys))|dict(trajectories=len(g),q_Ah_kg=q.q_Ah_kg,utilization=q.utilization,voltage_V=q.voltage_V,fixed_mass_kg=q.common_fixed_mass_kg,delta_kg=q.additional_or_unknown_delta_kg,delta_mass_kg=q.delta_mass_kg,baseline_pack_kg=q.baseline_pack_or_probe_kg,alternate_pack_kg=q.alternate_pack_or_probe_kg,baseline_sum_Wh=g.baseline_DC_Wh.sum(),delta_sum_Wh=g.delta_DC_Wh.sum(),total_weighted_saving_percent=100*g.delta_DC_Wh.sum()/g.baseline_DC_Wh.sum(),mean_individual_saving_percent=g.individual_saving_percent.mean(),median_individual_saving_percent=g.individual_saving_percent.median(),sd_individual_saving_percent=g.individual_saving_percent.std(ddof=1),min_individual_saving_percent=g.individual_saving_percent.min(),max_individual_saving_percent=g.individual_saving_percent.max(),mean_transfer_K_EM=g.transfer_K_EM.mean(),mean_transfer_K_Eq=g.transfer_K_Eq.mean(),scope=q.mass_scope))
 su=pd.DataFrame(summaries);table('PATH2_SENSITIVITY_SUMMARY.csv',su)
 bins=[];features=['distance_km','restarts','moving_mean_speed_m_s','positive_dv2'];unique=operation.drop_duplicates('trajectory_sha256');opbins=operation.copy()
 for feature in features:
  breaks=np.quantile(unique[feature],[.25,.5,.75]);opbins[feature+'_quartile']=np.searchsorted(breaks,operation[feature],side='left')+1
  for (rolling,quartile),g in opbins.groupby(['rolling_case',feature+'_quartile']):bins.append(dict(feature=feature,rolling_case=rolling,quartile=int(quartile),thresholds=json.dumps(breaks.tolist()),trajectories=len(g),delta_DC_Wh_mean=g.delta_DC_Wh.mean(),saving_percent_mean=g.individual_saving_percent.mean(),saving_percent_median=g.individual_saving_percent.median(),saving_percent_sd=g.individual_saving_percent.std(ddof=1),total_weighted_saving_percent=100*g.delta_DC_Wh.sum()/g.baseline_DC_Wh.sum(),scope='descriptive outcome-independent covariate quantiles; confounding not removed'))
 table('PATH2_OPERATION_STRATA.csv',bins);table('PATH2_OPERATION_PAIRED_FEATURES.csv',opbins)
 # Group resampling keeps trajectory/Crr pairing. Only endpoint total ratio receives a statistical sensitivity interval.
 groups=sorted(operation.group_id.unique());weights=np.random.default_rng(20261102).multinomial(len(groups),np.full(len(groups),1/len(groups)),size=10000);ci=[]
 for rolling,g in operation.groupby('rolling_case'):
  a=g.groupby('group_id')[['delta_DC_Wh','baseline_DC_Wh']].sum().reindex(groups,fill_value=0);vals=100*(weights@a.delta_DC_Wh)/(weights@a.baseline_DC_Wh);ci.append(dict(rolling_case=rolling,trajectories=len(g),groups=len(groups),point=100*g.delta_DC_Wh.sum()/g.baseline_DC_Wh.sum(),lower95=np.quantile(vals,.025),upper95=np.quantile(vals,.975),resamples=10000,seed=20261102,scope='hypothetical demand-group resampling sensitivity; not material/model error CI'))
 table('PATH2_GROUP_SENSITIVITY_INTERVALS.csv',ci)
 plt=plotting();qsu=su[(su.model=='T08')&(su.axis=='q_only')];fig,ax=plt.subplots(figsize=(7,4))
 for rc,g in qsu.groupby('rolling_case'):ax.plot(g.q_Ah_kg,g.total_weighted_saving_percent,label=rc)
 ax.set(xlabel='Cathode capacity proxy (Ah/kg)',ylabel='Total-weighted DC saving (%)',title='T08; fixed trajectories, u=1, V=3.5');ax.legend();savefig(fig,'PATH2_FIGURES','F1_capacity_transmission');plt.close(fig)
 fig,axs=plt.subplots(1,2,figsize=(11,4))
 for ax,(rc,g) in zip(axs,su[(su.model=='T08')&(su.axis=='u_V')].groupby('rolling_case')):
  piv=g.pivot(index='utilization',columns='voltage_V',values='total_weighted_saving_percent');im=ax.contourf(piv.columns,piv.index,piv.to_numpy(),levels=15,cmap='coolwarm');ax.contour(piv.columns,piv.index,piv.to_numpy(),levels=[0],colors='black');ax.set(title=rc,xlabel='S mean full-cell voltage (V)',ylabel='S utilization');fig.colorbar(im,ax=ax,label='DC saving (%)')
 savefig(fig,'PATH2_FIGURES','F2_voltage_utilization_boundary');plt.close(fig)
 fig,ax=plt.subplots(figsize=(7,4))
 for policy,g in pd.DataFrame(t9rows).query('V_common==3.5').groupby('policy'):ax.plot(g.uS,g.b_known_kg,'o-',label='T09 '+policy)
 z=su[(su.model=='T08')&(su.axis=='u_V')&(su.voltage_V==3.5)&(su.rolling_case=='CRR_LOWER_BOUND')];ax.plot(z.utilization,z.delta_mass_kg,'s--',label='T08 common coatings');ax.axhline(0,color='black',lw=.7);ax.set(xlabel='S utilization',ylabel='Known mass boundary b (kg)',title='Separate accounting structures; complete T09 pack unknown');ax.legend();savefig(fig,'PATH2_FIGURES','F3_structure_boundaries');plt.close(fig)
 fig,ax=plt.subplots(figsize=(7,4))
 for model in ['T08','T09_MASS_PROBE']:
  z=su[(su.model==model)&su.axis.isin(['additional_mass','unknown_mass_difference'])&(su.rolling_case=='CRR_LOWER_BOUND')];ax.scatter(z.delta_mass_kg,z.total_weighted_saving_percent,label=model)
 ax.axhline(0,color='black',lw=.7);ax.axvline(0,color='black',lw=.7);ax.set(xlabel='Net mass saving b-delta (kg)',ylabel='DC saving (%)',title='Mass cancellation and DC zero boundary');ax.legend();savefig(fig,'PATH2_FIGURES','F4_cancellation');plt.close(fig)
 fig,axs=plt.subplots(1,2,figsize=(10,4))
 for rc,g in operation.groupby('rolling_case'):axs[0].scatter(g.distance_km,g.delta_DC_Wh,s=8,alpha=.5,label=rc);axs[1].scatter(g.restarts,g.individual_saving_percent,s=8,alpha=.5,label=rc)
 axs[0].set(xlabel='Observed distance (km)',ylabel='DC saving (Wh)');axs[1].set(xlabel='Restarts',ylabel='Individual DC saving (%)');axs[0].legend(fontsize=7);savefig(fig,'PATH2_FIGURES','F5_operation_dependence');plt.close(fig)
 finish('PATH2_ANALYSIS',t0,dict(trajectories=460,rolling_cases=2,sensitivity_rows=len(res),parameter_cases=len(cases),T09_common_rows=len(t9rows),min_derivative_Wh_kg=min(minslopes),mass_boundary_kg=float(b),utilization_boundary=float(ustar),voltage_boundary_V=float(vstar)))
if __name__=='__main__':main()
