# 大田区v15道路属性例外規則の全件検証

> **実行日**: 2026-07-30
> **対象**: v15 Resolver停止記録の規則・データ例外
> **判定**: 排他的分類に合格、属性値の解決は保留

## 入力と実装

| 対象 | SHA-256 |
|---|---|
| v15例外キュー | `89a0edc656244619dd81e2dc53ddd1b6c6d0abc2650dab7604de110ff7cad858` |
| 例外決定表 | `ae30dcaa1a56eb4757c220da420d602ce2777456973da1678c700e92600cda9b` |
| 通常・異常・境界例 | `0a1ac6de76e3bbe22fc0b952055fcd67589a09a186ab2122bec1e3210adb965f` |
| 実装と独立した正解 | `8f5f45bb4fb65dd2c23a750d195c40e420f6296e1dd3720f45b827bd25b9bfcd` |
| 例外分類器 | `6a43f8f7d567e66a23463c80d40dfffd4f9d2dd5dd97e459e06eff0c7e8d7417` |
| 分類器試験 | `ddbea6ce8226a9b438a6847092602a8fdb896b570e5677bcfc7d5cfcb41f7678` |

対象307行は、`decision=stop`、`formal_blocker=true`であり、値状態が
`unresolved`、`valid_but_unsupported`、`conflict`のいずれかである行として
機械可読に定義した。単に「missing以外」とする暗黙条件は使用していない。

## 実行方法

```bash
PYTHONPATH=05_src python -m \
  traffic_simulation.network.classify_resolver_exceptions
```

自動試験は次のコマンドで実行する。

```bash
pytest -q \
  05_src/traffic_simulation/validation/test_resolver_exception_classifier.py \
  05_src/traffic_simulation/validation/test_resolver_exception_decision_table.py
```

## 結果

| 項目 | 件数 |
|---|---:|
| 選択行 | 307 |
| 分類済み | 307 |
| 一致なし | 0 |
| 複数一致 | 0 |
| ちょうど一つの規則へ一致 | 307 |

属性別では、一方通行1行、車線20行、最高速度22行、通行可能車種264行である。
20規則すべてについて通常例を固定し、未知の導出方法と壊れたタグJSONが0一致で
停止すること、重複規則を注入した場合に2一致で停止することを確認した。

### 検証一式の再実行

2026年7月30日に、固定`analysis`コンテナで検証一式を再実行した。従来の
331件構成では`331 passed`であり、不合格は0件であった。今回追加した例外分類器の
4件を含む構成では`335 passed`であり、不合格は0件であった。

| 検証範囲 | 合格 | 不合格 | 合計 |
|---|---:|---:|---:|
| 従来の検証一式 | 331 | 0 | 331 |
| 例外分類器の試験を含む現在の検証一式 | 335 | 0 | 335 |

331件構成は、今回追加した4件の試験ファイルだけを除外して再現した。

```bash
docker compose run --rm analysis \
  pytest -q 05_src/traffic_simulation/validation \
  --ignore=05_src/traffic_simulation/validation/test_resolver_exception_classifier.py
```

現在の335件構成は次のコマンドで再実行する。

```bash
docker compose run --rm analysis \
  pytest -q 05_src/traffic_simulation/validation
```

以前確認された`330/331`という結果は、現在の固定入力、実装およびDocker環境では
再現しなかった。失敗内容を推測してコードを変更せず、同じ331件構成を明示的に
再実行して全件合格を確認した。以後は、テスト総数だけでなく、対象コミット、
入力SHA-256、実行環境および失敗テスト名を併せて記録する。

## 解釈

この合格は分類の完全性と排他性を示す。307行の速度、車線数、通行可能車種が
決定したことは示さない。日本の法令適用日、東京の個別規制、条件付きタグの評価文脈、
許可状態、方向依存属性が不足する行は停止を維持する。このため、正式用の正規化
OSMおよびSUMO道路網の公開条件はまだ満たしていない。
