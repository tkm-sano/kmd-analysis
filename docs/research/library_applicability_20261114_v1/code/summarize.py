from pathlib import Path
import json,statistics as st,csv
R=Path(__file__).resolve().parents[1];E=R/'evidence'
rows=[json.loads(p.read_text()) for p in sorted((E/'measurements').glob('*.json'))]
assert len(rows)==40
metrics=['training_s','formulation_adapter_s','circuit_build_s','state_evolution_s','sampling_s','pricing_kernel_s','small_pipeline_s','postprocess_completion_RMP_IP_validation_s','max_rss_KiB','cpu_s']
summary={}
for case in ['macro','selection']:
 summary[case]={}
 for backend in ['qiskit','qulacs','quri','qamomile_ising']:
  rs=[r for r in rows if r['case']==case and r['backend']==backend]
  assert len(rs)==5
  summary[case][backend]={k:dict(median=st.median(r[k] for r in rs),min=min(r[k] for r in rs),max=max(r[k] for r in rs)) for k in metrics}
 for seed in range(1101,1106):
  rs=[r for r in rows if r['case']==case and r['seed']==seed];base=next(r for r in rs if r['backend']=='qiskit')
  for r in rs:
   for k in ['trace','optimized_angles','nfev','sample_counts','routes','feasible_rate','negative_valid_day_columns','integer_objective','changed_set_routes','logical_depth']:
    assert r[k]==base[k],(case,seed,r['backend'],k)
(E/'benchmark_summary.json').write_text(json.dumps(summary,indent=2))
keys=['case','backend','seed','pid','nfev','qubits','logical_depth','feasible_rate','best_penalized_sample_energy','best_valid_energy','best_trip_rc','distinct_routes','changed_set_routes','negative_valid_day_columns','added_columns','best_true_day_rc','integer_objective',*metrics]
with (E/'benchmark_metrics.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows({k:r[k] for k in keys} for r in rows)
labels={'qiskit':'Qiskit','qulacs':'Qulacs直接','quri':'QURI＋Qulacs','qamomile_ising':'Qamomile Ising＋Qiskit'}
s='''# 小規模実測結果

実施日: 2026-11-14 JST。40件すべて成功。**Qulacsは同じAOAの最終状態発展を短縮したが、解品質の向上と本研究のT_program改善は確認していない。QamomileのIsing変換併用に性能上の利点は確認できない。**

## 実行環境と証拠

Python 3.11.15、Linux 6.8.0-147-generic x86_64、AMD EPYC 9684X、CPU ID0に固定。native thread1、全案のアドレス空間上限4 GiB。NumPy2.3.1、SciPy1.16.0、Qiskit2.1.1、Qulacs0.6.14、QURI Parts circuit/core/qulacs0.28.0、Qamomile0.15.2。venvは `/tmp/kmd-library-survey-20261114`、全依存は [requirements.lock.txt](evidence/requirements.lock.txt)。既存環境にinstallしていない。

人工4顧客・2車両・2バースのみ。詳細条件は [プロトコル](BENCHMARK_PROTOCOL.md)。40独立プロセス、各案間は逐次。CPU自体は共有ホストであり排他的占有・周波数固定ではない。5 seedsは同じ需要の乱数感度で、独立需要5件ではない。単位時間が短いため順位/速度比を一般化しない。

生データ: [各測定JSON](evidence/measurements/)、[全指標CSV](evidence/benchmark_metrics.csv)、[集計JSON](evidence/benchmark_summary.json)、[PID・実行順・起動時間・stderr](evidence/benchmark_execution.json)、[ハードウェア情報](evidence/benchmark_execution.json)。共通importを計時前に行い、その起動/import/出力込み時間も別記録した。ソースコードの識別はpreservation manifest、測定前のコード/プロトコル識別は [freeze](evidence/protocol_freeze.json)。

## 時間

以下は5 seedsの中央値、単位ms。列ごとの中央値の和は総時間の中央値に一致しない。kernelは学習・回路構築・状態発展・最終sampling・Qamomile式変換。小pipelineは初期RMP・Pricing初期化・day完成・真RC・追加・再LP/IP・日程検証までを含む。本番の親4枝T_programではない。
'''
for case in ['macro','selection']:
 s+=f'\n### {case}\n\n|構成|学習|式変換追加|回路構築|状態発展|最終抽出|Pricing kernel|小pipeline|\n|---|---:|---:|---:|---:|---:|---:|---:|\n'
 for b,label in labels.items():
  d=summary[case][b];s+='|'+label+'|'+'|'.join(f'{1000*d[k]["median"]:.4f}' for k in ['training_s','formulation_adapter_s','circuit_build_s','state_evolution_s','sampling_s','pricing_kernel_s','small_pipeline_s'])+'|\n'
 s+='\n|構成|kernel範囲ms|小pipeline範囲ms|最大RSS範囲KiB|プロセスCPU秒の中央値（import込み）|\n|---|---:|---:|---:|---:|\n'
 for b,label in labels.items():
  d=summary[case][b];rng=lambda k,scale:f'{scale*d[k]["min"]:.3f}–{scale*d[k]["max"]:.3f}'
  s+=f'|{label}|{rng("pricing_kernel_s",1000)}|{rng("small_pipeline_s",1000)}|{rng("max_rss_KiB",1)}|{d["cpu_s"]["median"]:.4f}|\n'
s+='''
Qulacs直接は最終状態発展で両ケースの中央値を短縮した。QURI経由では変換・wrapperの時間も含まれる。学習は共有のNumPy tensor/COBYLAなのでSDK変更による高速化対象ではない。小pipelineの順位はkernelの順位と一致しない。Qamomileの追加変換は同じenergyを得る処理で、改善アルゴリズムではない。

最大RSSはfresh workerの共通import込み絶対ピーク。全案で共通の依存を読み込んでいるため、ライブラリを最小構成で使った場合のメモリ優越性を示さない。6/12 qubitsの生statevectorは1024/65536 bytesで、プロセスRSSの大部分はそれ以外。上限4 GiBを使用した量と誤認しない。

## 品質・経路生成・負Reduced Cost

各seedについて4構成の最適化履歴、角度、nfev、共通samplerのcount、受理経路、実行可能率、負RC列数、IP目的、論理深さが**一致**した。下表はQiskit列で全案を代表する。式変換の丸め以外に探索条件の差はない。

|case|seed|実nfev|raw実行可能率|受理異経路|集合変更経路|新規負RC day列|最良raw energy|最良trip代理RC|最良day真RC|最終IP km|
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
'''
for r in rows:
 if r['backend']=='qiskit':
  s+=f'|{r["case"]}|{r["seed"]}|{r["nfev"]}|{r["feasible_rate"]:.6f}|{r["distinct_routes"]}|{r["changed_set_routes"]}|{r["negative_valid_day_columns"]}|{r["best_penalized_sample_energy"]:.6f}|{r["best_trip_rc"]:.6f}|{r["best_true_day_rc"]:.6f}|{r["integer_objective"]:.6f}|\n'
s+='''
raw energyはmacroの全断片受理filterより前のVALID標本を含む。VALID標本の最良energyはこの入力では最良raw値と同じ。trip代理RCはfilter後の受理経路、day真RCは古典partner/車両/時刻を完成後の列の値。これらを同じ目的値として比較しない。負RC day列80/560は、同じ経路でも車両/積込時刻が異なれば別列。既存経路を含む測定tripと古典partner/時刻の組合せも含むので、すべてを量子による新経路改善と帰属しない。

各測定は最大20負列を追加した後LPを再求解しIPを選択。全件、初期LP=更新LP=最終IP=2.1 km、日程検証成功、W=0分。負RC列を見つけてもこの1 batchで最終目的は改善していない。マスターは有限列の選択で、全域最適・完全Pricingの証明ではない。

macro: 6 qubits、one-hot9状態、論理depth15、受理2経路、集合変更0。selection: 12 qubits、one-hot64状態、depth33、受理9経路、集合変更7。この差は**ドメインと受理filterの変更**に起因する。ライブラリの効果ではない。両方とも密XYを1論理ゲートとした深さで、実機native回路深さは未測定。

'''
total_train=sum(r['nfev']*1000 for r in rows);total_final=len(rows)*4096
s+=f'全40件の訓練shots相当は{total_train:,}、最終shotsは{total_final:,}。すべて古典Statevector/圧縮tensorシミュレーションであり、実機shotsではない。各seed/構成の実nfev×1000を保存し、未選択候補の計算を省いていない。\n'
s+='''
## 同値検査と既存runの確認

[検査結果](evidence/equivalence_checks.json)、[ログ](evidence/equivalence.log)。Qamomile BinaryModel/Isingと既存Polynomialの全計算基底64＋4096個を比較した。最大energy差はmacro 3.56e−15以下、selection 3.56e−14以下。4角度×3backend×2caseの24状態検査で1−忠実度の絶対値は6.7e−15以下、one-hot漏出は1e−8未満。

既存 `PricingAOA.run()` を両ケースseed1101でそのまま実行し、学習履歴と最適角がadapterと完全一致した。既存の最終 `Statevector.sample_counts` と今回の共通PCG64 samplingは同じ標本列ではない。元runの実行可能率はmacro0.786133/selection0.598633、adapterは0.782715/0.610596。samplerの差による標本変動であり、改善の証拠ではない。元runのtotalは参照値としてJSONに保存し、adapter時間との速度比に使わない。

Qamomile標準 `QAOAConverter` → QURI Parts → Qulacsも同じselection QUBO、p2、固定角、4096 shots、seed1101で実行できた。one-hotに該当した標本は6/4096。標準回路はplus初期状態/X mixerであり、本来one-hot XYの下で使う同じQUBOにはone-hotペナルティを追加していないため、同等問題空間の比較にならない。適切に定式化した標準QAOAの品質評価やQamomileの性能欠陥という結論には使わない。標準converterをそのまま現行Dへ置換できないことの確認である。

## 失敗・未実施項目

- 最初の隔離pip解決では `quri-parts-qiskit==0.28.0` のQiskit>=2.2要求と既存2.1.1が衝突した（[install.log](evidence/install.log)）。そのadapterを外し、直接の回路構築で比較した。Qamomile公式qiskit extraも>=2.3要求なので使用しない。任意の `--no-deps` 強制導入をしていない。成功した導入ログは [install_core.log](evidence/install_core.log)。
- 初回4 GiB制限下のnative solver abort(-6)を [別ログ](evidence/benchmark_execution_resource_attempt.json) に保全した。原因確定には至らないが、独立プロセス内のHiGHS明示threads1 adapter適用後は全40件成功。SciPyのoptions転送warningはstderrに保存した。
- Qamomile custom qkernelによる既存**exact** XY全置換の性能、FQAOA/QRAO/GAS/QSVT、QURI Algo/VM/cuQuantum、GPU、noise、実機は未測定。Qamomile定式化併用試験をこれらの性能実証にしない。
- 通常DWTの4並列全体T_program、S1〜S3、凍結需要/実OD、本研究D/Wの優越性、最小依存構成別RSS、複数ホストでの再現、native hardware depthは未測定。
- 独立需要を使う統計的なRQ/仮説検定は実施していない。5 seedsから信頼区間や有意な優越性を主張しない。

既存の小規模回帰テストは [regression_tests.log](evidence/regression_tests.log)。保全確認は [preservation_check.json](evidence/preservation_check.json)。
'''
(R/'BENCHMARK_RESULTS.md').write_text(s)
print('40 paired records verified; summary and report written.')
