"""Additional B-D/C-D paired rates and dual plots. Never use MCSE as yerr."""
from pathlib import Path
from kmd_toc.descriptive_v1.statistics import summary


def render_direct(report, out):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    out = Path(out)
    meta = {'error_bar': 'sample_SD', 'unit': 'percent', 'bars': [], 'figures': []}
    fixture = report['data_role'] == 'synthetic_statistics_fixture'
    for name in ('relative_D', 'relative_W', 'dual_box', 'dual_mean_SD'):
        fig, axes = plt.subplots(1, 3, figsize=(11, 3.5))
        for ax, scale in zip(axes, ('S1', 'S2', 'S3')):
            for i, base in enumerate(('B', 'C'), 1):
                if name.startswith('relative'):
                    metric = name[-1]
                    row = next(r for r in report['comparisons'] if (r['scale'],r['baseline'],r['comparison'],r['metric']) == (scale,base,'D',metric))
                    vals = row.get('trial_relative_rates') or []
                    aggregate = row.get('relative_rate_of_means_percent')
                else:
                    row = next(r for r in report['direct_dual_improvement'] if (r['scale'],r['baseline']) == (scale,base))
                    vals = [v for v in (row['trial_values_percent'] or []) if v is not None]
                    aggregate = row['I_dual_of_means_percent']
                z = summary([v for v in vals if v is not None])
                if z['mean'] is not None:
                    if name == 'dual_box':
                        ax.bxp([{'q1':z['Q1'],'q3':z['Q3'],'med':z['median'],
                                 'whislo':z['whisker_low'],'whishi':z['whisker_high'],'fliers':z['outliers']}],
                               positions=[i], manage_ticks=False)
                    elif z['SD'] is not None:
                        ax.errorbar(i, z['mean'], yerr=z['SD'], fmt='o', capsize=4)
                        meta['bars'].append({'scale':scale,'baseline':base,'figure':name,
                                             'mean':z['mean'],'yerr':z['SD'],'quantity':'sample_SD'})
                    else: ax.plot(i,z['mean'],'x',label='SD undefined')
                elif aggregate is not None:
                    # Explicit scalar; never manufacture a distribution from means.
                    ax.plot(i,aggregate,'D',mfc='none',label='Index/rate of group means only')
                else: ax.text(i,.5,'HOLD: no data',ha='center',transform=ax.get_xaxis_transform(),fontsize=7)
            ax.set_xticks([1,2],['D|B','D|C']);ax.set_xlim(.5,2.5)
            ax.set_title(scale);ax.set_ylabel('Improvement (%)');ax.axhline(0,color='0.7',lw=.5)
            if ax.get_legend_handles_labels()[0]:ax.legend(fontsize=6)
        fig.suptitle('FIXTURE ONLY — NOT DELIVERY RESULTS' if fixture else 'Audited registered outer trials')
        fig.tight_layout()
        for ext in ('png','pdf'):fig.savefig(out/f'{name}.{ext}',dpi=130)
        plt.close(fig);meta['figures'].append(name)
    return meta
