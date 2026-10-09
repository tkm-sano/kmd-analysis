# Battery / Energy API

## 1. Path 2の対象

容量20 kWhを固定し、パック比エネルギー180/220/250 Wh/kgによるパック質量の変化を車両質量へ反映する。容量増加や量子材料計算を扱わない。同一の保存走行軌跡に異なる質量条件を与える感度評価であり、実電池性能の達成・実車検証ではない。

## 2. Battery入力・出力

[mass.py](../../src/kmd_quantitative/battery/mass.py) は `official_mass_stages()` と `mass_at_specific_energy(selected)` を提供する。前者は元stage loopの全mass record、後者は既存Notebookと同じCUSTOM感度条件。入力selectedはWh/kg、計算容量は20 kWh固定。

[scenarios.py](../../src/kmd_quantitative/battery/scenarios.py) の `load_model()` はhash固定の [モデルfreeze](../../01_research_design/methodology/CONTROLLED_MASS_TO_DC_MODEL_FREEZE.json) を新しいdictとして読む。`stage_inputs()` はEnergyに渡すB0/B1/B2の凍結入力。呼出しごとに読み直すため返却dictの編集はfreezeを書き換えない。編集した条件は正式条件ではない。

## 3. 比エネルギーとパック質量

原sourceの関係は `m_pack = 20000 / e_pack`。B0/B1/B2のパック質量は約111.111111 / 90.909091 / 80 kg。新APIへ数式をコピーせず、review_pack_specific_energy.pyのcalcとstage loop、またはcustom用の元3文をASTとして呼ぶ。レビューsourceのmain全体・文献処理・表書込みは起動しない。stage選定用の相関式を今回変更・更新していない。

## 4. 車両質量

B0車両基準1100 kgからB0パック質量を差し引いた共通残余に各パック質量を加える。車両質量は1100 / 1079.79797979798 / 1068.888888888889 kg。Energyに渡すrunning_mass_kgは共通運転者55 kgを含む1155 / 1134.79797979798 / 1123.888888888889 kg。積載・追加設備は0 kg。パック軽量化の結果として車両質量が変わる。

## 5. Controlled-DC入力

[controlled_dc.py](../../src/kmd_quantitative/energy/controlled_dc.py) の `evaluate(t,v,model,pressure,stage)` は元run_full_controlled_dc.pyの関数そのものを公開する。tは秒、vはm/s、1秒間隔の同長numpy配列、pressureは既存Crr条件p_bar、stageはrunning_mass_kg等の凍結dict。配列順を変更しない。

CSV入力はSimulation API `read_dc_input` で検査する。Energy低水準APIのassert/例外は元関数と同一で、一般的入力validatorではない。一部の異長配列はNumPy broadcastで計算され得るため、直接呼ぶ側も契約を守る。Simulationの等長/有限値/1秒guardを通す。`python -O` は使わない。欠損補充・端点補間・並べ替えはしない。

## 6. 出力と18 kWh

返り値は `(out, arrays)`。outの主項目はtraction_DC_Wh/net_DC_Wh/cumulative_DC_Wh、observed_interval_count/observed_distance_m、成分Wh、Wh_per_observed_km、initial/minimum/terminal_stock_Wh、stock_integrity、boundary等。arraysはroll/translational/rotational/aero/wheel/dcの区間Wh配列（N−1要素）。負仕事は符号付き成分と非負の負側magnitudeを区別する。

**18 kWhは実際の残量会計に使われる。** 元核は `18000 - np.cumsum(dc)` を計算し、負残量をSTOCK_INTEGRITY_FAILとして記録する。18000は核内固定値であり、返却modelのstock_accountingだけを編集して可変SOCモデルにできるわけではない。残量で走行を打ち切らず、clampせず、充電やSOC依存効率を計算しない。

## 7. 物理モデル・評価境界

元freeze/実装では右端速度×dtで区間距離、隣接速度二乗差で並進・回転運動エネルギーを扱う（加速度配列は返さない）。転がり抵抗係数は `0.005+(0.01+0.0095*(3.6*v/100)^2)/p_bar`。p_bar=4.5/2.6はCrrの上下境界で、実際の圧力変更実験や信頼区間ではない。

g=9.80665 m/s²、rho=1.2041 kg/m³、CdA=1.175 m²、回転等価質量61 kgは段階共通。roll+translation+rotation+aeroの仕事を3600でJ→Whへ変換し、合計wheelの正側を一定効率0.90で除してDC電力量とする。成分ごとに正側を先に切り取る処理ではない。平坦、回生なし、補機対象外、turn loss対象外。負wheel仕事を充電として扱わない。

内部会計のnearは相対1e-11・絶対1e-7 Wh。新APIの数値回帰は元関数との完全一致。`scalar_check` も元関数を公開する。

## 8. Simulation接続・実行例

既存Notebook環境でrepo rootから `PYTHONPATH=src python -B`：

```python
from pathlib import Path
from kmd_quantitative.simulation.trajectory_io import read_dc_input
from kmd_quantitative.battery.scenarios import load_model, stage_inputs
from kmd_quantitative.energy.controlled_dc import evaluate

t, speed = read_dc_input(Path('notebooks/fixtures/speed.csv'))
model = load_model()
for stage in stage_inputs():
    out, arrays = evaluate(t, speed, model, 4.5, stage)
    print(stage['stage_id'], out['net_DC_Wh'])
```

このCSVは人工4標本で、SUMOの科学結果ではない。正式保存軌跡を使う場合はmanifestと圧縮ファイルhashをread_dc_inputへ渡す。実軌跡1,319標本も今回6条件の回帰に使用したが、配布fixtureに複製していない。

確認済みコマンド：`python -B tests/test_battery_energy_api.py`、`python -B notebooks/test_notebooks.py`。numpy/pandas等はnotebooks/requirements.txtの既存環境を利用。新規pip構築やWindowsは未検証。

## 9. Method×Battery

Path 1は経路ごとの固定軌跡、Path 2は同一軌跡への質量条件変更。既存Method×Batteryはこの組合せを保存済みの母集団・単位・比較規則で集計する。APIは新しい効果指標や母集団を定義しない。Notebook04は凍結R0/R1と共通64対応ブロック等の保存結果、05は古典6規模の保存結果を読む。

## 10. 正式sourceとの関係

質量：review_pack_specific_energy.pyの元計算文。正式Energyシナリオ：CONTROLLED_MASS_TO_DC_MODEL_FREEZE.json。Energy核：run_full_controlled_dc.pyのevaluate/scalar_check/near。新APIはhash確認後に接続し、sourceを変更/移動しない。Energy sourceは定義と定数だけをimportし、main/preflight/ファイル出力を呼ばない。

旧apply_r0_method_battery.pyはR1のapply_r1_method_battery.pyがASTで再利用し、R0 commonがそのadapterへ接続する。旧R0という名前でも現役依存。削除しない。質量とEnergyのNotebook側抽出処理は新API呼出しへ置換し、二重管理を避けた。

## 11. 配布と復元条件

新APIだけでなく元質量source、DC source、freeze、Simulation用旧R0sourceも取得する必要がある。技術候補は372パス。小規模実行にSUMO/道路networkは不要。全量生成用の専用router/native fork/network/Hayateパスは別依存で未移植。旧互換リンクなしの一時配置で検証したが、公開権利は未確定でGitHubへ反映していない。

## 12. 評価しないもの

保存された最初〜最後の標本間のDC牽引電力量だけを評価する。終端観測外、補機、充電器入力/損失、計算・通信、設備・製造、物流システム全体の消費を含まない。nullのturn/auxiliary/terminal gapを物理的0と解釈しない。配送未充足による消費減を省エネ成果とせず、実業務の需要充足や実電池性能を実証したとは扱わない。
