# 修正と再検証

- `review_recovery_before_missing_control.py`／`KNOWN37_RAW_NATIVE_DISTANCE_CHECKS.before.csv` を保存し、HOLD1行を明示して134区間の分母を復帰。`review_recovery.diff`、`control_ledger.diff` が修正差分。
- `RECOVERY_REVIEW.log` と `FINAL_REVIEW.log` が修正後再検証。既存科学データの変更なし。
- 初回経路回収の効率問題は `ROUTE_RECOVERY_ATTEMPT01.log` を保持。キャッシュ修正前code完全snapshotは未保存。
