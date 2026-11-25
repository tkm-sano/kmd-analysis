"""Publication figures: only mean +/- sample SD. MCSE lives under internal/."""
from pathlib import Path
import math
from .statistics import summary


def render(report,rows,out):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    out=Path(out);out.mkdir(parents=True,exist_ok=False);(out/'internal').mkdir()
    role=report['data_role'];banner='STATISTICS FIXTURE ONLY - NOT DELIVERY RESULTS' if role=='synthetic_statistics_fixture' else 'Verified outer trials'
    scales=('S1','S2','S3');methods=('B','C','D');metadata={'data_role':role,'error_bar':'sample_SD','figures':[],'bars':[]}
    def values(scale,method,metric):return [r[metric] for r in rows if r['eligible'] and (r['scale'],r['method'])==(scale,method)]
    def save(fig,name,*,internal=False):
        fig.suptitle(banner,fontsize=10);fig.tight_layout(rect=(0,0.04,1,.94))
        fig.text(.5,.008,'Boxes: Tukey 1.5 IQR; bars: mean +/- 1 sample SD; no significance interpretation.',ha='center',fontsize=7)
        base=out/'internal' if internal else out
        for ext in ('png','pdf'):fig.savefig(base/f'{name}.{ext}',dpi=160)
        plt.close(fig);metadata['figures'].append({'name':name,'internal':internal})
    def box(ax,data,labels):
        stats=[];positions=[]
        for i,v in enumerate(data,1):
            z=summary(v)
            if v:
                stats.append({'q1':z['Q1'],'q3':z['Q3'],'med':z['median'],'whislo':z['whisker_low'],
                              'whishi':z['whisker_high'],'fliers':z['outliers']});positions.append(i)
                # Show every observed point, including small and zero-spread samples.
                ax.scatter([i]*len(v),v,s=10,color='0.35',alpha=.5,zorder=3)
            ax.text(i,.98,f'J={len(v)}',transform=ax.get_xaxis_transform(),ha='center',va='top',fontsize=7)
        if stats:ax.bxp(stats,positions=positions,showfliers=True,shownotches=False,manage_ticks=False)
        else:ax.text(.5,.5,'No eligible observations',transform=ax.transAxes,ha='center')
        ax.set_xticks(range(1,len(labels)+1),labels);ax.set_xlim(.5,len(labels)+.5)
    def point(ax,x,mean,sd,tag):
        if mean is None:return
        if sd is None:
            ax.plot(x,mean,'x',color='C0');ax.annotate('SD undefined',(x,mean),fontsize=6,xytext=(3,4),textcoords='offset points')
        else:
            ax.errorbar(x,mean,yerr=sd,fmt='o',capsize=4,color='C0')
            metadata['bars'].append({'tag':tag,'mean':mean,'yerr':sd,'lower':mean-sd,'upper':mean+sd,'quantity':'sample_SD'})
    for metric in ('D','W'):
        unit='Distance (km)' if metric=='D' else 'Total loading wait (min)'
        for kind in ('box','mean_SD'):
            fig,axes=plt.subplots(1,3,figsize=(12,4))
            for ax,scale in zip(axes,scales):
                data=[values(scale,m,metric) for m in methods]
                if kind=='box':box(ax,data,list(methods))
                else:
                    for i,v in enumerate(data,1):
                        z=summary(v);point(ax,i,z['mean'],z['SD'],f'{scale}/{methods[i-1]}/{metric}')
                        ax.text(i,.98,f'J={len(v)}',transform=ax.get_xaxis_transform(),ha='center',va='top',fontsize=7)
                    ax.set_xticks([1,2,3],methods);ax.set_xlim(.5,3.5)
                    if not any(data):ax.text(.5,.5,'No eligible observations',transform=ax.transAxes,ha='center')
                refs=[r for r in report['comparisons'] if r['scale']==scale and r['metric']==metric and r['baseline']=='A' and r.get('A_display_allowed')]
                if refs:ax.axhline(refs[0]['A_value'],color='C3',linestyle='--',label='A external scalar');ax.legend(fontsize=7)
                else:ax.text(.02,.02,'A: comparability unconfirmed',transform=ax.transAxes,fontsize=6)
                ax.set_title(scale);ax.set_ylabel(unit);ax.grid(axis='y',alpha=.2)
            save(fig,f'{metric}_{kind}')
        fig,axes=plt.subplots(1,3,figsize=(14,4))
        for ax,scale in zip(axes,scales):
            groups=[r for r in report['comparisons'] if r['scale']==scale and r['metric']==metric]
            for i,r in enumerate(groups,1):point(ax,i,r['mean_delta'],r['SD_delta'],f'{scale}/{r["baseline"]}-{r["comparison"]}/delta_{metric}')
            ax.set_xticks(range(1,6),[f'{r["baseline"]}->{r["comparison"]}' for r in groups],rotation=20)
            ax.set_title(scale);ax.set_ylabel('Y-X: '+unit);ax.axhline(0,color='0.7',linewidth=.5)
            if all(r['mean_delta'] is None for r in groups):ax.text(.5,.5,'No eligible contrasts',transform=ax.transAxes,ha='center')
        save(fig,f'delta_{metric}_mean_SD')
        # Internal distribution/stability diagnostics. These are not chosen J.
        fig,axes=plt.subplots(3,3,figsize=(12,9))
        for rr,scale in enumerate(scales):
            for cc,m in enumerate(methods):
                ax=axes[rr,cc];v=values(scale,m,metric)
                checkpoints=list(range(1,len(v)+1)) if len(v)<=20 else sorted({1,len(v),*(2**k for k in range(int(math.log2(len(v)))+1))})
                if checkpoints:box(ax,[v[:n] for n in checkpoints],[str(n) for n in checkpoints])
                else:ax.text(.5,.5,'No eligible observations',transform=ax.transAxes,ha='center')
                ax.set_title(f'{scale} / {m}');ax.set_xlabel('Valid prefix count (display only)');ax.set_ylabel(unit)
        save(fig,f'{metric}_prefix_boxes',internal=True)
        fig,axes=plt.subplots(1,3,figsize=(12,4))
        for ax,scale in zip(axes,scales):
            for m in methods:
                z=[r for r in report['prefixes'] if r['scale']==scale and r['method']==m and r['metric']==metric and r['MCSE'] is not None]
                if z:ax.plot([r['J'] for r in z],[r['MCSE'] for r in z],marker='.',label=m)
            ax.set_title(scale+' / internal J review');ax.set_xlabel('Valid outer count');ax.set_ylabel('MCSE (not result error bars)')
            if ax.lines:ax.legend()
            else:ax.text(.5,.5,'MCSE unavailable',transform=ax.transAxes,ha='center')
        # Deliberately a separately labelled internal figure with no error bars.
        fig.suptitle(banner+' / INTERNAL MCSE ONLY',fontsize=10);fig.tight_layout(rect=(0,0,1,.9))
        for ext in ('png','pdf'):fig.savefig(out/'internal'/f'{metric}_MCSE.{ext}',dpi=160)
        plt.close(fig);metadata['figures'].append({'name':f'{metric}_MCSE','internal':True,'quantity':'MCSE_internal_only'})
    for kind in ('box','mean_SD'):
        fig,axes=plt.subplots(1,3,figsize=(12,4))
        for ax,scale in zip(axes,scales):
            data=[]
            for m in ('B','D'):
                group=next((r for r in report['dual_trials'] if r['scale']==scale and r['method']==m),None)
                data.append([x for x in group['values'] if x is not None] if group else [])
            if kind=='box':box(ax,data,['B|C','D|C'])
            else:
                for i,v in enumerate(data,1):
                    z=summary(v);point(ax,i,z['mean'],z['SD'],f'{scale}/{("B","D")[i-1]}/I_dual')
                ax.set_xticks([1,2],['B|C','D|C']);ax.set_xlim(.5,2.5)
                if not any(data):ax.text(.5,.5,'No registered C references',transform=ax.transAxes,ha='center')
            ax.axhline(0,color='0.6',linestyle='--',label='Zero improvement threshold (positive C denominators only)')
            ax.set_title(scale);ax.set_ylabel('Trial I_dual relative to C (%)')
        save(fig,f'I_dual_{kind}')
    return metadata
