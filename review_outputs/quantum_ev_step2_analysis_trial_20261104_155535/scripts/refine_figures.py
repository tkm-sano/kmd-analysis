from common import *
t=time.perf_counter();plt=plotting();s=frame(O/'QAOA_CONTROLLED_CELL_SUMMARY.csv');q=s[s.method=='QAOA'];fig,axs=plt.subplots(1,3,figsize=(12,4),sharey=True)
for ax,(pid,g) in zip(axs,q.groupby('problem_id')):
 labels=[f"{x.support[:1]}/{x.initial_state[:1]}/{x.mixer[:1]}/p{x.layers}" for x in g.itertuples()];rates=g.primary_optimal_rep0_rate.to_numpy();err=np.maximum(np.array([rates-g.primary_optimal_Wilson95_lower.to_numpy(),g.primary_optimal_Wilson95_upper.to_numpy()-rates]),0);ax.bar(range(len(g)),rates,yerr=err,capsize=2);ax.set(title=pid,ylabel='Optimal acquisition, rep0 (Wilson95)',ylim=(0,1.08));ax.set_xticks(range(len(g)),labels,rotation=90,fontsize=6)
fig.subplots_adjust(bottom=.30);fig.text(.5,.01,'F/M: full/mirror support; B/U: basis/uniform; G/P: graph/projector; 97 independent learning fits per cell',ha='center',fontsize=8);savefig(fig,'QAOA_CONTROLLED_EXPERIMENT_FIGURES','F1_support_optimal_acquisition');plt.close(fig)
co=frame(O/'QAOA_SAME_ANGLE_DEPHASING.csv');g=co[co.problem_id=='R1_020'];fig,ax=plt.subplots(figsize=(9,4));labels=[];vals=[]
for k,h in g.groupby(['support','initial_state','mixer','layers']):labels.append(f'{k[0][0]}/{k[1][0]}/{k[2][0]}/p{k[3]}');vals.append(h.dephased_minus_Q_expected_s)
ax.boxplot(vals,tick_labels=labels,showfliers=False);ax.tick_params(axis='x',rotation=50);ax.axhline(0,color='black',lw=.7);ax.set(ylabel='Dephased minus Q expected OD (s)',title='Same-angle dephasing, R1_020; expected value is distinct from sampled-best');fig.subplots_adjust(bottom=.28);fig.text(.5,.01,'F/M: full/mirror; B/U: basis/uniform; G/P: graph/projector; 97 learned Q angles per cell',ha='center',fontsize=8);savefig(fig,'QAOA_CONTROLLED_EXPERIMENT_FIGURES','F3_same_angle_dephasing');plt.close(fig)
d=frame(O/'PATH1_STATISTICAL_RESULTS.csv');d=d[d.primary_comparison & d.scale.isin(['R0','R1','R2'])];fig,ax=plt.subplots(figsize=(8,4))
for cfg,h in d.groupby('config_id'):ax.plot(h.scale,h.input_mean_delta_J_mean,'o-',label=cfg)
ax.axhline(0,color='black',lw=.7);ax.set(ylabel='Mean Delta J vs greedy (s)',xlabel='B small-problem scale',title='Small-scale detail of F1; same CSV values');ax.legend(fontsize=6,ncol=2);savefig(fig,'PATH1_STATISTICAL_FIGURES','F1b_small_scale_detail');plt.close(fig)
# Clear the all-zero success-rate panels and retain explicit denominators.
d=frame(O/'PATH1_STATISTICAL_RESULTS.csv');d=d[d.primary_comparison & d.scale.ne('ALL')];configs=sorted(d.config_id.unique());fig,axs=plt.subplots(2,3,figsize=(12,7),sharey=True)
for ax,sc in zip(axs.flat,sorted(d.scale.unique())):
 h=d[d.scale==sc].set_index('config_id').loc[configs];ax.bar(range(len(configs)),h.improve_percent);ax.set(title=sc,ylabel='Improving measurement reps (%)',ylim=(0,100));ax.set_xticks(range(len(configs)),[c.replace('ACTIVE_ADJACENT_P3_GRID','ACTIVE').replace('_P2','') for c in configs],rotation=65,ha='right');ax.text(.5,.8,f'0 / {int(h.scheduled_measurement_reps.iloc[0])} per setting',transform=ax.transAxes,ha='center')
savefig(fig,'PATH1_STATISTICAL_FIGURES','F2_improvement_rates');plt.close(fig)
# Final multi-panel spacing check: keep row labels clear of lower-row titles.
ip=frame(O/'PATH1_INPUT_CONFIG_STATISTICS.csv');ip=ip[ip.primary_comparison];scales=sorted(ip.scale.unique());cs=sorted(ip.config_id.unique());labels=[c.replace('ACTIVE_ADJACENT_P3_GRID','ACTIVE').replace('_P2','') for c in cs];sizes={'R0':3,'R1':4,'R2':5,'R3':25,'R4':100,'R5':125}
fig,axs=plt.subplots(2,3,figsize=(12,8))
for ax,sc in zip(axs.flat,scales):
 h=d[d.scale==sc].set_index('config_id').loc[cs];ax.bar(range(len(cs)),h.improve_percent);ax.set(title=f'{sc} (n={sizes[sc]})',ylabel='Improving measurement reps (%)',ylim=(0,100));ax.set_xticks(range(len(cs)),labels,rotation=65,ha='right');ax.text(.5,.8,f'0 / {int(h.scheduled_measurement_reps.iloc[0])} per setting',transform=ax.transAxes,ha='center')
fig.tight_layout(h_pad=3,w_pad=2);savefig(fig,'PATH1_STATISTICAL_FIGURES','F2_improvement_rates');plt.close(fig)
for filename,field,ylabel in [('F3_global_gap_distribution','exact_gap_percent','Input mean global gap (%)'),('F5_measurement_variation','within_measurement_sd_s','Within-fit measurement SD (s)')]:
 fig,axs=plt.subplots(2,3,figsize=(12,8))
 for ax,sc in zip(axs.flat,scales):
  h=ip[ip.scale==sc];values=[pd.to_numeric(h[h.config_id==c][field],errors='coerce').dropna() for c in cs];ax.boxplot(values,tick_labels=labels,showfliers=False);ax.tick_params(axis='x',rotation=65);ax.set(title=f'{sc} (n={sizes[sc]})',ylabel=ylabel);ax.set_ylim(bottom=0)
 fig.tight_layout(h_pad=3,w_pad=2);savefig(fig,'PATH1_STATISTICAL_FIGURES',filename);plt.close(fig)
fig,axs=plt.subplots(2,3,figsize=(11,8))
for ax,sc in zip(axs.flat,scales):
 h=ip[ip.scale==sc]
 for cfg,label in zip(cs,labels):
  z=h[h.config_id==cfg];ax.scatter(z.JC_s,z.mean_JQ_s,s=9,alpha=.5,label=label)
 lo=min(h.JC_s.min(),h.mean_JQ_s.min());hi=max(h.JC_s.max(),h.mean_JQ_s.max());ax.plot([lo,hi],[lo,hi],color='black',lw=.7);ax.set(title=f'{sc} (n={sizes[sc]})',xlabel='Classical greedy J (s)',ylabel='Quantum mean J (s)')
axs[0,0].legend(fontsize=6);fig.tight_layout(h_pad=2,w_pad=2);savefig(fig,'PATH1_STATISTICAL_FIGURES','F4_paired_objectives');plt.close(fig)

finish('FIGURE_REFINEMENT',t,{'refined':6,'additional':1})
