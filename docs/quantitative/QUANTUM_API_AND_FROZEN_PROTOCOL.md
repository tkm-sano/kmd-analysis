# Quantum APIと凍結Protocol V2

## 1. 正式Candidate C

再利用入口は `src/kmd_quantitative/quantum/`。研究当時の実装は物理移動せず、[共有science](../../05_src/traffic_simulation/matched_quantum_protocol_v2_shared/science.py)と[R1 worker](../../05_src/traffic_simulation/matched_quantum_r1_c_protocol_v2/worker.py)に保持する。R0 fullは共有science、R1 fullはR1資格workerに接続する。APIの整備は科学結果の更新や公開許諾を意味しない。

## 2. PUBO構築

[builder.py](../../src/kmd_quantitative/quantum/builder.py)の `build_C(model,a)` は `(q, poly)` を返す。q=n²、polyはビットindexのtupleをキーとするDecimal係数。変数indexは `(customer-1)*n+position`。`route_code(order,n)` はindexを下位bitから数える整数で、Qiskit表示文字列の左端がbit0という意味ではない。両one-hot、道路旅行時間、可行性事前表の違反完全順列に対するn次罰則を元の関数ASTから計算する。罰則Aはmodelのpenalty_s。目的は電力量でなく道路旅行時間。

入力aはnodes/travel/distance/ready/due/service/demand等の正式配列契約、modelはn/penalty_s/capacity_ok/permutations等の完全な事前情報。欠落した順列表を補ったり、任意の配送問題向けに制約を一般化するAPIではない。

## 3. 復号と可行性

[formal.py](../../src/kmd_quantitative/quantum/formal.py)が正式処理へのadapter。

- `feasible_route_table(model,a)`：事前表でcapacity/TIME_WINDOW/RETURN_HORIZONを満たす順列をroutingの独立validatorで検査し、code→経路表と事後評価用の厳密最小旅行時間を返す。表が空なら元実装と同じAssertionError。
- `parse_sample_counts(raw_counts,shots)`：Qiskit形式の文字列キーを整数へ変換し総shotsを検査。空白区切りを除去する元処理。非binary文字はValueError、shots不一致はProtocolFailure。
- `evaluate_final_counts(model,a,counts)`：整数codeを可行表へ照合し、最終経路を再度独立validatorで検査して返す。返り値は `final_feasible_count`, `sampled_feasible_routes`, `best_final_feasible_route`。

このAPIは信頼されたsampler契約の入力用。幅・負数・bool等に対する包括的入力防御を元コードに追加したものではない。未知の整数codeは除外される。正しい可行問題に可行標本がない場合は空経路一覧・Noneであり、可行問題自体がない場合とは異なる。`python -O` は使わない（正式validatorはassertを利用）。

## 4. 最終経路選択

`select_final_route(routes)` は独立検査済みの正式recordを前提とする低水準API。道路旅行時間のDecimal値、整数bitstringの昇順でminを選ぶ。頻度・最適フラグは同点の基準ではない。空一覧はNone。正式標本の復号も必要ならevaluate_final_countsを使う。

parameter incumbentの選択は別規則：域内・有限評価から可行標本数最大→平均エネルギー最小→評価index最小、可行標本ゼロなら平均エネルギー→index。既存protocol.pyに保持し、今回移行しない。最終4096標本のみが経路取得のauthority。probe標本を混ぜない。

## 5. 古典・量子の分担

入力構築、全順列可行性、PUBO、COBYLA、復号・独立検証・経路選択は古典処理。正式QAOAは理想StatevectorSamplerであり実機ではない。p=1、H初期状態、X mixer、最大100目的評価・各2048shots、独立seedの最終4096shots。詳細条件は凍結protocol/planを優先する。

静的回路生成元は static_reduced_circuit_resources.py（Hayate保存参照: `05_src/traffic_simulation/matched_quantum_qualification/static_reduced_circuit_resources.py`、公開ツリー非同梱） のbinary_poly_to_z/make_circuit。回路はAで正規化したpolyをx=(1−Z)/2へ変換し、RZ/RZZ/CXパリティ列とRx(2β)を構成する。scienceは保存QPYを読み、目的評価のmean_energy_sには非正規化PUBOを使用する。この違いを同一視しない。生成scriptはトップレベルに出力処理があり、importしない。今回回路生成・実験は行っていない。

## 6. 利用例

repo rootから `PYTHONPATH=src python -B`、またはJupyterでrepoのsrcをsys.pathへ加える。既存Notebook環境を利用する。

```python
from kmd_quantitative.quantum import builder, formal
# aとmodelは02 Notebookまたは正式入力契約に従って用意する。
q, poly = builder.build_C(model, a)
counts = formal.parse_sample_counts(raw_counts, shots)
result = formal.evaluate_final_counts(model, a, counts)
print(result['best_final_feasible_route'])  # Noneも正当な結果
```

確認済みコマンド：`python -B tests/test_formal_quantum_api.py` と `python -B notebooks/test_notebooks.py`。前者はnumpyと既存fixture、後者はnotebooks/requirements.txtの環境を使う。例のa/model/raw_countsは自動取得されない。

## 7. 凍結sourceとの接続

scienceのSHA256を固定し、純粋関数とexecute_child内の必要な文のASTのみcompileする。workerのimport、トップレベル、execute_child全体、sampler、COBYLA、write_newは実行しない。数式・判定を別ファイルへコピーしない。source不足・hash不一致は失敗する。src単独配布は不可で、science.pyも必要。

新APIは新routingのindependent.pyを利用する。保存例のplan指定validatorとbytes一致を確認した。R1 workerはn=4と16bitを固定、共有sourceはmodel nとqを使う。対応箇所だけを正規化したAST比較と4顧客の出力比較で確認し、R1を3顧客へ適用したとはしない。

## 8. qualificationとの差

qualification_builder.pyはprefix-AND補助変数を含むQUBOで、正式Candidate Cは補助変数なしのPUBO。前者の可行性・罰則metadataは最終V2にも利用される。decoder.pyはbit配列の幅・binary・one-hot・物理条件・ancillaを独立検査する。正式V2はこのdecoderを呼ばず可行表とvalidatorを使う。両者の入力・エラー・出力形式も異なる。

## 9. Notebookとの差

02の回路は未正規化PUBOのdense教材回路、既定64shots、最大6評価の任意最適化は未検証。正式QPYの正規化、角度、seed、2048/4096shotsの再現ではない。PUBOと最終標本判定のみ正式APIへ統一した。既定の最終可行0/64はNOT_ACQUIREDのまま。教材結果を正式R0/R1結果に置き換えない。

## 10. 再利用範囲・制約

小規模PUBO・可行表・記録済み標本判定・Notebookの再利用が対象。新APIとNotebookは移行済み旧4互換リンクを必要としないが、凍結science等の05_src実ファイルは必要。全量workerは旧path、source freeze、QPY/instance/validator、固定環境、Linuxのfcntl/resource等に依存する。全量再実行・Windows・新規環境install・Colabは未検証。公開権利は未確定。

根拠：第3段階の検証（Hayate保存参照: `docs/audits/quantitative_repository_structural_migration_20261009/19_PHASE3_REGRESSION_TEST_RESULTS.md`、公開ツリー非同梱）。
