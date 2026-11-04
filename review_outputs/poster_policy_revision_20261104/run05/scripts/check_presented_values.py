"""Check transcription of displayed numbers; no new scientific experiment."""
from pathlib import Path
import csv,json
R=Path(__file__).resolve().parents[1]
a=json.loads((R/'evidence/EXTENDED_AUDIT.json').read_text())
c=list(csv.DictReader((R/'evidence/C_MASS_DC_RECONCILIATION.csv').open()))[0]
b=list(csv.DictReader((R/'evidence/C_COMPONENT_BOUNDARIES.csv').open()))
s=(R/'poster_text.txt').read_text();checks=[]
def check(label,value,source):
 ok=value in s;checks.append(dict(item=label,expected_text=value,status='PASS' if ok else 'FAIL',source=source));assert ok,checks[-1]
for n in [3,4,5,25,100,125]:
 rows=[v for v in a['normalized_scale_results'] if v['n']==n and v['config_id'].startswith('GROVER_')]
 lo,hi=sorted(v['mean_delta_s'] for v in rows)
 def f(v):return ('−' if v<0 else '+' if v>0 else '')+f'{abs(v):,.2f}'
 val=f(lo) if round(lo,2)==round(hi,2) else f(lo)+'〜'+f(hi)
 check('GM平均秒差_'+str(n),val,'B_NORMALIZED_BY_SCALE_CONFIG.csv: input/rep aggregation unchanged')
for label,key,digits in [('推計電池質量','battery_reduction_percent',2),('走行時総質量','running_reduction_percent',3),('走行DC','DC_reduction_percent',3)]:check(label,f'{float(c[key]):.{digits}f}%','C_MASS_DC_RECONCILIATION.csv; LP denominator')
for key in ['LP_pack_kg','S_pack_kg','LP_running_kg','S_running_kg']:check(key,f'{float(c[key]):.2f}','C_MASS_DC_RECONCILIATION.csv')
for row in b:check(row['policy'],f"{float(row['known_mass_difference_kg']):.2f} kg",'C_COMPONENT_BOUNDARIES.csv; representative designs')
check('入力LP','171.9','121/0.704 Ah/kg');check('入力S','196.0','194/0.99 Ah/kg')
with (R/'evidence/PRESENTATION_VALUE_CHECKS.csv').open('w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=list(checks[0]));w.writeheader();w.writerows(checks)
print('Displayed numerical values match audited sources:',len(checks),'PASS')
