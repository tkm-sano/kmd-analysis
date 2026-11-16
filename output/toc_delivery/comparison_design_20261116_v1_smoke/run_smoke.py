import sys
from pathlib import Path
sys.path.insert(0,'scripts');sys.path.insert(0,'src')
from run_comparison_design import plan_for
from kmd_toc.comparison_v1.contract import read,dump,register
from kmd_toc.comparison_v1.design import RULES_PATH
from kmd_toc.comparison_v1.execution import run_registered
from kmd_toc.comparison_v1.evaluation import aggregate
root=Path('output/toc_delivery/comparison_design_20261116_v1_smoke')
r=read(RULES_PATH);p=plan_for(r,r['profiles'][0],'selection_pilot',1,2026111600)
p['cases']=p['cases'][:1];p['cases'][0].update(scale='ART_N12',scenario_id='artificial-fixture-only',input_dir='output/toc_delivery/comparison_integration_v1_20261115_inputs/ART_N12')
p['runs']=[x for x in p['runs'] if x['case_id']=='S1'];p['reference_groups']=p['reference_groups'][:1]
dump(root/'PLAN.json',p)
f=register(root/'PLAN.json',root/'registered');run_registered(f);print(aggregate(f,root/'tables'))
