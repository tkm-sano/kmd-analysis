# Jupyter Notebookの利用

Hayateの現行Python実装・freezeを正本にした公開インターフェースです。別の公開リポジトリは作成しません。まず `00`、次に `01 → 02 → 03 → 04 → 05` を実行します。各冊は独立してRun Allできます。

|Notebook|入力・処理|出力・主な限界|
|---|---|---|
|[00_start_here](00_start_here.ipynb)|依存38件のhash・環境|全モデルの妥当性ではない|
|[01_classical_routing](01_classical_routing.ipynb)|人工3顧客→正式全列挙solver/独立validator|巡回40秒、時間窓変更、不能・容量違反検出|
|[02_pubo_qaoa](02_pubo_qaoa.ipynb)|正式PUBO関数・decoder→教材dense p1回路|9qubit・評価64/最終64標本（別seed）。実機/正式Protocolの再実行ではない|
|[03_battery_energy](03_battery_energy.ipynb)|正式質量文のadapter→正式DC核|20kWh・3段階、人工定速/変更例。量子材料計算なし|
|[04_quantitative_results](04_quantitative_results.ipynb)|最終freeze/CSVの読取り|R0/R1、共通64、pp、配送制約の保存診断|
|[05_scale_analysis](05_scale_analysis.ipynb)|保存済み6規模集計|古典の解法・時間・制約・Battery感度。再最適化なし|

## 環境と実行

最新版は[新規環境ガイド](../reproducibility/environment/QUICKSTART_ENVIRONMENT.md)です。解決済みquickstart lockを使い、rootで `python -B scripts/verify_quickstart.py` を実行すると45件のAPIテストと6冊をまとめて検証できます。以下の直接依存requirementsは旧来の入口として保持しています。

Python 3.12.3、[requirements](requirements.txt)の環境でnbclient/Jupyter kernel実行を確認しています。既存のJupyter環境とは分離したvenvを推奨します。

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r notebooks/requirements.txt
.venv/bin/python -m ipykernel install --user --name kmd-notebooks --display-name 'KMD notebooks'
```

上記は利用者向けのセットアップ例。今回はHayateのrepo外venvに同じpackageを導入し、kernelを一時登録してnbclientで実行しました。既存Jupyter UIから登録kernelを選び、repo rootまたはnotebooksを作業ディレクトリにしてください。JupyterLab等のUI自体はこのrequirementsに含めません。UI未導入なら別途準備が必要です。テストはUI不要です。

```bash
python -B notebooks/test_notebooks.py
```

現在のPythonをkernelとして6冊を自動実行します。結果は標準出力、元Notebookは通常書換えません。`--save-outputs` はNotebook自身の表示出力だけを更新します。正式コード・入力・freezeは変更しません。`--report NEW_PATH.json` は新規報告ファイルのみ作成します。`python -O`は使用しないでください。

## 入力変更

01の時間窓、02のγ/β/seed/shots、03の比エネルギー/速度係数、04/05の表示フィルタを変更できます。fixtureは人工データで、実研究の観測結果ではありません。各冊のassertには初期fixtureの基準値が含まれます。自由な問題サイズ変更を受け付ける一般ソルバーUIではありません。

高負荷の実験は用意していません。02の任意COBYLA最大6評価分岐は通常無効・自動検証外です。正式Protocol V2の100評価・2048/4096shots、保存QPY・監督処理とは異なります。可行経路が取得できない場合はNOT_ACQUIREDを表示し、結果に合わせて自動調整しません。

## 正式sourceとの対応

`adapters.py` はhashを照合し、solver/validator/DC/decoder等を直接importします。Candidate Cはsrc/kmd_quantitative/quantum API経由で正式science.pyの4関数AST、最終選択は同sourceの式を無変更で呼びます。質量はBattery APIからreview_pack_specific_energy.pyの計算文だけを無変更で呼び、Energy APIは正式DC核へ接続します。mainのファイル書込みや資料生成は実行しません。数理モデルの別実装をutilsに作っていません。

02の回路表現は教育用で、正式ゲート分解/回路資源と同等ではありません。03の任意比エネルギーは同じ質量式を使う教育用条件で、凍結条件の変更ではありません。

[dependencies.json](fixtures/dependencies.json)に38依存（正式API・設定・合成fixture・保存結果）の相対パス・SHA256・容量を記録しました。保存結果は原本を直接読み、抜粋データの複製は作りません。大容量OD・実住所・SUMO軌跡・第三者PDF・native binaryは通常セルで要求しません。合成fixtureの由来は以前のpreviewですが、正式モデルは現repoのソースです。

## GitHubからの利用

権利承認と必要ファイルの反映後、同じリポジトリをcloneし、[環境ガイド](../reproducibility/environment/QUICKSTART_ENVIRONMENT.md)に従ってください。現時点でcommit/pushは未実施です。Colabは今回対象外で、動作確認済みとはしません。

## 結果と公開条件

Notebookの保存出力は小型例・既存集計の表示で、新しい科学結果freezeではありません。全配送充足、量子優位性、社会システム全体の省エネを主張しません。L1静的計画/L2走行完了/L3実時刻時間窓/L4実業務を区別します。

同梱コード・集計のLICENSE適用範囲、第三者由来の利用条件・引用metadataは既存監査の留保を継承します。動作成功と公開権利承認は別です。[Model Index](../docs/quantitative/QUANTITATIVE_MODEL_INDEX.md)、[実行ガイド](../docs/quantitative/CURRENT_EXECUTION_GUIDE.md)、今回の報告（Hayate保存参照: `docs/audits/github_jupyter_integration_20261009/NOTEBOOK_IMPLEMENTATION_REPORT.md`、公開ツリー非同梱）。

## 構造移行 第1段階

古典solver・独立検証は `src/kmd_quantitative/routing/solver.py` / `independent.py` が正式配置です。01/02は新パスを直接参照し、dependencies.jsonも同じ15依存のうち2パスだけを更新しました。計算sourceの内容hashは移行前と同一です。00/01/02の古い保存出力は消去し、Run Allで現在の表示を取得します。過去のsource位置には相対互換リンクを残し、研究freezeに記録されたhashを維持します。

通常のpackage importはrepository rootで `PYTHONPATH=src` を設定して `from kmd_quantitative.routing import solver, independent` を利用します。まだpip配布packageを構築したわけではありません。リンク非対応のcheckoutでは旧パス互換機能を保証しません。`python -B tests/test_routing_migration.py` は新配置・旧互換・制約と小規模計算を検証します。

## 構造移行 第2段階

02のqualification schedule/decoderは新しい `src/kmd_quantitative/quantum/` へ直接接続する。`builder.py` はCandidate C PUBOの公開API、`qualification_builder.py` は従来QUBO・scheduleであり混同しない。PUBOの数式本体はhashを固定した従来science.py内に残り、全量workerは移行していない。`from kmd_quantitative.quantum import builder, decoder, qualification_builder` は `PYTHONPATH=src` で利用できる。

`python -B tests/test_quantum_migration.py` は6テスト。旧リンクを配布しない場合の新入口のみの検証は `python -B tests/test_quantum_migration.py QuantumCoreTests`。旧互換リンク4件を省略/通常テキスト化した一時Git取得状態でもNotebook6冊は成功したが、旧パスimportは失敗する。元の05_srcツリー全体が不要という意味ではない（science/Protocol/Battery/DC等を引き続き使用）。公開許諾は未確定。

## Phase 3：02の正式API接続

[Quantum API](../docs/quantitative/QUANTUM_API_AND_FROZEN_PROTOCOL.md)の `formal.evaluate_final_counts` を使用します。qualification decoderとの比較も保持します。17依存のhashを検査し、移行済み旧4リンクを使いません。正式science実ファイルは必要です。教材回路は正式QPYと正規化・角度・shots等が異なり、既定0/64を取得成功とは扱いません。

## Phase 4：保存軌跡とControlled-DCの接続

[Simulation / Trajectory API](../docs/quantitative/SIMULATION_AND_TRAJECTORY_API.md)に、正式CSV読込み、単位、時刻境界、SUMO外部依存を記載しました。`src/kmd_quantitative/simulation/trajectory_io.py` は保存軌跡の時刻・速度をそのまま返します。Notebook03の入力を接続し、`python -B tests/test_simulation_api.py` で小規模検証できます。SUMO全量再実行は行わず、生成worker・凍結sourceは原位置で保持しています。

## Phase 5：Battery / Energy API

[質量・Controlled-DCの正式入口](../docs/quantitative/BATTERY_AND_ENERGY_API.md)を追加しました。`battery.mass` は元計算文、`battery.scenarios` は既存freeze、`energy.controlled_dc` は元DC関数へ接続します。Notebook03はSimulation→Battery/Energyを利用します。`python -B tests/test_battery_energy_api.py` で数値回帰を確認できます。18 kWhは残量会計に使いますが、SOC・充電モデルではありません。科学sourceとfreezeは維持し、全量SUMO移植・公開許諾は未完了です。

## Phase 6：04・05の保存結果読込み

04はMethod×Battery/R0/R1、05は古典6規模の保存表を [Analysis API](../docs/quantitative/ANALYSIS_API_AND_FROZEN_RESULTS.md) 経由で読みます。表示や条件選択は従来と同じです。`python -B tests/test_analysis_api.py`（rootで実行）でhash・母数・単位・除外条件を検査できます。必要な小規模保存表は追跡候補に追加し、未取得Quantum経路は補完しません。

## Phase 7：設定・入力・結果の参照

[入力設定](../configs/examples/NOTEBOOK_INPUTS.json)・[合成fixture](../data/README.md)・[保存結果Index](../results/README.md)を整備しました。正式設定・freezeは原位置で保持し、小規模合成fixtureだけをバイト一致コピーで配置しています。Notebook01/02/03は設定例から入力を取得し、04/05は既存Analysis APIを継続利用します。`python -B tests/test_distribution_layout.py` と `python -B notebooks/test_notebooks.py` をrootで実行できます。配布技術候補と公開許諾は別で、権利確認・独立永続保存・全量SUMO再現は未完了です。

## 今回のライセンス適用

TAKUMA SANOが公開・適用権限を持つ自作コード・Notebookの自作部分にはApache-2.0を適用します。[READMEの適用範囲](../README.md#利用条件ライセンスの適用範囲)を参照してください。保存出力の研究結果、共同/第三者の権利、外部データの許諾を含めた一括承認ではありません。
