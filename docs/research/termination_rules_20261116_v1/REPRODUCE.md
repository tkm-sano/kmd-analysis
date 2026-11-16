# 再現手順

リポジトリroot /home/takuma/kmd-analysisで実行する。新規パッケージをinstall/updateしない。Pythonは既存venv、共通ローカルprefixを全手法に等しく適用する。使用版・実ファイルhashはDEPENDENCY_FILES.json、外部資源上限はEXTERNAL_ENVIRONMENT.jsonに保存した。新fresh子のimportはT内である。

```bash
cd /home/takuma/kmd-analysis
export PYTHONPATH=/opt/miniconda/envs/qgpu/lib/python3.12/site-packages:src
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
termination_python=/home/takuma/.cache/kmd-analysis/venvs/ad-pipeline-v1/bin/python
"$termination_python" -m pytest tests/toc_termination_v1 -q
```

本作業で登録・実行する実規模の確認（各規模×5手法×1回、計15試行）の正本は以下である。登録時に設定/入力/コード/seed/順序/コアを固定しsnapshotを保存する。既存directoryへの再registerは拒否する。runは完了済みIDを上書きしない。STARTEDのみの未完了IDを自動再実行しない。操作を再現する場合は別の新ID/directoryを使い、旧結果を保全する。

```bash
"$termination_python" scripts/run_termination_rules.py register output/toc_delivery/termination_rules_20261116_v1/scales_02
"$termination_python" scripts/run_termination_rules.py run output/toc_delivery/termination_rules_20261116_v1/scales_02
"$termination_python" scripts/run_termination_rules.py aggregate output/toc_delivery/termination_rules_20261116_v1/scales_02
"$termination_python" scripts/audit_termination_rules.py output/toc_delivery/termination_rules_20261116_v1/scales_02
```

再集計・監査の最後2コマンドは既存結果を読み、集計ファイルだけを更新する。runにtimeout、旧tau、native秒数、品質目標停止を渡す入口はない。Ctrl-C/SIGTERMやRSS資源停止の場合はその状態と未実行を残す。異常試行を上限・seedの事後変更で成功へ置き換えない。新登録を実行する前にRUN IDの重複とsource差分を確認する。本実験manifestは実行不能であり、このCLIはsmall_fixtureとscale_functional_checkのphaseだけ実行する。

小規模確認は別phaseとして以下を実行した。small_01はアダプター不備を記録した失敗バッチ、small_02/03は修正の確認、small_04はSAT内側dtime依存の前処理を無効化、small_05はCの初期候補保全も確認した最終設定の確認である。それぞれsnapshotと全失敗を保全する。人工入力を本実験用需要へ代用しない。

```bash
"$termination_python" scripts/run_termination_rules.py register-fixture output/toc_delivery/termination_rules_20261116_v1/small_05
"$termination_python" scripts/run_termination_rules.py run output/toc_delivery/termination_rules_20261116_v1/small_05
"$termination_python" scripts/audit_termination_rules.py output/toc_delivery/termination_rules_20261116_v1/small_05
```

過去snapshotの再現にはtarを別のチェックアウトへ展開する。working treeへ上書き展開しない。REGISTERED.jsonのsource_hashesとtarメンバーhashを照合し、入力filesとfreeze hashも確認する。HEADだけでは追跡外ソースを再現できない。凍結入力は既存input_rootのS1/S2/S3を用い、ODを再生成しない。別マシンではcpu_idsと依存パスを事前登録し直して別IDとし、同一資源・Tとして混合しない。4物理コアが不足した場合は逐次へfallbackせず登録/実行を拒否する。

設定選択はSTOPPING_RULES.mdの構造的基準による単一基準設定である。旧150秒へ実測を近づけるチューニングや勝者に合わせた候補選択を行っていない。小規模の不具合修正はAMENDMENTS.jsonに残す。今回の確認を分散データ・本実験へ流用せず、新設定での分散測定後にR、精度、多重性等の研究上の解析条件を別登録する。

既存共通D/W目標への記述用照合は、試行コードや採否を変更せず次で行う。閾値は旧comparison_designの事前設定をそのまま読み、終了Tを初到達時刻へ置換しない。新設定の本実験用品質目標を採択したという意味ではない。

```bash
"$termination_python" docs/research/termination_rules_20261116_v1/ANALYZE_RECORDED_TARGETS.py
```

COUNTER_DEFINITIONS.jsonは実行回数/評価要求/cache/実測shots/列挙候補の定義である。RESULT_SCHEMA.jsonは終了理由・実行状態・計画状態・採用を分離した実行済み結果のschemaであり、旧deadline必須schemaを緩めて流用しない。未実行は集計上NOT_STARTEDとして残す。HIGHS_OPTION_VERIFICATION.jsonは使用中ネイティブAPIでのoption受理確認であり、試行結果ではない。

最終のschema・保全・報告生成は次で再現する。初回の保全監査で見つかった無関係な登録前変更を上書きしない。PRETRIAL_UNRELATED_CHANGE.jsonと初回監査*_01を参照する。

```bash
"$termination_python" docs/research/termination_rules_20261116_v1/FINALIZE_REPORT.py
```

別ディレクトリでソースと凍結付帯ファイルを復元する場合は以下である。大容量の凍結入力/ODは元の読取対象をsymlinkし、hashで同一性を確認する。既存working treeへtarを上書き展開しない。登録は新しい保存先へ行い、必要な確認件数を実行する場合だけ明示的にrunする。本手順の復元検証では追加の計画作成試行を実行していない。

```bash
termination_replay_root=$(mktemp -d /tmp/termination-replay.XXXXXX)
tar -xzf /home/takuma/kmd-analysis/output/toc_delivery/termination_rules_20261116_v1/scales_02/SUPPORTING_ASSETS.tar.gz -C "$termination_replay_root"
tar -xzf /home/takuma/kmd-analysis/output/toc_delivery/termination_rules_20261116_v1/scales_02/SOURCE_SNAPSHOT.tar.gz -C "$termination_replay_root"
mkdir -p "$termination_replay_root/output/toc_delivery/ad_pipeline_20261112_route_v2/roads"
ln -s /home/takuma/kmd-analysis/output/toc_delivery/ad_pipeline_20261112_route_v2/roads/inputs "$termination_replay_root/output/toc_delivery/ad_pipeline_20261112_route_v2/roads/inputs"
cd "$termination_replay_root"
export PYTHONPATH=/opt/miniconda/envs/qgpu/lib/python3.12/site-packages:"$termination_replay_root/src"
"$termination_python" -c 'from kmd_toc.comparison_v1.contract import check_freeze; from kmd_toc.common.config import load_conditions; check_freeze(); load_conditions(); print("frozen assets verified")'
"$termination_python" scripts/run_termination_rules.py --help
```

他ホストへ移す場合は既存venvの同版ライブラリ・VeRyPy保存sourceも再現し、CPU/依存pathを別IDへ事前登録する。ここでの正確なコマンドとTはこのホストの記録であり、他ホストのT同一性を主張しない。
