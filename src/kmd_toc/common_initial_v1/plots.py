from pathlib import Path
from kmd_toc.descriptive_v1.statistics import summary
from .analysis import NAMES


def render(result,output):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    out=Path(output);out.mkdir(exist_ok=False);meta={'bars':'sample_SD','box':'Tukey 1.5 IQR','figures':[],'data_role':result['data_role']}
    from matplotlib import font_manager
    font=Path.home()/'.local/share/fonts/NotoSansJP-Regular.ttf'
    if font.exists():
        font_manager.fontManager.addfont(str(font));plt.rcParams['font.family']=font_manager.FontProperties(fname=str(font)).get_name()
    else:plt.rcParams['font.family']='Droid Sans Fallback'
    meta['bars_detail']=[]
    rows=result['audited_rows'];fixture=result['data_role']=='synthetic_statistics_fixture'
    for metric in ('D','W'):
        for kind in ('box','mean_SD'):
            fig,axes=plt.subplots(1,3,figsize=(11,3.5))
            for ax,scale in zip(axes,('S1','S2','S3')):
                for i,method in enumerate(('B','C','D'),1):
                    vals=[r[metric] for r in rows if r['eligible'] and (r['scale'],r['method'])==(scale,method)]
                    z=summary(vals)
                    if not vals:continue
                    if kind=='box':
                        ax.bxp([{'q1':z['Q1'],'q3':z['Q3'],'med':z['median'],'whislo':z['whisker_low'],
                                 'whishi':z['whisker_high'],'fliers':z['outliers']}],positions=[i],manage_ticks=False)
                    elif z['SD'] is not None:
                        ax.errorbar(i,z['mean'],yerr=z['SD'],fmt='o',capsize=3)
                        meta['bars_detail'].append({'quantity':metric,'scale':scale,'method':method,'yerr':z['SD']})
                    else:ax.plot(i,z['mean'],'x')
                ax.set_xticks([1,2,3],[NAMES[m] for m in ('B','C','D')],rotation=16,ha='right',fontsize=7);ax.set_title(scale)
                ax.set_ylabel('Distance (km)' if metric=='D' else 'Total loading wait (min)')
                # A has no distribution; only a verified external scalar may appear.
                refs=[r for r in result['comparisons'] if r['scale']==scale and r['baseline']=='A' and r['metric']==metric and r.get('A_display_allowed')]
                if refs:ax.axhline(refs[0]['A_value'],ls='--',label='Administrative reference')
            fig.suptitle('FIXTURE ONLY — NOT DELIVERY RESULTS' if fixture else 'Verified shared-initial outer trials')
            fig.tight_layout()
            for ext in ('png','pdf'):fig.savefig(out/f'{metric}_{kind}.{ext}',dpi=130)
            plt.close(fig);meta['figures'].append(metric+'_'+kind)
    fig,axes=plt.subplots(1,3,figsize=(11,3.5))
    for ax,scale in zip(axes,('S1','S2','S3')):
        r=next(r for r in result['common_initial_mean_hypothesis'] if r['scale']==scale)
        for i,key in enumerate(('I_classical_initial_percent','I_hybrid_initial_percent'),1):
            if r.get(key) is not None:ax.plot(i,r[key],'D',mfc='none')
        ax.set_xticks([1,2],[NAMES[m] for m in ('C','D')],rotation=16,ha='right',fontsize=7);ax.set_title(scale);ax.set_ylabel('Index of method means (%)')
    fig.suptitle(('FIXTURE ONLY — ' if fixture else '')+'Indices of means: no fabricated SD error bars')
    fig.tight_layout()
    for ext in ('png','pdf'):fig.savefig(out/f'initial_index_of_means.{ext}',dpi=130)
    plt.close(fig);meta['figures'].append('initial_index_of_means')
    for kind in ('box','mean_SD'):
        fig,axes=plt.subplots(1,3,figsize=(11,4))
        for ax,scale in zip(axes,('S1','S2','S3')):
            trials=[r for r in result['common_initial_trial_hypothesis'] if r['scale']==scale]
            for i,key in enumerate(('I_classical_initial_percent','I_hybrid_initial_percent'),1):
                vals=[r[key] for r in trials if r[key] is not None];z=summary(vals)
                if not vals:continue
                if kind=='box':ax.bxp([{'q1':z['Q1'],'q3':z['Q3'],'med':z['median'],'whislo':z['whisker_low'],
                    'whishi':z['whisker_high'],'fliers':z['outliers']}],positions=[i],manage_ticks=False)
                elif z['SD'] is not None:
                    ax.errorbar(i,z['mean'],yerr=z['SD'],fmt='o',capsize=3)
                    meta['bars_detail'].append({'quantity':key,'scale':scale,'yerr':z['SD']})
                else:ax.plot(i,z['mean'],'x')
            ax.set_xticks([1,2],[NAMES[m] for m in ('C','D')],rotation=16,ha='right',fontsize=7)
            ax.set_title(scale);ax.set_ylabel('Verified trial initial-reference index (%)')
        fig.suptitle(('FIXTURE ONLY — ' if fixture else '')+'Trial indices; distinct from index of means')
        fig.tight_layout()
        for ext in ('png','pdf'):fig.savefig(out/f'initial_trial_index_{kind}.{ext}',dpi=130)
        plt.close(fig);meta['figures'].append('initial_trial_index_'+kind)
    for metric in ('D','W'):
        fig,axes=plt.subplots(1,3,figsize=(11,4))
        for ax,scale in zip(axes,('S1','S2','S3')):
            for i,pair in enumerate((('B','C'),('B','D'),('C','D')),1):
                row=next(r for r in result['comparisons'] if (r['scale'],r['baseline'],r['comparison'],r['metric'])==(scale,*pair,metric))
                if row.get('mean_delta') is None:continue
                if row.get('SD_delta') is not None:
                    ax.errorbar(i,row['mean_delta'],yerr=row['SD_delta'],fmt='o',capsize=3)
                    meta['bars_detail'].append({'quantity':'delta_'+metric,'scale':scale,'comparison':list(pair),'yerr':row['SD_delta']})
                else:ax.plot(i,row['mean_delta'],'x')
            ax.axhline(0,color='gray',lw=0.6);ax.set_title(scale)
            ax.set_xticks([1,2,3],['従来型→古典','従来型→ハイブリッド','古典→ハイブリッド'],rotation=16,ha='right',fontsize=7)
            ax.set_ylabel('Delta distance (km)' if metric=='D' else 'Delta total loading wait (min)')
        fig.suptitle(('FIXTURE ONLY — ' if fixture else '')+'Deltas: SD of registered trial differences only')
        fig.tight_layout()
        for ext in ('png','pdf'):fig.savefig(out/f'delta_{metric}_mean_SD.{ext}',dpi=130)
        plt.close(fig);meta['figures'].append('delta_'+metric+'_mean_SD')
    meta['display_name_mapping']=NAMES
    return meta
