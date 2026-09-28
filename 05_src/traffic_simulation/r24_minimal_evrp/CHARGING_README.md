<a id="minimal-evrp-classical充電検証"></a>

# 最小構成の電気自動車配送経路問題 古典計算充電検証

凍結結果は [20260926_v2 report](../../../reproducibility/outputs/traffic_simulation/r24_minimal_evrp_charging_validation/20260926_v2/MINIMAL_EVRP_CHARGING_VALIDATION_REPORT.md) である。モデルはN002 WIDEの制御初期充電率・10kWで検証済み。実車の充電性能正本は未解決であり、10kWを第0段階へ転用しない。

`charging.py`は独立電気自動車 sidecarと全構造Exact/reference、`charging_milp.py`は区間-流れ HiGHS、`charging_independent.py`はDecimal再計算と生求解器証明照合である。既存replay.py/independent.pyの無充電回帰処理は変更しない。

保存結果の再監査（求解器実行なし）:

```bash
PYTHONPATH=05_src/traffic_simulation .conda/bin/python reproducibility/outputs/traffic_simulation/r24_minimal_evrp_charging_validation/20260926_v2/verify_freeze.py
EVRP_RESULT_DIR=reproducibility/outputs/traffic_simulation/r24_minimal_evrp_charging_validation/20260926_v2 PYTHONPATH=05_src/traffic_simulation .conda/bin/python -m unittest r24_minimal_evrp.test_replay r24_minimal_evrp.test_charging -v
```

実行器 `run_charging_validation`は古典計算 scientific 実行を行うため新しい実行承認・新規判定基準 ディレクトリが必要である。凍結済み結果への再実行を拒否する。今回の2case 厳密・3stage 混合整数線形計画以降の想定条件は実行していない。

初回開発serialization例外は出力v1に保持し、数学・パラメータを変更せず新規保存処理を修正した。既存出典 defectの修復や不利な科学結果の置換ではない。
