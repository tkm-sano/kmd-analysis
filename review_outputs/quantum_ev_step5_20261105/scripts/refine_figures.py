from pathlib import Path
import pandas as pd,numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
O=Path(__file__).resolve().parents[1]
d=pd.read_csv(O/'data/B_PLAN_GAPS_36800.csv');ic=pd.read_csv(O/'data/INPUT_CONFIG_MEANS_3680.csv');ip=pd.read_csv(O/'data/INPUT_MEANS_460.csv');metrics=['delta_s','abs_delta_s','relative_gap_percent']
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42,'savefig.dpi':300})
colors=plt.cm.tab10(np.arange(8));configs=sorted(d.config_id.unique());
def save(fig,name):
 fig.savefig(O/'figures'/f'{name}.png',bbox_inches='tight');fig.savefig(O/'figures'/f'{name}.pdf',bbox_inches='tight');plt.close(fig)
fig,ax=plt.subplots(figsize=(6.3,4.7))
for c,color in zip(configs,colors):
 h=d[d.config_id==c];ax.scatter(h.J_greedy_s,h.J_candidate_s,s=7,alpha=.3,label=c,color=color,rasterized=True)
m=max(d.J_candidate_s.max(),d.J_greedy_s.max());ax.plot([0,m],[0,m],color='black',lw=1,label='Equal objective');ax.set(xlabel='Greedy directed round-trip travel J (s)',ylabel='Candidate directed round-trip travel J (s)',title='B: 36,800 saved plans; paired by 460 inputs');ax.legend(fontsize=8,loc='upper left',ncol=2);fig.text(.5,.005,'8 settings x 10 reps/input; dependent repeats; CPU simulations',ha='center',fontsize=8);save(fig,'F1_paired_objectives')
fig,axs=plt.subplots(1,2,figsize=(6.3,3.4))
for ax,col,label in zip(axs,['delta_s','relative_gap_percent'],['Candidate minus greedy (s)','Relative gap vs greedy (%)']):
 ax.hist(d[col],bins=50,color='#236785',alpha=.85);ax.axvline(0,color='black',lw=.7);ax.set(xlabel=label,ylabel='Saved plans (count)');ax.set_title(f'n = 36,800; median = {d[col].median():.3f}',fontsize=9)
fig.suptitle('B: signed and relative gaps (dependent repeats)',fontsize=10);fig.tight_layout(rect=(0,.04,1,.94));fig.text(.5,.005,'Positive = worse; n = descriptive count of dependent plans.',ha='center',fontsize=8);save(fig,'F2_gap_distributions')
fig,axs=plt.subplots(2,1,figsize=(6.3,5.8),sharex=True)
for ax,col,lab in zip(axs,metrics[::2],['Signed gap (s)','Relative gap (%)']):
 ax.boxplot([ic.loc[ic.config_id==c,col] for c in configs],tick_labels=['Active p3','Coherent2','Coherent4','CVaR01 p2','CVaR10 p2','Grover p2','Grover p3','Mean p2'],showfliers=True,flierprops={'markersize':2});ax.set_ylabel(lab);ax.axhline(0,color='black',lw=.7)
axs[1].tick_params(axis='x',rotation=35,labelsize=9);fig.suptitle('B: 460 input means per setting (10 reps/input)',fontsize=11);fig.tight_layout(rect=(0,.04,1,.95));fig.text(.5,.003,'Median / quartiles; whiskers 1.5 IQR; outliers retained; paired inputs.',ha='center',fontsize=8);save(fig,'F3_setting_input_boxes')
fig,axs=plt.subplots(2,1,figsize=(6.3,5.0),sharex=True)
ordered=ip.sort_values('problem_id');x=np.arange(len(ordered));
for ax,col,lab in zip(axs,['delta_s','relative_gap_percent'],['Mean signed gap (s)','Mean relative gap (%)']):
 for sc,color in zip(sorted(ip.scale.unique()),plt.cm.Set2(np.arange(6))):
  mask=ordered.scale.eq(sc).to_numpy();ax.scatter(x[mask],ordered.loc[mask,col],s=11,label=sc,color=color)
 ax.set_ylabel(lab);ax.axhline(0,color='black',lw=.7)
axs[0].legend(ncol=6,fontsize=8);axs[1].set_xlabel('Input rank in problem_id order (460 inputs)\nEach point averages 8 settings x 10 reps');fig.suptitle('B: input-level gaps vs greedy; equal input weights',fontsize=11);fig.tight_layout();save(fig,'F4_input_gaps')
