import json
import math

import pytest

from test_statistics import fixture_module
from kmd_toc.descriptive_v1.pipeline import write_analysis
from kmd_toc.descriptive_v1.statistics import summary


def test_primary_errorbars_actual_sd_not_mcse_and_box_stats(tmp_path,fixture_module,monkeypatch):
    import matplotlib
    matplotlib.use('Agg')
    from matplotlib.axes import Axes
    bars=[];boxes=[]
    oldbar=Axes.errorbar;oldbox=Axes.bxp
    def bar(self,*a,**kw):
        bars.append((a[1],kw['yerr']));return oldbar(self,*a,**kw)
    def box(self,stats,*a,**kw):
        boxes.extend(stats);assert kw['shownotches'] is False
        return oldbox(self,stats,*a,**kw)
    monkeypatch.setattr(Axes,'errorbar',bar);monkeypatch.setattr(Axes,'bxp',box)
    path=fixture_module.fixture(tmp_path/'fixture');write_analysis(path,tmp_path/'out')
    meta=json.loads((tmp_path/'out/FIGURE_SPEC.json').read_text())
    wanted=summary([90,91,93,89,92,95]);target=next(b for b in meta['bars'] if b['tag']=='S1/D/D')
    assert target['yerr']==wanted['SD'] and target['yerr']!=pytest.approx(wanted['SD']/math.sqrt(6))
    assert target['lower']==target['mean']-wanted['SD'] and target['upper']==target['mean']+wanted['SD']
    assert len(bars)==len(meta['bars']) and all(b['quantity']=='sample_SD' for b in meta['bars'])
    assert any(b['fliers']==[140.0] for b in boxes)
    assert len(list((tmp_path/'out/figures').glob('*.png')))==8
    assert len(list((tmp_path/'out/figures').glob('*.pdf')))==8
    assert len(list((tmp_path/'out/figures/internal').glob('*.png')))==4
    assert meta['data_role']=='synthetic_statistics_fixture'
    assert all('MCSE' not in r['name'] for r in meta['figures'] if not r['internal'])
