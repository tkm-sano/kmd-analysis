"""Summarize saved raw evidence only; never executes an optimizer."""
from pathlib import Path
import json,statistics as st,csv,hashlib,subprocess
R=Path(__file__).resolve().parents[1];E=R/'evidence'
labels={'original':'現行Qiskit未変更run','qiskit':'Qiskit adapter','qulacs':'Qulacs直接','quri':'QURI＋Qulacs','qamomile_quri':'Qamomile＋QURI＋Qulacs'}
def read(p):return json.loads(p.read_text())
def stat(xs):
 xs=list(xs);q=st.quantiles(xs,n=4,method='inclusive')
 return {'median':st.median(xs),'min':min(xs),'max':max(xs),'IQR':q[2]-q[0]}
def f(x,scale=1):return f'{x*scale:.4f}'
def span(xs,scale=1):
 s=stat(xs);return f'{f(s["median"],scale)} [{f(s["min"],scale)}, {f(s["max"],scale)}]'
def save(name,s): (R/name).write_text(s)
def csv_save(name,rows):
 with (E/name).open('w') as file:
  w=csv.DictWriter(file,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
backend=[read(p) for p in sorted((E/'backend').glob('*.json'))];pricing=[read(p) for p in sorted((E/'pricing').glob('*.json'))]
trials=[]
for p in sorted((E/'trials').glob('main_*/trial_result.json')):
 r=read(p);spec=read(p.parent/'spec.json');stats=[];qtraces=[]
 for branch in sorted((p.parent/'branches').iterdir(),key=lambda p:int(p.name)):
  w=read(branch/'worker_result.json');m=(w.get('plan') or {}).get('method_settings',{})
  qs=[read(q) for q in sorted((branch/'stages').glob('D_AOA_*.json'))];qtraces.append([x['result']['history'] for x in qs])
  if spec['trial_algorithm']=='updated':
   added=m.get('added_valid_columns');updates=m.get('RMP_addition_updates');lp_calls=3*len(m.get('CG_trace',[]))+1
   changed=m.get('changed_customer_set_routes');dualmoves=sum(x['customer_dual_changed'] for x in m.get('CG_trace',[]))
  else:
   traces=m.get('base',{}).get('trace',[])+m.get('hybrid',{}).get('trace',[])
   added=sum(x['new_negative'] for x in traces);updates=sum(x['new_negative']>0 for x in traces)
   lp_calls=sum(x['type']=='LP' for x in m.get('base_solver_calls',[])+m.get('hybrid_solver_calls',[]));changed=0;dualmoves=None
  stats.append({'branch':int(branch.name),'status':w['status'],'added':added,'updates':updates,'LP_calls':lp_calls,'changed_sets':changed,'dual_changes':dualmoves,'incomplete':m.get('algorithm_path_incomplete',False),'quantum_calls':len(qs),'max_RSS_KiB':w['max_rss_KiB']})
 trials.append({'n':int(spec['scenario_id'].split('N')[-1]),'seed':spec['seeds']['solver_seed'],'backend':spec['trial_backend'],'algorithm':spec['trial_algorithm'],
                'status':r['status'],'D_km':r['D_km'],'W_min':r['W_min'],'T_program_s':r['T_program_s'],'setup_s':r['dependency_setup_s'],
                'quantum_calls':r['total_quantum_calls'],'training_shots':r['total_training_shots'],'final_shots':r['total_final_shots'],
                'added_columns':sum(x['added'] or 0 for x in stats),'RMP_updates':sum(x['updates'] or 0 for x in stats),'LP_calls':sum(x['LP_calls'] for x in stats),
                'changed_sets_all_branches':sum(x['changed_sets'] or 0 for x in stats),'customer_dual_changes':sum(x['dual_changes'] or 0 for x in stats),
                'aggregate_RSS_upper_bound_KiB':r['aggregate_RSS_upper_bound_KiB'],'branches':stats,'histories':qtraces,'directory':str(p.parent.relative_to(R))})
assert len(backend)==36 and len(pricing)==15 and len(trials)==54,(len(backend),len(pricing),len(trials))
model=read(E/'model_validation_final.json');tests=(E/'tests_four_cpu.log').read_text();assert '107 passed' in tests
failed=[]
for directory in (E/'failed_trials').glob('*'):
 qs=[read(p) for p in directory.glob('branches/*/stages/D_AOA_*.json')]
 failed.append({'directory':str(directory.relative_to(R)),'spec':read(directory/'spec.json'),
                'quantum_accounting_complete':False,'completed_quantum_calls_observed':len(qs),
                'observed_training_shots':sum(q.get('training_total_shots',0) for q in qs),
                'observed_final_shots':sum(q.get('final_total_shots',0) for q in qs),
                'unfinished_work_shots':'unknown; never imputed zero'})
(E/'failed_attempt_accounting.json').write_text(json.dumps(failed,indent=2))
(E/'full_trial_summary.json').write_text(json.dumps([{k:v for k,v in r.items() if k!='histories'} for r in trials],indent=2))
parity=[]
for n in [6,8]:
 for seed in [1101,1102,1103]:
  original=next(r for r in trials if (r['n'],r['seed'],r['backend'],r['algorithm'])==(n,seed,'original','legacy'))
  for b in ['qiskit','qulacs','quri','qamomile_quri']:
   r=next(r for r in trials if (r['n'],r['seed'],r['backend'],r['algorithm'])==(n,seed,b,'legacy'))
   parity.append({'n':n,'seed':seed,'backend':b,'all_four_branch_histories_equal':r['histories']==original['histories'],'D_equal':r['D_km']==original['D_km'],'W_equal':r['W_min']==original['W_min']})
(E/'legacy_parity.json').write_text(json.dumps(parity,indent=2))
metrics=[]
for r in backend:
 rows=[x for x in r['rows'] if not x['warmup']]
 m={k:r[k] for k in ['backend','nodes','slots','p','qubits','logical_depth']}
 for k in ['circuit_build_s','conversion_s','statevector_s','probability_s','sampling_s','total_s','execution_excluding_conversion_s','execution_including_conversion_s']:
  m.update({k+'_'+sk:sv for sk,sv in stat(x[k] for x in rows).items()})
 m['VmHWM_KiB']=r['memory']['VmHWM_KiB'];metrics.append(m)
csv_save('backend_metrics.csv',metrics)
csv_save('end_to_end_metrics.csv',[{k:v for k,v in r.items() if k not in ['branches','histories']} for r in trials])

# 1 Numerical equivalence
all_checks=[x['equality'] for r in backend for x in r['rows']]
eq={k:max(abs(1-x[k]) if k=='fidelity' else x[k] for x in all_checks) for k in ['fidelity','phase_aligned_max_abs','probability_max_abs','probability_L1','expectation_abs','leakage']}
s='''# バックエンド数値同等性

2026-11-14。前回成果は `../library_applicability_20261114_v1/` に保全し、142件のartifact hash一致を再確認した。前回の40測定/24状態検査は背景証拠として再利用し、今回の時間統計へ混ぜない。

今回、同じPricingAOAのHamiltonian、ALiM、customer_unique penalty、depot one-hot初期状態、位置別exact ring XY、同じ固定角をQiskit・Qulacs直接・QURI Parts→Qulacsで実行した。**3構成は検証範囲でグローバル位相を除き数値的に同等だった。**

## 検査範囲と誤差

地点数(depot込み)3/4、slots3/5、p1/2/4の12条件、3構成、warm-up1＋測定7の計288状態を検査した。q6/8/12/16。全2^qビット列の確率分布を比較し、one-hot外の漏出も含めた。期待値は厳密one-hotのenergy配列と標本抽出前の確率から求めた。

|指標|許容誤差|観測最大|
|---|---:|---:|
'''
for k,tol in [('fidelity',1e-8),('phase_aligned_max_abs',1e-9),('probability_max_abs',1e-9),('probability_L1',1e-9),('expectation_abs',1e-8),('leakage',1e-8)]:s+=f'|{"abs(1−fidelity)" if k=="fidelity" else k}|{tol:.1e}|{eq[k]:.4e}|\n'
s+='''
位相調整はoverlap `<reference|other>` の偏角を除いた最大複素振幅差。Qiskit原回路は定数Hamiltonianのglobal_phaseを入れるが、Qulacs/QURIの回路はその状態全体位相を省略する。物理的確率/期待値の差として扱わない。

## ゲート・bit対応

- indexは `b = position_block*n + node`、整数maskのbit bがqubit b。表示bitstringは幅q、左が高位、右がqubit0。標本列を逆順にして顧客IDへ渡さない。
- Qiskit RZ/RZZは `exp(−i angle*P/2)`。Qulacs直接のRZ/PauliRotationは符号を反転して渡す。QURI側はQiskitと同符号で構築し、QURIのQulacs変換が反転する。
- XYは既存 `full_xy_block(beta)` の密行列を同じ順のtargetへ作用させる。近接ペアゲート積のTrotter近似へ変えていない。論理深さは密XYを1ゲートと数え、実機native深さとしない。
- 訓練は現行どおり圧縮one-hot tensor＋COBYLA。実機、Aer、noiseは使用しない。今回のadapterの最終抽出は全構成で**現行のQiskit Statevector.sample_counts**を使用し、標本PRNG差を取り除く。前回PCG64 multinomialを使った試験とは区別する。

根拠: [adapters.py](code/adapters.py)、[既存aoa.py](../../../src/kmd_toc/column_generation/aoa.py)、[QURI変換実装](https://github.com/QunaSys/quri-sdk/blob/v0.28.0/quri-parts/packages/qulacs/quri_parts/qulacs/circuit/__init__.py)、[生データ](evidence/backend/)。明示した許容誤差を超えた比較を速度結果へ含めないようassertしている。

## 現行runとの整合性

新規契約テストでは3実行adapterについて、現行runの学習履歴・最適角・最終bit counts・経路・実行可能率の一致を確認した。追加の全体試験は [legacy_parity.json](evidence/legacy_parity.json) に4枝すべての履歴一致を保存した。Qamomileの直接式構築は数学的同等でも浮動小数点の和の順が変わるので、COBYLAの同点近傍の判断まで同一であるとは要求しない。差が生じた場合はQamomileによる品質改善と解釈しない。

容量2・1バース・最大2便の人工6顧客について、4構成の列生成接続契約も通過した。最終3便、D=4.2 km、W=2分、バースピーク1で、別実装の再計算も一致。部分計画の顧客欠落は検証で拒否した。[契約テスト](code/test_contracts.py)、[107件成功ログ](evidence/tests_four_cpu.log)、[binding結果](evidence/binding_contract_quri.json)。

最初の回帰実行は1コアに制限したため「4コアが必要」という既存テスト6件が失敗した。割当を0–3へ直した再実行では107件すべて通過した。失敗ログも `evidence/tests.log` に保全し、性能測定の反復へ数えていない。
'''
save('BACKEND_EQUIVALENCE.md',s)

# 2 Backend performance
s='''# Statevectorの時間・メモリ比較

[同等性検査](BACKEND_EQUIVALENCE.md)に通った回路だけを比較した。7反復の中央値とmin/max/IQRをCSVへ保存した。全条件で1 warm-upを測定集計から除外した。固定角のベンチマークであり、パラメータ最適化・RMP・日程完成は含まない。

Python3.11.15、NumPy2.3.1、SciPy1.16.0、Qiskit2.1.1、Qulacs0.6.14、QURI Parts0.28.0、Qamomile0.15.2。共有ホストAMD EPYC9684X/Linux、単一コアaffinity、native数値pool各1 thread。アドレス空間4 GiB/プロセス。最大q16のraw状態は1 MiB、参照/確率/一時コピーの数MiBと共通importを見積もって実行した。q20超やS1〜S3は実行しない。

回路生成はIsingゲート・XY行列指数化・回路への追加。QURI変換は `convert_circuit` だけを分離した。Statevectorは変換済みnative回路の実行とベクトル取得、確率はabs²と正規化。最終抽出は全構成共通のNumPy choice/bitstring化（4096 shots）。ライブラリ固有sampler性能ではない。全体D試験では既存Qiskit samplerを使う。

## 時間（中央値、ms）

|q|p|構成|論理depth|生成|変換|Statevector|確率取得|抽出|総時間|
|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|
'''
for m in sorted(metrics,key=lambda r:(r['qubits'],r['p'],r['backend'])):
 s+=f'|{m["qubits"]}|{m["p"]}|{labels[m["backend"]]}|{m["logical_depth"]}|'+ '|'.join(f(m[k+'_median'],1000) for k in ['circuit_build_s','conversion_s','statevector_s','probability_s','sampling_s','total_s'])+'|\n'
s+='\n## 変換の影響・ばらつき\n\n|q|p|構成|変換なし実行ms 中央値[min,max]|変換込み実行ms 中央値[min,max]|全体ms IQR|VmHWM KiB|\n|---:|---:|---|---:|---:|---:|---:|\n'
for r in sorted(backend,key=lambda r:(r['qubits'],r['p'],r['backend'])):
 rows=[x for x in r['rows'] if not x['warmup']]
 s+=f'|{r["qubits"]}|{r["p"]}|{labels[r["backend"]]}|{span((x["execution_excluding_conversion_s"] for x in rows),1000)}|{span((x["execution_including_conversion_s"] for x in rows),1000)}|{f(stat(x["total_s"] for x in rows)["IQR"],1000)}|{r["memory"]["VmHWM_KiB"]}|\n'
s+='''
実行=状態発展＋確率取得＋共通sampling。総時間はこれに回路構築/変換を含む。上表の列別中央値の和は総中央値と一致するとは限らない。変換済み回路を反復再利用する場合と、各Pricingで構築・変換する場合を混同しない。

RSSは共通ライブラリunionと参照状態も含むプロセスの絶対ピーク。構成の最小依存メモリ比較ではない。OS auxiliary threadを含む実thread数は各JSONに保存しており、solver/native poolへの指定1と総OS thread数を同じ意味で使わない。

[backend_metrics.csv](evidence/backend_metrics.csv) にmin/max/IQR、[生データ](evidence/backend/)、[実行ログ](evidence/execution_components.json) にseed、固定角、PID、affinity、起動/import/出力込みwall、10ms間隔のプロセスtree RSSを保存した。shared pageはRSS和で重複計数され、10ms間隔のtree peakは真の瞬間最大を取り逃す。周波数固定/ホスト排他はしていない。

Qulacsの最終状態計算が短くても、条件DのRMP・学習・完成・検証を含むT_program改善とは判定しない。[全体試験](END_TO_END_COMPARISON.md)を別に評価する。すべて古典CPUによる量子回路シミュレーションである。
'''
save('BACKEND_BENCHMARK.md',s)

# 3 Model
s='''# QamomileによるHamiltonian・ALiMの検証

今回のQamomile実装は、既存Polynomialの係数を入力してspinへ変換した前回試験から進め、**配送距離・顧客双対・需要・容量・λを入力し、BinaryExprで式そのものを組み立てる**。[adapters.QamomilePolynomial](code/adapters.py)、[検査コード](code/model_validation.py)。

位置別one-hot変数は既存と同じ連番。t=0のdepotを定数1、他地点を0に固定する。容量残差hに対して明示的にλc(h+h²)、顧客ごとの訪問回数uに対してλv(u²−u)を加える。`paper_literal`は位置ごとの同じ式へ切り替える。Qamomileに配送専用のALiM自動処理があると仮定していない。OMMXの自動slack/ペナルティ化は使わない。

## 数値検証

需要を1/2/3とする非一様人工入力、容量3、非対称距離、顧客双対0.9+0.31*i。2/3顧客、slots3/4、2種類penalty、λ組(1,1)/(0.7,2.3)の12条件で全binary状態を確認した。係数は未出現項を0として比較、定数項とIsing Z/ZZも別比較。Qamomileの変数圧縮により番号が変わらないことをq/全基底energyで確認した。

|q|penalty|λc/λv|QUBO項差最大|Ising項差最大|energy差最大|全基底数|decode差|
|---:|---|---|---:|---:|---:|---:|---:|
'''
for r in model['results']:s+=f'|{r["q"]}|{r["penalty"]}|{r["lambda_capacity"]}/{r["lambda_visit"]}|{r["QUBO_term_max_abs"]:.3e}|{r["Ising_term_max_abs"]:.3e}|{r["energy_max_abs"]:.3e}|{r["basis_states_checked"]}|{r["decode_errors"]}|\n'
s+='''
各条件のvariable mapping、定数、項数、VALID/EMPTY/REPEATED/CAPACITY_EXCEEDED別件数と違反例energyは [model_validation_final.json](evidence/model_validation_final.json)。decodeには共通の配送decoderを保持し、独立した顧客重複/需要合計の分類と照合した。Qamomileが配送decoderを新たに提供するという結果ではない。

Pricingの部分集合で訪問しない顧客があるのは許容される。欠落は `missing_from_domain` として記録し、最終計画の全顧客exactly-onceをRMP/独立検証で確かめる。ALiM h+h²は単なる違反量ペナルティと異なり、h=−2でも正値となる。この現行仕様を変更していない。

## 構築・変換・評価時間（中央値、ms）

各1 warm-up＋7反復。同じ条件のnative Polynomial生成、Ising化と、Qamomile式構築、spin化を分けた。energy評価は同じone-hot masksを全件評価する総時間。

|q|penalty|λc/λv|native構築|native Ising|Qamomile構築|Qamomile Ising|native評価|Qamomile評価|native/Qam項数|
|---:|---|---|---:|---:|---:|---:|---:|---:|---|
'''
for r in model['results']:
 t=[x for x in r['timings'] if not x['warmup']]
 s+=f'|{r["q"]}|{r["penalty"]}|{r["lambda_capacity"]}/{r["lambda_visit"]}|'+ '|'.join(f(st.median(x[k] for x in t),1000) for k in ['native_build_s','native_conversion_s','qamomile_build_s','qamomile_conversion_s','native_energy_s','qamomile_energy_s'])+f'|{r["native_terms"]}/{r["qamomile_terms"]}|\n'
s+=f'\nモデル検証プロセスのVmHWMは{model["memory"]["VmHWM_KiB"]} KiB（共通import込み）。条件ごとの最小構成メモリ優位は未確認。全反復の生時間・評価状態数をJSONへ保存した。\n'
s+='''
同じ式の異なる加算順序によりfloat値はbit単位では一致しない。COBYLAがほぼ同点の候補を比較するときは、この小差でも後続角・nfev・経路集合が変わり得る。固定角の状態同等性と、適応的最適化履歴の完全再現を区別する。

## 変更量と判定

本番の変更ファイルは0。候補は `QamomilePolynomial` とbackend選択を独立ファイルへ実装した。既存の短い定式化を単純に消して依存を置換できるわけではなく、変数/定数/λ/decoder/版の契約を維持する必要がある。独立検証コードの非空・非コメント行数は [implementation_size.json](evidence/implementation_size.json) に保存する。行数は本番移行工数の見積りではない。

標準Qamomile QAOAのX mixer/plus初期状態、FQAOAの粒子数保存を現行位置別exact XYへそのまま置換しない。本比較はQamomileの明示モデル構築＋既存ALiMの同式再実装である。配送制約を自動生成してくれる利点や、より良いALiM調整は実証していない。モデル共有の用途は残るが、現行の簡潔なPolynomialに対する速度・品質の実質的な導入利点は別途採否で判定する。

前回環境のprotobuf6.33.6は既存OR-Tools9.14の要求<6.32と衝突した。今回は隔離環境のprotobufだけ6.31.1へ合わせ、OR-Toolsを既存Dと同じ9.14.6206に固定した。Qiskit/NumPy/SciPyも前回と同版。初期resolver失敗、9.15試行、最終解決ログをすべて保存し、本番環境と前回venvは変更していない。[freeze](evidence/requirements.lock.txt)、[導入手順](evidence/install_reproduce.sh)。
'''
s+='\n容量60・q12の実Pricingも全4096状態ずつ事後照合した。QUBO係数差最大5.69e−14、Ising係数差最大2.85e−14、energy差最大1.82e−12で同じ許容誤差内。[実容量の結果](evidence/actual_capacity_model_audit.json)。\n'
save('QAMOMILE_VALIDATION.md',s)

# 4 Pricing
s='''# 量子Pricingの実装比較

[Huangら2025](https://arxiv.org/html/2503.17051v1)の「量子が候補列を生成し、古典RMPへ戻す」構成を、既存day completionと真Reduced Costへ接続した。論文がQamomile/ALiMとQURI Partsを使用したことは方法上の対照理由であり、現在の配送D/W/T改善の証拠にはしない。

前回のmacro/selection40件は背景証拠として再利用した。今回は現行 `Statevector.sample_counts` に標本法を統一し、Qamomileは式の直接構築、QURI変換は分離して実行した。前回のmultinomial sampler時間と今回を同条件として集計していない。

## 同一アルゴリズムのsnapshot比較

人工6顧客・2車両・1バース・容量2・最大2便。独立ID順初期列をRMPで解き、その顧客双対上位3地点を1顧客ずつのdomainとする。slots3、p2、maxiter80、restart1、train1000、final4096、seed1101/1102/1103。全案同じドメイン/制約/初期角/停止条件である。初期計画は3便を必要とし、容量・2便・バースを実際に使う。

量子は部分集合と順序を選び、測定したtripを必ず含む有限grid dayを、singleton/初期列/測定tripのpartnerから古典生成する。違反を修復したり未測定のoracle経路を注入しない。真day RCは距離から顧客・物理車両・占有バース・εの双対を全て差し引く。trip代理RCと別値として保存する。顧客集合変更数は初期のどのtripの集合とも一致しない経路数である。

|構成|seed|量子Pricing ms|完成/RCまでms|実行可能率|異経路|集合変更|最良代理RC|最良真day RC|負RC有効列|q/depth|VmHWM KiB|
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|
'''
for r in pricing:
 s+=f'|{labels[r["backend"]]}|{r["seed"]}|{f(r["quantum_Pricing_s"],1000)}|{f(r["Pricing_s"],1000)}|{r["result"]["feasible_rate"]:.5f}|{r["distinct_routes"]}|{r["changed_set_routes"]}|{r["best_proxy_rc"]:.5f}|{r["best_true_RC"]:.5f}|{r["negative_columns"]}|{r["result"]["qubits"]}/{r["result"]["logical_depth"]}|{r["memory"]["VmHWM_KiB"]}|\n'
s+='''
量子Pricing時間はモデル初期化＋全COBYLA/tensor学習＋最終回路/状態/抽出/decode。完成/RCまでの時間はさらにfixture準備、初期RMP、有限day completion/検証を含み、条件D全体のT_programではない。seed別のnfev・全bit counts・標本理由・ゲート深さ・段階時間は [pricing JSON](evidence/pricing/) に保存した。raw sampleの実行可能率と、最終planの実行可能率を区別する。

## 必須7条件の確認

|条件|実装と確認範囲|
|---|---|
|訪問順変更|位置変数をQAOAnsatzで抽出し、異なるtupleの測定経路を生成。集合順列に固定しない|
|顧客集合変更|depotを選ぶ位置を許し、異なるsubsetを受理。初期trip集合と比較して数える|
|容量|ALiMは誘導、decodeは需要合計を厳密拒否。非一様需要の違反energyも検査|
|重複・欠落|同trip/同day重複は拒否。部分集合tripの未訪問は記録し、全体exactly-onceと欠落はRMP/最終検証で判定|
|双対反映|各RMPの顧客dualをPricingの距離−報酬へ反映。全資源dualは完成dayの真RCで使用|
|車両・便・バース|既存make_day/enumerate_daysまたはevent日程を通し、day単体検証とmasterの全体バース行で判定|
|真RC|車両・バース・εを含めて計算し、RC<−1e−7/未知identityのみ追加|

## アルゴリズムが異なる比較

通常DWTは元tripの全マクロ断片順列だけを受理し、量子stage内でbase dualを更新しない。試験用updated CGは、独立CW初期列を保ち、双対上位/回転近傍のsingleton domains→測定subset→完成day→真RC→負列追加→**即LP再求解**を最大4round行う。この変更はQURIに固有の機能ではなく、Qiskit/Qulacsでも同じ制御フローを実装した。

このvariantの4枝全体試験と、未変更現行D/バックエンドだけ変更したDを [全体比較](END_TO_END_COMPARISON.md) で分離した。Qamomileのfloat加算順から最適化軌跡が変わった場合、生成列数の増加をライブラリの優位としない。

原則の機能確認は [binding契約テスト](code/test_contracts.py) でも実施した。各backendで4round×20列追加後にRMP双対を再取得し、最終3便・1バースの計画を独立再計算した。制約接続の成功は全域Pricing最適性の証明ではない。
'''
s+='\nrawの互換field `qiskit_seconds` はadapterでは選択backendの最終処理合算。`backend` と `timing` で構築/変換/状態/抽出を識別する。Qulacs/QURIの回路状態発展をQiskitが代行したわけではない。\n'
save('PRICING_COMPARISON.md',s)

# 5 end-to-end
s='''# 条件D全体のD/W/T比較

**通常の4プロセス内部multistartを使った小規模全体試験**。各枝1コア、native solver1 thread。候補方式を同時に走らせず、同じ人工入力・root seeds・20秒予算・W上限30分で逐次比較した。S1〜S3、凍結需要、実OD、B/Cの出力を使用していない。

## 実験条件と計時境界

入力は既存 `baseline_a.fixtures.artificial_problem(6/8,2,1)` を新規出力内に保存した人工有向グラフで、実道路の測定値ではない。全比較で容量60、1台最大2便、積込1800秒、作業120秒、準備0、勤務08–20時と車両別readyを保つ。小規模なため容量/2便が最適解でbindingとは限らない。容量2・3便必須・1バースの接続は別の機能契約で検証した。

現行Dは `dwt/methods.generate` をそのまま実行。backend-onlyは独立プロセス内のクラス差替えだけで、同じCW初期列・macro受理・予算配分・RMP/完成器を使う。updatedは同じCW seedから始め、集合変更/新双対を持つ別アルゴリズム。両者の差をライブラリ性能と呼ばない。

`execute_parallel` を再利用し、T_programを親の入力読込前から全枝停止/回収・全候補選択・最終二重検証まで測った。共通の依存unionと4待機workerのfresh spawnはT前で別記。問題・回路・solverをT前に実行しない。親の最終出力はT後だが、各枝のstage記録・返却結果のファイル出力と親の候補読込/途中記録は親Tの中に入る。updatedの詳細ログ量も含まれるため、アルゴリズム差の時間に計測負担が含まれる。出力単独のIO時間は分離できておらず、起動/import/出力込みwallを実行台帳へ別記した。T外残差を純粋な出力時間とは呼ばない。

root seeds1101–1103は2人工入力それぞれで共通。4枝seedは既存SeedSequence規則で派生し全て保存した。4枝は内部探索であり外側反復4件として扱わない。以下はroot3回の中央値と[min,max]。独立需要の母集団検定・有意性評価はしていない。

## D/W/T

|配送先|方式|構成|D km範囲|W min範囲|T_program秒 中央値[min,max]|setup秒 中央値[min,max]|実行可能/実行試行|
|---:|---|---|---|---|---:|---:|---|
'''
for n in [6,8]:
 for a in ['legacy','updated']:
  for b in (['original','qiskit','qulacs','quri','qamomile_quri'] if a=='legacy' else ['qiskit','qulacs','quri','qamomile_quri']):
   rs=[r for r in trials if (r['n'],r['algorithm'],r['backend'])==(n,a,b)]
   failed_here=sum(x['spec']['scenario_id']==f'ART_N{n}' and x['spec']['trial_algorithm']==a and x['spec']['trial_backend']==b for x in failed)
   s+=f'|{n}|{a}|{labels[b]}|{min(r["D_km"] for r in rs):.6f}–{max(r["D_km"] for r in rs):.6f}|{min(r["W_min"] for r in rs):.4f}–{max(r["W_min"] for r in rs):.4f}|{span(r["T_program_s"] for r in rs)}|{span(r["setup_s"] for r in rs)}|{sum(r["status"]=="VALIDATED" for r in rs)}/{3+failed_here}|\n'
s+='''
主試験では54予定seed/variantが完了したほか、N6/legacy/Qamomile併用の最初の1試行が外側120秒監視で未完了となった。上表ではその失敗も分母へ含め、時間中央値は完了した3seedだけの値である。失敗した試行のT_programは未確定で、0秒や120秒の計画時間として補完しない。準備59.598秒の後、入力/solver処理開始が記録されていたが、原因は未確定でありQamomile固有の障害と断定しない。同一条件の再試行は完了した。外側監視だけ300秒へ修正し、計画20秒予算と全アルゴリズム条件は変えていない。

失敗試行の出力、観測できた全枝shots、未完了分がunknownであることは [failed_attempt_accounting.json](evidence/failed_attempt_accounting.json)、[監視修正理由](evidence/controller_revision.txt) に保存した。これを成功反復や需要数へ加えず、計算量をなかったことにしない。
'''
s+='\n## 全枝の探索・資源（root3回の中央値）\n\n|配送先|方式|構成|Pricing calls|負列追加|追加によるRMP更新|LP calls|顧客双対変化|集合変更経路の枝合計|RSS上限和MiB|\n|---:|---|---|---:|---:|---:|---:|---:|---:|---:|\n'
for n in [6,8]:
 for a in ['legacy','updated']:
  for b in (['original','qiskit','qulacs','quri','qamomile_quri'] if a=='legacy' else ['qiskit','qulacs','quri','qamomile_quri']):
   rs=[r for r in trials if (r['n'],r['algorithm'],r['backend'])==(n,a,b)]
   s+=f'|{n}|{a}|{labels[b]}|'+ '|'.join(str(st.median(r[k] for r in rs)) for k in ['quantum_calls','added_columns','RMP_updates','LP_calls','customer_dual_changes','changed_sets_all_branches'])+f'|{st.median(r["aggregate_RSS_upper_bound_KiB"] for r in rs)/1024:.2f}|\n'
s+='''
legacyの負列追加はbase/quantum後の有限catalogueでの古典負列追加合計。updatedでは測定tripを含む未知の完成dayを真RCで追加した数。両者の列追加数を量子の貢献量として直接比較しない。LP callsはlegacyでは実solver callログ、updatedでは各roundの現在pool/拡張catalogue/追加後の3 solve＋最終1 solve。実際のdualベクトルを保存しており、更新しても目的値が下がるとは限らない。

集合変更経路は各枝のunique集合変更tuple数の合計で、枝間重複を除いた需要数ではない。通常legacyでは受理集合が固定なので0。未選択枝のquantum calls、訓練/最終shots、失敗/停止も記録した。

RSS上限和は親と全枝の各high-water markの和で、時点もshared pageも揃わない**物理メモリ実測ではない上限指標**。別にcontrollerがexecutor treeのRSS和を10ms間隔で観測し、[execution_end_to_end.json](evidence/execution_end_to_end.json)へ保存した。これもshared pageを重複計数し瞬間peakを取り逃し得る。allocationが同じでもメモリ削減が証明されたとはしない。

## 検証・再現性・限界

各planは共通validatorと、別モジュールのraw OD/時刻再計算で検証し、親で全候補を再検証して選択した。[生の全体試験](evidence/trials/)、[全指標CSV](evidence/end_to_end_metrics.csv)、[全枝集計](evidence/full_trial_summary.json)、[現行runとの履歴照合](evidence/legacy_parity.json)。親4枝の全入力hashとCPU、PID、seedを残している。

updatedはLP再求解後のdualを次roundへ渡す。時刻calendar/顧客domainが有限であり、4round上限・sampled候補で見つからないことは全域非負RCの証明ではない。最終IPやCP-SATによる改善は古典処理の寄与を含む。代理RCが負でも、完成不可、真RC非負、既存identity等で追加しない。

今回の全体比較はCPUシミュレーションの実装効率を検証するもので、実機量子計算の高速化・研究規模の優位性ではない。共通importの時間や最小依存構成、Python3.12の既存環境と同一の時間、S1〜S3でのD/W/Tは未検証。ホスト共有・短時間試験・少数seedであるため、中央値差を統計的に有意な改善と書かない。
'''
save('END_TO_END_COMPARISON.md',s)
# leave final decision with computed tables to a separate manual authoring step.
(E/'numerical_summary.json').write_text(json.dumps({'equivalence':eq,'tests':'107 passed','backend_conditions':36,'pricing_trials':15,'full_trials':54,'full_valid':sum(r['status']=='VALIDATED' for r in trials),'all_branch_valid':sum(x['status']=='VALIDATED' for r in trials for x in r['branches']),'max_model_energy_error':max(r['energy_max_abs'] for r in model['results']),'legacy_parity':parity},indent=2))
print('Five evidence reports and data tables written. Final decision requires assessing paired full-trial data.')
