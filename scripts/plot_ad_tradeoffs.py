"""Publication-exportable paired D/W plot; no synthetic combined minima."""
import csv
import os
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(os.environ.get('KMD_AD_OUTPUT_ROOT','output/toc_delivery/ad_pipeline_20261112'))
if __name__=='__main__':
    rows=[r for r in csv.DictReader((ROOT/'A_TO_D_COMPARISON.csv').open()) if r['scenario']=='S1' and r['status']=='FEASIBLE' and r['is_replicate']=='False']
    fig,ax=plt.subplots(figsize=(7,4.5),layout='constrained')
    for method,color,marker in [('A2','tab:blue','o'),('A3','tab:cyan','o'),('B','tab:orange','s'),('C','tab:green','^'),('D','tab:purple','D')]:
        r=[r for r in rows if r['method']==method]
        ax.scatter([float(q['D_km']) for q in r],[float(q['W_min']) for q in r],label=method,c=color,marker=marker,s=65,alpha=.8)
    ax.set(xlabel='Total directed road distance D [km]',ylabel='Total loading wait W [min]',title='S1: feasible plans on the same frozen demand and road OD')
    ax.grid(alpha=.2);ax.legend(title='Method / rule');fig.text(.5,-.01,'Each point is one plan. A1 infeasible. D is a limited macro AOA hybrid; no quantum advantage claim.',ha='center',fontsize=8)
    fig.savefig(ROOT/'S1_D_W_TRADEOFF.pdf',bbox_inches='tight');fig.savefig(ROOT/'S1_D_W_TRADEOFF.png',dpi=180,bbox_inches='tight')
