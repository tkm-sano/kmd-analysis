# 共通条件 v1.1 の再検証

リポジトリルートから実行する。既存出力ディレクトリを指定しない。

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src \
  /home/takuma/.cache/kmd-analysis/venvs/vehicle-day-v1/bin/python -m pytest \
  tests/toc_common tests/toc_cg tests/toc_vehicle_day tests/toc_search_improvement \
  tests/test_toc_contracts.py -q -p no:cacheprovider

OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src \
  /usr/bin/time -v /home/takuma/.cache/kmd-analysis/venvs/vehicle-day-v1/bin/python \
  scripts/audit_toc_common.py --output /tmp/common-v1-1-new-audit
```

現行設定はcommon_conditions_v1_1.json、条件版AD-common-20261111-v1.1。
旧common_conditions_v1.jsonはv1.0履歴として保持し、現行loaderでは拒否する。
旧入力・計画の版だけを変更して使い回さず、新規入力を作って検証する。

テストは共通72件＋既存ToC/D64件、計136件。需要の再生成を呼ぶ旧
tests/test_toc_frozen_demand.pyは実行対象外。新テストは既存8ファイルの
読込・hashと一時コピーへの破損試験だけを行う。

audit/は新版で新しく保存した人工witnessと実データ読取監査であり、
過去の実験結果を更新しない。4〜6/20地点の人工検証はA〜D性能比較ではない。
S1〜S3の最適化、本比較、需要生成、公開OSRM要求、commit/pushは実行しない。

変更前原文はSOURCE_BEFORE/、初期状態はGIT_STATUS_BEFORE.txtと
PRESERVATION_BEFORE.json、終了時の保全検査はPRESERVATION_AFTER.json。
変更した10ファイル以外の既存ファイルが同一であること、旧設定・
旧実験/検証出力・アルゴリズム本体・凍結需要8ファイルの保全を確認する。
