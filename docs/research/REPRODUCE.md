# 2026-11-21追加：正式な記述統計解析

[統計Freeze](statistical_scope_20261121_v1/FREEZE_SPEC.md)に従う現在の集計は次を使う。

```bash
python -B scripts/analyze_descriptive_v1.py --registration REGISTRATION.json --output NEW_OUTPUT
# 同じ処理への案内入口
python -B scripts/analyze_dw.py --statistics-registration REGISTRATION.json --output NEW_OUTPUT
```

REGISTRATIONには入力・運行版・比較条件・外側試行とその証跡、独立性・対応の登録根拠を指定する。保存済み計画を読み取り、記述統計・SD図表と内部MCSEを新規出力へ保存する。既存出力は上書きしない。Jの採択・最適化・量子計算は行わない。詳細は[新しい再現手順](statistical_scope_20261121_v1/REPORT.md)。通常の `--input --plan` FCFS評価と `--historical-reproduction` の履歴経路は維持する。

以下は直前版の再現案内であり、旧検定・図表を新しい正式統計解析へ流用しない。

---

# 現行FCFS評価と履歴再現の区別

2026-11-20更新。この文書は現行案内であり、研究仕様の正本ではありません。[研究仕様1〜7（凍結v1）](../frozen/配送計画最適化_評価指標と実験条件_1-7.md)と[追加運用仕様FCFS_v1](FCFS_OPERATING_POLICY_V1.md)を参照します。数式・数値・未決定事項をこの案内から新たに決定しません。更新前の案内（保全資料）は保全しています。


## 凍結の確認

標準ライブラリだけで実行できる読み取り検証。PASSは本文の完全性であり、本実験開始や全実装適合のPASSではない。

```bash
python -B scripts/verify_research_freeze_20261120.py
python -B scripts/verify_fcfs_policy_v1.py
```

## 保存計画のFCFS評価

プロジェクトの依存環境を有効にし、大文字の入力・計画・出力名を実際のパスへ置き換える。

```bash
PYTHONPATH=src python -B scripts/analyze_dw.py \
  --input COMMON_INPUT \
  --plan B_PLAN.json --plan C_PLAN.json --plan D_PLAN.json \
  --output NEW_FCFS_OUTPUT
```

`analyze_dw.py`は`evaluate_fcfs_v1.py`へ接続する。入力と別の未使用出力先が必要で、既存出力を上書きしない。同じProblem/ODに対応する計画を与え、FCFS不適合や旧新混在は拒否する。最適化・需要生成・量子処理は起動しない。現行CLIに旧版の`--model`・`--events`を付けない。Tが未記録なら補完しない。

元計画を自動修復しない。固定経路を明示的にFCFSで組み直す場合は、新Planと別出力へ保存し、旧結果や新たな最適化性能試験と区別する。

## 旧版と検証記録

旧予備解析は`analyze_dw.py --historical-reproduction`。旧`run_dwt.py`等も対応する明示的な履歴フラグを要求する。旧イベントAPI・平均荷待ち評価は旧版の診断として分離し、現行総積込Wへラベルだけ付け替えない。

過去の登録/source sealを現在のhashへ置換して再開しない。履歴再現には保存snapshotと別出力を用い、新規登録は新IDにする。本実験の登録・実行は未承認であり、これらの案内から開始しない。

[FCFS検証報告](../../reports/FCFS_V1_IMPLEMENTATION_REPORT_20261120.md)、使用環境（保存済み証跡）、関連テスト結果（保存済み証跡）を参照。そこに記録された88件と関連回帰30件は重複を含み、独立需要や本実験試行数へ加算しない。

FCFS部分PASS、本実験全体HOLD。今回の案内更新では新規実験・再最適化を行わない。
