# Minimal EVRP classical充電検証

凍結結果は [20260926_v2 report](../../../reproducibility/outputs/traffic_simulation/r24_minimal_evrp_charging_validation/20260926_v2/MINIMAL_EVRP_CHARGING_VALIDATION_REPORT.md) である。モデルはN002 WIDEの制御初期SOC・10kWで検証済み。実車の充電性能authorityは未解決であり、10kWをS0へ転用しない。

`charging.py`は独立EV sidecarと全構造Exact/reference、`charging_milp.py`はarc-flow HiGHS、`charging_independent.py`はDecimal再計算と生solver証明照合である。既存replay.py/independent.pyの無充電回帰処理は変更しない。

保存結果の再監査（solver実行なし）:

```bash
PYTHONPATH=05_src/traffic_simulation .conda/bin/python reproducibility/outputs/traffic_simulation/r24_minimal_evrp_charging_validation/20260926_v2/verify_freeze.py
EVRP_RESULT_DIR=reproducibility/outputs/traffic_simulation/r24_minimal_evrp_charging_validation/20260926_v2 PYTHONPATH=05_src/traffic_simulation .conda/bin/python -m unittest r24_minimal_evrp.test_replay r24_minimal_evrp.test_charging -v
```

runner `run_charging_validation`はclassical scientific executionを行うため新しい実行承認・新規gate directoryが必要である。凍結済み結果への再実行を拒否する。今回の2case Exact・3stage MILP以降のscenarioは実行していない。

初回開発serialization例外は出力v1に保持し、数学・パラメータを変更せず新規保存処理を修正した。既存source defectの修復や不利な科学結果の置換ではない。
