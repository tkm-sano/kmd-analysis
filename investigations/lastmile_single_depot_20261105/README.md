# 単一拠点ラストマイル配送・調査成果物

2026-11-05。既存研究成果と分離した調査専用フォルダ。

1. [調査報告書](REPORT.md)：採用判断、一次資料、現行設定、比較設計、追加データ、予備計測。
2. [証拠台帳](evidence_ledger.csv)：37主張、1行1主張、URL・箇所・定義・留保・判定。
3. [パラメータ採用表](parameter_decisions.csv)：12項目。研究仮定を実測と区別。
4. [実験計画表](experiment_plan.csv)：18条件行。各行の60/300/900秒×10入力seed×5探索seedを予定。実行済みは合成予備計測のみ。
5. [修論・ポスター用記述案](SHORT_TEXT.md)：既存原稿へは未反映。
6. [Amazon再監査](AMAZON_REAUDIT.md)、[検索・未確認事項](SEARCH_AND_LIMITATIONS.md)。

`sources/manifest.json` は初回取得のHTTP成否を含み、403・404は取得済み本文ではない。`FILE_MANIFEST.csv` は最終ファイルのSHA256。`sources/transcript_excerpts.txt` はユーザー提供本文の抜粋で、原音声・完全txtではない。外部NPZは保全領域のパス・hashを `probes/local_input_audit.json` に記録。

計算環境は調査専用 `probes/venv/`。再作成はPython3.11でvenvを作り `probes/pip_freeze.txt` を参照する。主要コマンド（研究ルートから）：

```bash
.conda/bin/python investigations/lastmile_single_depot_20261105/probes/local_audit.py
.conda/bin/python investigations/lastmile_single_depot_20261105/probes/amazon_stats.py
investigations/lastmile_single_depot_20261105/probes/venv/bin/python investigations/lastmile_single_depot_20261105/probes/solver_probe.py --contract-only
```

`solver_probe.py` を引数なしで実行すると合成5規模を再測定し、同フォルダの予備計測結果を更新する。実行時間は環境に依存し一致保証はない。既存の科学入力・凍結結果を変更しない。`build_tables.py` は台帳・採用表・計画表を再生成する。

30台3000先は合成拡張試験として条件付き採用、実運用再現規模として保留。量子を含む全体比較と大田区全ODの複数台実験は未実行。

**追加調査：** [ヤマトと日本のAmazonの比較](japan_carrier_comparison/COMPARISON.md)。国内DSPの車両目安・一日2ルート条件、両社の計画業務を追記。企業の国内運用参照と米国公開データを分離した最新の判断はこちら。元の37主張台帳は履歴として保持し、追加18主張は別台帳。
