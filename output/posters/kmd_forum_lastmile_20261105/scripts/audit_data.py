"""Read-only reconciliation of poster claims with the saved experiment records."""
from pathlib import Path
from fractions import Fraction
import hashlib, json
import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parents[1]
ROOT = OUT.parents[2]
B = ROOT/'review_outputs/quantum_ev_step5_20261105'
L = ROOT/'review_outputs/no_sumo_full_analysis_20261102/run01'
checks, sources = [], {}

def pin(path, role):
    path = Path(path)
    h = hashlib.sha256(path.read_bytes()).hexdigest()
    sources[str(path)] = dict(path=str(path), sha256=h, role=role)
    return path, h

def check(name, condition, detail=''):
    checks.append(dict(check=name, passed=bool(condition), detail=str(detail)))
    if not condition:
        raise AssertionError((name, detail))

def read(path, role):
    p, _ = pin(path, role)
    return pd.read_csv(p, keep_default_na=False, low_memory=False)

d = read(B/'data/B_PLAN_GAPS_36800.csv', '主結果・同一入力の対応差')
i = read(B/'data/B_INPUT_CONDITIONS_460.csv', '入力条件・古典対照')
l = read(L/'B_PLAN_REFERENCES_36800.csv', '生成計画台帳')
r = read(L/'B_RESOURCES_PER_FIT.csv', '学習・工程時間台帳')
for path in [B/'data/SUMMARY.json', B/'STEP5_OBJECTIVE_GAP_ANALYSIS.md',
             B/'STEP5_PATHWAY1_CONDITIONS.md', B/'STEP5_OPERATIONAL_IMPACT.md',
             ROOT/'review_outputs/poster_causal_structure_revision_20261105/run10/poster.pptx',
             ROOT/'研究のまとめ_20261105更新版.pptx']:
    pin(path, '照合資料・既存デザイン')

key = ['problem_id', 'config_id', 'measurement_rep']
check('unique 460 × 8 × 10 comparisons', len(d)==36800 and not d.duplicated(key).any())
check('460 inputs, 8 settings, 10 measurement replicates',
      len(i)==460 and d.config_id.nunique()==8 and d.measurement_rep.nunique()==10)
check('balanced output cells', d.groupby(key[:2]).size().eq(10).all()
      and d.groupby('problem_id').size().eq(80).all())
check('3680 fitted states; not 36800 independent training runs', len(r)==3680 and r.fit_id.nunique()==3680)
m = d.merge(l, on=key, suffixes=('_summary','_ledger'), validate='one_to_one')
check('all summary rows correspond to ledger', len(m)==len(d))
for col in ['input_sha256','source_sha256','fit_id','shots','n_customers']:
    check('ledger binding: '+col, (m[col+'_summary']==m[col+'_ledger']).all())
check('ledger rational candidate objectives', (m.J_candidate_fraction==m.objective_fraction).all())
check('exact signed and absolute differences', all(
    Fraction(a)-Fraction(b)==Fraction(c) and abs(float(abs(Fraction(c)))-e)<1e-9
    for a,b,c,e in zip(d.J_candidate_fraction,d.J_greedy_fraction,d.delta_fraction,d.abs_delta_s)))
check('candidate objective numeric transcription', np.allclose(d.J_candidate_s.astype(float),m.objective_s.astype(float),atol=1e-9,rtol=0))
check('all saved best candidates feasible', d.feasible.eq(True).all())
check('8192 samples per measurement', d.shots.eq(8192).all())
check('CPU simulation only', d.generation.eq('CPU_SIMULATION_OF_QUANTUM_ALGORITHM').all())
check('not a customer block decomposition', r.algorithm_scope.str.contains('no customer partition').any())

depots=set()
for row in i.to_dict('records'):
    p, h=pin(row['input_path'], '実入力NPZ：条件の独立照合')
    check('NPZ hash '+row['problem_id'], h==row['input_sha256'])
    a=np.load(p)
    n=len(a['nodes'])-1
    depots.add(str(a['nodes'][0]))
    check('NPZ settings '+row['problem_id'], n==row['n_customers']
          and np.all(a['ready']==0) and np.all(a['due']==32400)
          and a['service'][0]==0 and np.all(a['service'][1:]==102)
          and int(a['demand'].sum())==row['demand_PE']<=216
          and row['capacity_PE']==216)
    gp, _=pin(row['greedy_source'], '古典対照の元結果')
    g=json.loads(gp.read_text())
    route=g['route_indices']
    gj=sum(Fraction(str(float(a['travel'][x,y]))) for x,y in zip(route,route[1:]))
    check('classical route and cost '+row['problem_id'],
          route[0]==route[-1]==0 and sorted(route[1:-1])==list(range(1,n+1))
          and abs(float(gj)-row['greedy_J_s'])<1e-9)
check('single depot across B',len(depots)==1,depots)
check('input distribution',i.groupby('n_customers').size().to_dict()=={3:78,4:78,5:78,25:78,100:78,125:70})
check('all return times follow J+102n',np.allclose(d.candidate_return_s,d.J_candidate_s+d.total_service_s,atol=1e-9,rtol=0))
check('no contractual on-time-rate observations', d.contractual_on_time_rate.eq('').all())

groupmap={c:('位置交換など6設定' if not c.startswith('GROVER_') else c) for c in d.config_id.unique()}
d['poster_group']=d.config_id.map(groupmap)
agg=d.groupby('poster_group',sort=False).agg(
    comparisons=('problem_id','size'),inputs=('problem_id','nunique'),
    classical_mean_s=('J_greedy_s','mean'),candidate_mean_s=('J_candidate_s','mean'),
    delta_mean_s=('delta_s','mean'),absolute_mean_s=('abs_delta_s','mean'))
agg.to_csv(OUT/'evidence/POSTER_RESULT_TABLE.csv')
d.groupby(['n_customers','config_id']).agg(comparisons=('problem_id','size'),classical_mean_s=('J_greedy_s','mean'),candidate_mean_s=('J_candidate_s','mean'),delta_mean_s=('delta_s','mean')).to_csv(OUT/'evidence/SCALE_SETTING_RESULTS.csv')
summary=dict(inputs=len(i),settings=8,trained_states=len(r),measurement_repetitions=10,
             comparisons=len(d),shots_per_measurement=8192,depots=sorted(depots),
             classical_mean_s=d.J_greedy_s.mean(),candidate_mean_s=d.J_candidate_s.mean(),
             delta_mean_s=d.delta_s.mean(),absolute_mean_s=d.abs_delta_s.mean(),
             median_delta_s=d.delta_s.median(),max_delta_s=d.delta_s.max(),
             input_mean_median_s=d.groupby('problem_id').delta_s.mean().median(),
             improved=int(d.delta_s.lt(0).sum()),equal=int(d.delta_s.eq(0).sum()),worsened=int(d.delta_s.gt(0).sum()),
             min_return_slack_s=d.candidate_return_slack_s.min(),
             planned_service_s_per_100_stops=100*102,planned_travel_budget_s=32400-100*102)
saved=json.loads((B/'data/SUMMARY.json').read_text())
for k,v in [('mean_delta_s',summary['delta_mean_s']),('greedy_mean_s',summary['classical_mean_s']),
            ('candidate_mean_s',summary['candidate_mean_s']),('min_return_slack_s',summary['min_return_slack_s'])]:
    check('saved summary '+k, abs(saved[k]-v)<1e-8)
(OUT/'evidence/POSTER_DATA.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
pd.DataFrame(checks).to_csv(OUT/'evidence/DATA_CHECKS.csv',index=False)
pd.DataFrame(sources.values()).to_csv(OUT/'evidence/SOURCE_MANIFEST.csv',index=False)
print(json.dumps(summary,ensure_ascii=False,indent=2))
print('All checks passed:',len(checks))
