"""Saved-record arithmetic and source inspection only; no solver/model runner."""
from pathlib import Path
import csv,json,statistics,hashlib,collections
from fractions import Fraction
R=Path(__file__).resolve().parents[1];D=Path('/home/takuma/kmd-analysis/review_outputs/no_sumo_full_analysis_20261102/run01');E=R/'evidence';checks=[]
def read(n):return list(csv.DictReader((D/n).open()))
def write(n,rows):
 with (E/n).open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def ck(i,value,expected,src,tol=None):
 ok=abs(value-expected)<tol if tol else value==expected
 checks.append(dict(id=i,actual=value,expected=expected,status='PASS' if ok else 'FAIL',source=src));assert ok,checks[-1]
b=read('B_PLAN_REFERENCES_36800.csv');fits=read('B_RESOURCES_PER_FIT.csv');refs=read('B_EXACT_REFERENCE_COVERAGE.csv');initial=read('B_CLASSICAL_INITIAL_BASELINES.csv')
# Exact references: certificate identity, meaning, and missingness, separately from orbit minima.
certrows=[]
for v in refs:
 p=Path(v['certificate_path']);z=json.loads(p.read_text());ok=hashlib.sha256(p.read_bytes()).hexdigest()==v['certificate_sha256'];assert ok
 proven=v['exact_reference_available']=='True'
 if proven:
  value=z.get('exact_optimum_seconds');assert value is not None
  assert Fraction(value)==Fraction(v['exact_optimum_fraction'])
 else:assert z['termination']=='EXACT_BOUND_WITNESS_MISMATCH' and z['proved_optimal']==False
 certrows.append(dict(problem_id=v['problem_id'],scale=v['scale'],global_exact_proven=proven,certificate_sha256_match=ok,proof=v['certificate_kind'],termination=z.get('termination',z.get('status','')),reason=v['missing_reason'],certificate_path=str(p),scope='全配送先閉路のOD総和の厳密最小（時間窓なし）；matching支持最小とは別'))
ck('all_reference_certificates_hash_and_values',len(certrows),460,'B_EXACT_REFERENCE_COVERAGE.csv + 460 saved certificates')
coverage=[]
for scale,n in zip(['R0','R1','R2','R3','R4','R5'],[3,4,5,25,100,125]):
 a=[v for v in certrows if v['scale']==scale];yes=sum(v['global_exact_proven'] for v in a)
 coverage.append(dict(n=n,scale=scale,inputs=len(a),global_exact= yes,not_proven=len(a)-yes,reason='EXACT_BOUND_WITNESS_MISMATCH' if yes<len(a) else '',not_proven_configs='全8設定で同じ入力が参照欠測'))
ck('missing_global_exact_n100',coverage[4]['not_proven'],21,'global certificate table')
ck('missing_global_exact_n125',coverage[5]['not_proven'],32,'global certificate table')
write('GLOBAL_REFERENCE_CERTIFICATES.csv',certrows);write('GLOBAL_REFERENCE_COVERAGE.csv',coverage)
by=collections.defaultdict(list)
for v in b:by[(v['config_id'],v['problem_id'])].append(v)
per=[];improvements=[]
for (cfg,pid),vs in sorted(by.items()):
 delta=statistics.fmean(float(Fraction(v['objective_fraction'])-Fraction(v['classical_initial_fraction'])) for v in vs)
 pct=statistics.fmean(float(100*(Fraction(v['objective_fraction'])-Fraction(v['classical_initial_fraction']))/Fraction(v['classical_initial_fraction'])) for v in vs)
 per.append(dict(config_id=cfg,problem_id=pid,scale=vs[0]['scale'],n=int(vs[0]['n_customers']),mean_delta_s=delta,mean_relative_delta_percent=pct,repetitions=len(vs)))
 if delta<0:improvements.append(dict(config_id=cfg,problem_id=pid,n=int(vs[0]['n_customers']),mean_delta_s=delta,negative_references=sum(Fraction(v['objective_fraction'])<Fraction(v['classical_initial_fraction']) for v in vs),repetitions=len(vs)))
scaled=[]
for scale,n in zip(['R0','R1','R2','R3','R4','R5'],[3,4,5,25,100,125]):
 for cfg in sorted({v['config_id'] for v in b}):
  rows=[v for v in per if v['scale']==scale and v['config_id']==cfg]
  scaled.append(dict(scale=scale,n=n,config_id=cfg,inputs=len(rows),mean_delta_s=statistics.fmean(v['mean_delta_s'] for v in rows),mean_relative_delta_percent=statistics.fmean(v['mean_relative_delta_percent'] for v in rows),aggregation='mean_i(mean_rep(100*(J_best-J_initial)/J_initial)); not ratio of scale means',interpretation='保存データからの派生算術。新しい実験ではない。'))
for cfg in ['GROVER_P2','GROVER_P3']:
 ck('improvements_'+cfg+'_n4',sum(v['config_id']==cfg and v['n']==4 for v in improvements),1,'B_PLAN_REFERENCES_36800.csv')
 ck('improvements_'+cfg+'_n5',sum(v['config_id']==cfg and v['n']==5 for v in improvements),6,'B_PLAN_REFERENCES_36800.csv')
ck('same_7_improving_physical_inputs',set(v['problem_id'] for v in improvements if v['config_id']=='GROVER_P2')==set(v['problem_id'] for v in improvements if v['config_id']=='GROVER_P3'),True,'per-input 10 rep means')
write('B_NORMALIZED_BY_SCALE_CONFIG.csv',scaled);write('B_IMPROVING_INPUTS.csv',improvements)
# All five restricted conditions, one adjacent, and both GM settings exist at large n.
setting=[]
for cfg in sorted({v['config_id'] for v in fits}):
 a=[v for v in fits if v['config_id']==cfg];family=a[0]['family']
 setting.append(dict(config_id=cfg,family=family,fits=len(a),n25=sum(v['n']=='25' for v in a),n100=sum(v['n']=='100' for v in a),n125=sum(v['n']=='125' for v in a),backends=';'.join(sorted({v['simulation_backend'] for v in a})),global_reference_set=','.join(v['problem_id'] for v in refs if v['exact_reference_available']=='False'),support='n! customer permutations / ideal uniform state' if cfg.startswith('GROVER_') else 'restricted matching orbit 2^floor(n/2), all customers retained' if family=='mirror_family' else 'adjacent swaps with p=3; t grid {0,0.5,1}',classical_candidate_set='事前列挙プールから経路を選ぶ方式ではない。全訪問先を保持した状態支持である。',hardware='CPU数値処理のみ；実機の状態準備・速度・資源は未実証'))
ck('all_8_configs_large_scales',all((v['n25'],v['n100'],v['n125'])==(78,78,70) for v in setting),True,'B_RESOURCES_PER_FIT.csv')
write('SETTING_SCOPE_AUDIT.csv',setting)
# Read the actual per-fit saved timing fields, compare to summary, and retain HOLDs.
resources=read('B_SAVED_RESOURCES_LONG.csv');times=[]
for label,scope in [('学習','FIT'),('最終状態・精度検証','FINAL_VALIDATION')]:
 rows=[v for v in resources if v['config_id']=='GROVER_P3' and v['scale']=='R3' and v['scope']==scope and v['resource_field']=='wall_seconds']
 assert len(rows)==78 and len({v['fit_id'] for v in rows})==78
 for v in rows:
  f=Path(v['source_path']);z=json.loads(f.read_text());assert hashlib.sha256(f.read_bytes()).hexdigest()==v['source_sha256']
  q=z
  for part in v['json_pointer'].strip('/').split('/'):q=q[part]
  assert float(q)==float(v['value'])
 avg=statistics.fmean(float(v['value']) for v in rows)
 expect=.8884206184003955 if scope=='FIT' else 168.7453417102687
 ck('time_'+scope,avg,expect,'78 saved source JSON files per stage',1e-8)
 times.append(dict(stage=label,scope=scope,records=78,mean_wall_s=avg,status='A 保存工程時間',meaning='CPU工程の壁時計時間。25配送先、GM-QAOA層数3。10測定反復へ重複させない。'))
for label in ['候補生成・8192標本の取得','前処理','全工程']:
 times.append(dict(stage=label,scope='HOLD',records=0,mean_wall_s='',status='C 比較可能な工程値未確認',meaning='統一した工程の範囲・実験当時環境・共通予算が未確認。欠けた工程を推定で合算しない。'))
write('TIME_SCOPE_AUDIT.csv',times)
# Snapshot integrity; actual source semantics are separately logged by line locator.
ss=list(csv.DictReader(open('/home/takuma/kmd-analysis/review_outputs/thesis_results_interpretation_20261102/run01/ALGORITHM_SOURCE_SNAPSHOTS.csv')))
ck('algorithm_snapshot_hashes',sum(hashlib.sha256(Path(v['path']).read_bytes()).hexdigest()==v['sha256'] for v in ss),len(ss),'ALGORITHM_SOURCE_SNAPSHOTS.csv')
# Original classical initial route reused, not newly fitted or min'ed with measured candidates.
base=Path('/home/takuma/kmd-analysis-pre-clean-20261102-112222/untracked/review_outputs/unified_no_windows_r0_r8_20261022')
bind=[]
for v in initial:
 p=base/'RESULTS'/(v['problem_id']+'.json');z=json.loads(p.read_text())
 assert z['instance_sha256']==v['input_sha256'] and z['route_indices']==json.loads(v['initial_route']) and float(z['validation']['objective_seconds'])==float(v['initial_seconds'])
 bind.append(dict(problem_id=v['problem_id'],source_path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),source_method=z['method'],algorithm_metadata=json.dumps(z['algorithm_metadata']),route_binding='PASS'))
ck('initial_route_binding_all',len(bind),460,'initial routes reused from unified no-windows saved deterministic heuristic')
write('INITIAL_ROUTE_BINDINGS.csv',bind)
# Full checklist is independent of, and supplements, the previous 41 checks.
write('EXTENDED_CHECKS.csv',checks)
(E/'EXTENDED_AUDIT.json').write_text(json.dumps(dict(status='PASS',checks=len(checks),failed_checks=0,global_reference_coverage=coverage,normalized_scale_results=scaled,improving_input_ids=sorted({v['problem_id'] for v in improvements}),time_scopes=times,scientific_runners_invoked=0),ensure_ascii=False,indent=2))
print('Extended checks:',len(checks),'PASS; normalized GM values:')
for v in scaled:
 if v['config_id'].startswith('GROVER_'):print(v['n'],v['config_id'],round(v['mean_relative_delta_percent'],6))
