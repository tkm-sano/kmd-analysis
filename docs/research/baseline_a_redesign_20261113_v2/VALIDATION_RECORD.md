# 検証記録

## 単体・回帰検証

既存の`/home/takuma/.cache/kmd-analysis/venvs/ad-pipeline-v1/bin/python`環境を使用した。追加インストールは行っていない。

```bash
PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 \
  /home/takuma/.cache/kmd-analysis/venvs/ad-pipeline-v1/bin/python -B \
  -m pytest -q tests/toc_baseline_a tests/toc_common
```

結果は143 passed、90.90秒である。その後の出力契約・独立型検査・正規化照合の修正に対して新規テストを再実行し、19 passed、15.48秒である。最終の全規模動作確認とテストは同時実行していない。テストの人工ODと本研究のRoute ODは区別する。

新規19テストは、手計算可能な2地点の3km・arcごとceil・120秒作業の検算、120地点1台2便の連結、配送漏れ・重複・容量・便数・早発・終業超過・負待ち・距離・作業・デポ破損、バース重複、入力/OD不達拒否、失敗保存、既存出力保全、計時に第二検証が含まれること、二検証不一致時のnull、timeout、正規化参照の境界を確認したものである。

## 予備CLIの失敗を含む記録

`output/toc_delivery/a_provisional_program_20261113_v2_check01`は準備段階で`threadpoolctl`の不足を記録した。補助依存を不要にし、import前のnative thread環境設定と1コアaffinityを用いるよう修正した。追加パッケージを既存環境へ導入しなかった。このフォルダの値は完成版の指標へ採用しない。

`..._check02`は最終レビューで出力完備性と設定コピー位置の改善が必要と分かり中断した。check01/02は消去せず、INTERRUPTED.jsonを残す。中断時に既に実行された工程・失敗があっても、それを成功したAのD/W/Tや正式反復へ加算しない。

最終確認は`..._check03`を正本とする。登録された2回×S1〜S3を逐次実行し、コード固定性、子プロセスexit、成果物の存在・hashと計画バイト同一性を確認する。結果は[最終報告](BASELINE_A_FINAL_REPORT.md)および出力SUMMARYに記録する。準備・出力・失敗も親プロセスの記録に含めるが、検証済み計画取得のTとは区別する。
