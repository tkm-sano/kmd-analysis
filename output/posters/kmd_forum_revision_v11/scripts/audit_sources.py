"""Read frozen outputs and source snapshots only; never run experiment code."""
from pathlib import Path
from fractions import Fraction
from collections import Counter,defaultdict
import csv,json,hashlib,math
import numpy as np
O=Path(__file__).resolve().parents[1];R=O.parents[2]
U=Path('/home/takuma/kmd-analysis-pre-clean-20261102-112222/untracked/review_outputs')
Q=U/'staged_qaoa_validation_20261102';C=U/'cpu_matched_classical_swaps_r0_r5_20261101'
S=R/'review_outputs/quantum_ev_step5_20261105';N=R/'review_outputs/no_sumo_full_analysis_20261102/run01'
manifest={};checks=[]
def pin(path,role,expected=None):
 p=Path(path);h=hashlib.sha256(p.read_bytes()).hexdigest()
 if expected: assert h==expected,(p,h,expected)
 manifest[str(p)]=dict(path=str(p),sha256=h,role=role,bytes=p.stat().st_size)
 return p

def rows(p):return list(csv.DictReader(pin(p,'frozen experiment ledger').open()))
def ck(k,ok,detail=''):
 checks.append(dict(check=k,passed=bool(ok),detail=detail));assert ok,(k,detail)
def location(p,text):
 p=pin(p,'saved source or report');lines=p.read_text().splitlines();hits=[i+1 for i,s in enumerate(lines) if text in s]
 assert hits,(p,text)
 return dict(path=str(p),lines=hits,needle=text)
for ext in ['pptx','pdf']:pin(R/f'v10_KMD_Forum_量子技術と物流配送計画_A1縦_言語監査.{ext}','protected v10 input')
for p in [S/'STEP5_OBJECTIVE_GAP_ANALYSIS.md',S/'STEP5_OPERATIONAL_IMPACT.md',N/'run_b.py',N/'FROZEN_PROTOCOL.json',N/'00_FROZEN_ANALYSIS_PROTOCOL.md',S/'scripts/analyze.py']:
 pin(p,'adopted saved experiment documentation')
gaps=rows(S/'data/B_PLAN_GAPS_36800.csv');inp=rows(S/'data/B_INPUT_CONDITIONS_460.csv');refs=rows(N/'B_PLAN_REFERENCES_36800.csv');resources=rows(N/'B_RESOURCES_PER_FIT.csv')
ck('saved populations',len(gaps)==len(refs)==36800 and len(inp)==460 and len(resources)==3680)
bykey={(x['problem_id'],x['config_id'],x['measurement_rep']):x for x in refs}
ck('measurement keys unique',len(bykey)==36800)
ck('input x setting repetition design',all(n==10 for n in Counter((x['problem_id'],x['config_id']) for x in gaps).values()) and all(n==80 for n in Counter(x['problem_id'] for x in gaps).values()))
ck('saved candidates match no_sumo references',all(x['source_sha256']==bykey[(x['problem_id'],x['config_id'],x['measurement_rep'])]['source_sha256'] and Fraction(x['J_candidate_fraction'])==Fraction(bykey[(x['problem_id'],x['config_id'],x['measurement_rep'])]['objective_fraction']) for x in gaps))
ck('same eight settings and saved fits',len(set(x['config_id'] for x in gaps))==8 and set(x['fit_id'] for x in gaps)==set(x['fit_id'] for x in resources))
ck('classification is exact sign of rational difference',all(Fraction(x['delta_fraction'])==Fraction(x['J_candidate_fraction'])-Fraction(x['J_greedy_fraction']) and x['classification']==('equal' if Fraction(x['delta_fraction'])==0 else 'improved' if Fraction(x['delta_fraction'])<0 else 'worsened') for x in gaps))
ck('counts retained',Counter(x['classification'] for x in gaps)==Counter(equal=28200,worsened=8600))
ck('saved route constraints true in ledger',all(x['feasible']=='True' for x in gaps) and all(x['feasible']=='True' for x in refs))
ck('no hardware runs',all(x['generation']=='CPU_SIMULATION_OF_QUANTUM_ALGORITHM' and x['shots']=='8192' for x in gaps))
ck('contractual on-time metric absent in this cohort',all(x['contractual_on_time_rate']=='' for x in gaps))
conditions=[]
for x in inp:
 p=pin(x['input_path'],'saved NPZ condition',x['input_sha256'])
 with np.load(p,allow_pickle=False) as a:
  n=len(a['nodes'])-1
  conditions.append(dict(problem_id=x['problem_id'],n=n,ready_zero=bool(np.all(a['ready']==0)),due32400=bool(np.all(a['due']==32400)),service102=bool(np.all(a['service'][1:]==102) and a['service'][0]==0),depot=str(a['nodes'][0]),load=int(a['demand'].sum())))
ck('input origin, service and common horizon',all(x['ready_zero'] and x['due32400'] and x['service102'] and x['depot']=='DEP_006' and x['load']<=216 for x in conditions))
ck('only six requested customer counts',sorted({x['n'] for x in conditions})==[3,4,5,25,100,125])
# Read representative original measurement records for every setting and scale.
seen=set()
for x in gaps:
 k=x['config_id'],x['scale']
 if k in seen:continue
 seen.add(k);p=pin(x['source_path'],'original CPU measurement',x['source_sha256']);saved=json.loads(p.read_text())
 rr=next(v for v in saved['records'] if str(v['rep'])==x['measurement_rep'] and v.get('mode','OPTIMIZED')=='OPTIMIZED')
 ck('saved raw output '+str(k),Fraction(str(rr.get('sampled_best_seconds',rr.get('road_seconds'))))==Fraction(x['J_candidate_fraction']))
for x in inp[:1]+inp[-1:]:pin(x['greedy_source'],'greedy baseline saved selected route')
protocols={}
for family in ['mirror_family','grover_depth','active_adjacent_p3']:
 p=pin(Q/family/'PROTOCOL.json','corresponding saved configuration');protocols[family]=json.loads(p.read_text())
protocols['classical']=json.loads(pin(C/'PROTOCOL.json','corresponding saved baseline configuration').read_text())
# Source snapshots are authoritative for the historical saved records.
mirror=Q/'mirror_family/SOURCE_SNAPSHOT/scripts/run_staged_mirror_qaoa.py'
grover=Q/'grover_depth/SOURCE_SNAPSHOT/scripts/run_staged_grover_depth.py'
active=Q/'active_adjacent_p3/SOURCE_SNAPSHOT/scripts/run_staged_active_p3.py'
classic=C/'SOURCE_SNAPSHOT/scripts/run_cpu_matched_classical_swaps.py'
nowindows=Q/'active_adjacent_p3/SOURCE_SNAPSHOT/src/kmd_quantitative/routing/no_windows.py'
for p in [mirror,grover,active,classic,nowindows,C/'SOURCE_SNAPSHOT/src/kmd_quantitative/routing/classical_swap_baselines.py']:
 pin(p,'historical frozen implementation')
# Also verify snapshot file hashes where the experiment exported a source hash mapping.
snapshot_checks=[]
for base in [Q/'mirror_family',Q/'grover_depth',Q/'active_adjacent_p3',C]:
 hp=base/'SOURCE_HASHES.json'
 if not hp.exists():continue
 d=json.loads(pin(hp,'historical source hash mapping').read_text())
 for p in list(manifest):
  pp=Path(p)
  try:rel=str(pp.relative_to(base/'SOURCE_SNAPSHOT'))
  except ValueError:continue
  if isinstance(d,dict) and rel in d and isinstance(d[rel],str):
   pin(pp,'verified historical source snapshot',d[rel]);snapshot_checks.append(rel)
print('snapshot hashes checked',len(snapshot_checks))
# Retain the original precision. These are checks against the same frozen series, not new experiments.
original=json.loads(pin(O/'evidence/POSTER_DATA.json','v10 original unrounded values').read_text())
groups=rows(O/'evidence/POSTER_RESULT_TABLE.csv')
keymap={'GROVER_P2':'GROVER_P2','GROVER_P3':'GROVER_P3'}
for g in groups:
 data=[x for x in gaps if (x['config_id']==keymap[g['poster_group']] if g['poster_group'] in keymap else x['config_id'] not in keymap)]
 ck('fixed table cohort '+g['poster_group'],len(data)==int(g['comparisons']))
 for sourcekey,tablekey in [('J_greedy_s','classical_mean_s'),('J_candidate_s','candidate_mean_s'),('delta_s','delta_mean_s')]:
  mean=math.fsum(float(x[sourcekey]) for x in data)/len(data)
  ck('original value '+g['poster_group']+' '+sourcekey,abs(mean-float(g[tablekey]))<1e-9)
ck('original overall means retained',abs(math.fsum(float(x['J_candidate_s']) for x in gaps)/36800-original['candidate_mean_s'])<1e-9)
ck('return and final delivery definition match saved columns',all(abs(float(x['candidate_return_s'])-float(x['J_candidate_s'])-float(x['total_service_s']))<1e-8 for x in gaps))
definitions=[
 dict(topic='積載上限の単位・換算基準',decision='条件表の積載上限行を省略',adopted=False,reason='capacity_PE=216は記録されるが、この保存実験に結び付いたPE換算基準を確定できない。個数・kgに置き換えない。',evidence=[dict(path=str(Q/'mirror_family/PROTOCOL.json'),field='capacity_PE'),dict(path=str(S/'data/B_INPUT_CONDITIONS_460.csv'),field='capacity_PE')]),
 dict(topic='帰着期限の起点',decision='モデル上の開始時刻から9時間（32,400秒）',adopted=True,reason='保存モデルは開始原点0、共通上限32400秒。計画計算開始や実際の出発時計時刻とは同定しない。',evidence=[location(S/'STEP5_OPERATIONAL_IMPACT.md','t0=0'),location(nowindows,'returned = road + service'),location(nowindows,'HORIZON = 32400')]),
 dict(topic='基準計画',decision='隣接交換を用いる反復貪欲法',adopted=True,reason='Step5が結合したITERATED_GREEDY_ADJACENT_SWAPの保存結果を使う。no_sumoのclassical_initial列へ置き換えない。',evidence=[location(S/'scripts/analyze.py',"ITERATED_GREEDY_ADJACENT_SWAP/RESULT.json"),location(classic,'delta,i=cb.best_adjacent'),location(classic,'route=best_route.copy()')]),
 dict(topic='初期計画の保持と計算予算',decision='古典手法は初期計画を含めて最良を保持。QAOAは抽出した最短候補。古典予算は旧実験の入力別CPU秒。',adopted=True,evidence=[location(classic,'best_score=initial_score'),location(S/'STEP5_OBJECTIVE_GAP_ANALYSIS.md','古典の計算予算は現行8設定に対応せず')]),
 dict(topic='候補選択・条件確認・保存',decision='図ラベルは「最短候補を選び、条件確認して保存」',adopted=True,reason='入力・順列の適合を前提とし、候補の最短値を選択後に保存候補の積載・帰着条件を確認する。鏡型とGrover型は選択後にvalidateしてrecordを保存、activeもvalid順列の最短を選びvalidate後にrecordを保存。全候補に積載・帰着を個別照合したとは書かない。',evidence=[location(mirror,'chosen=min(unique,key=model.exact)'),location(mirror,"assert v['feasible']"),location(grover,'selected=min(candidates'),location(active,'best=min(candidates'),location(active,'mode_records.append')]),
 dict(topic='配達完了時刻',decision='最後の配送先での配達作業完了時刻',adopted=True,reason='last_time=J−最後の配送先から拠点への移動時間＋全配送先の作業時間。拠点帰着とは別。',evidence=[location(S/'scripts/analyze.py','def last_time(route)'),location(S/'STEP5_OPERATIONAL_IMPACT.md','最終顧客のサービス完了')]),
 dict(topic='期限内配達率',decision='指標名と分母・分子の説明を省略',adopted=False,reason='B系列は顧客固有期限なしで、contractual_on_time_rate列は全件空。共通帰着上限内の顧客割合や他系列AのPE加重率を流用しない。',evidence=[location(S/'STEP5_OPERATIONAL_IMPACT.md','contractual_on_time_rate=NULL'),dict(path=str(S/'data/B_PLAN_GAPS_36800.csv'),field='contractual_on_time_rate')]),
 dict(topic='同等の判定',decision='丸め前の保存値を分数として比較し、差が厳密に0',adopted=True,reason='判定の許容誤差は用いず、delta_fractionのゼロ判定を使用する。量子候補選択時の浮動小数点スクリーニング許容差とは別である。',evidence=[location(S/'scripts/analyze.py',"'classification':'improved' if delta<0 else 'equal' if delta==0 else 'worsened'")]),
 dict(topic='QAOAの対象配送先と探索範囲',decision='各計画の全配送先。一部交換6設定と全順列Grover2設定を区別',adopted=True,evidence=[dict(path=str(Q/'mirror_family/PROTOCOL.json'),fields=['customer_partitioning','support']),dict(path=str(Q/'grover_depth/PROTOCOL.json'),fields=['customer_partitioning','support']),dict(path=str(N/'B_RESOURCES_PER_FIT.csv'),field='algorithm_scope')]),
 dict(topic='実施済みと今後',decision='今回の問いは総移動時間差。採用・実配送成果と複数台割当ては今後',adopted=True,reason='研究全体のRQの変更はしない。新しい実験・シミュレーションは実行しない。',evidence=[location(S/'STEP5_OPERATIONAL_IMPACT.md','実採用・実道路への接続はHOLD')])
]
(O/'evidence/DEFINITION_DECISIONS.json').write_text(json.dumps(definitions,ensure_ascii=False,indent=2))
with (O/'evidence/DEFINITION_DECISIONS.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=['topic','adopted','decision','reason','evidence']);w.writeheader()
 for d in definitions:w.writerow({**d,'reason':d.get('reason',''),'evidence':json.dumps(d['evidence'],ensure_ascii=False)})
(O/'evidence/SOURCE_CHECKS.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2))
with (O/'evidence/SOURCE_MANIFEST.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=['path','sha256','role','bytes']);w.writeheader();w.writerows(manifest.values())
(O/'evidence/ORIGINAL_NUMERIC_VALUES.json').write_text(json.dumps(dict(overall=original,groups=groups,display_precision=1,source='v10 fixed original values; no cohort substitution'),ensure_ascii=False,indent=2))
print(json.dumps(dict(checks=len(checks),passed=all(x['passed'] for x in checks),pinned_files=len(manifest),definitions=len(definitions),omitted=[x['topic'] for x in definitions if not x['adopted']]),ensure_ascii=False))
