# 佐川急便A相対値監査：実装前計画

2026-11-12。最新ユーザー指示を採用判断の最優先とする。

- 読取：README、現行共通条件v1.1、A関連文書、研究計画監査記録、指定一次資料3件。
- 作成：A_SAGAWA_RELATIVE_VALUES.md/.json/.csv、A_SAGAWA_EVIDENCE_AUDIT.md、A_SAGAWA_COMPARISON_DESIGN.md、A_SAGAWA_FINAL_DECISION.md。
- 既存A文書に新決定への短い優先参照を付す場合は、元本文を保全し変更前コピーを保存する。旧参照値・評価台帳は履歴として変更しない。
- 保全：共通設定、凍結需要8ファイル、src/scripts/tests、研究計画本体、README、旧実験結果。大規模実験・事業者連絡・commit/pushを行わない。
- 指定原画像、PDF、本文をGETで取得しURL・取得日時・SHA256を保存。画像のラベル・軸・比較基準を点検し、独立OCRまたは別表現・資料による照合を試す。
- 比率はbefore>0とafter、または明示比率がある場合だけ算出。不足はnull。差分だけから比率を捏造しない。Wは積込ready/startとの一致を必須とする。
- DecimalとFractionによる別計算、分母欠損/0、欠測と0の区別、別実験結合禁止、リンク・hash・機械可読値/文書の一致を検査する。
- 終了時に既存全対象ファイルhash・HEAD・git diffを確認し、意図したA文書追記以外の変更がないことを記録する。

## 追加指示による変更

最新指示：Aは佐川急便のLoogia導入前の人手計画。改善後や改善率はA性能値に採用しない。相対値確定の工程を、改善前の絶対値・実経路・作業記録と再現に必要な情報の監査へ変更。新成果物はA_SAGAWA_MANUAL_BASELINE.md/.json/.csv、A_SAGAWA_EVIDENCE_AUDIT.md、A_SAGAWA_COMPARISON_DESIGN.md、A_SAGAWA_FINAL_DECISION.md。差分は非採用の根拠としてのみ保存。問い合わせ禁止を維持する。
