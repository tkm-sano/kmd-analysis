"""Analysis-only checks; does not launch any planning method."""
import sys
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
from run_comparison_design_supplement import success_pair
from kmd_toc.comparison_v1.design import welch_halfwidth


def test_cost_allocation_with_one_observed_constant_metric_is_only_point_planning():
    c,d=success_pair(4,0,10,20,1,'variance_cost')
    assert d==2 and c>2
    assert welch_halfwidth(4,0,c,d)<=1
    assert success_pair(None,4,10,20,1,'uniform_all') is None
    assert success_pair(0,4,10,20,1,'variance_cost')[0]==2


def test_uniform_all_quality_floor_starts_from_equal_groups():
    c,d=success_pair(4,16,10,20,1,'uniform_all')
    assert c==d
    assert welch_halfwidth(4,16,c,d)<=1
