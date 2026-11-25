# 公開更新の監査記録

対象は大田区ToC配送の公開再現パッケージです。現行入口のソースを作業ツリーから取得し、import、動的カーネル読込み、設定と記録の参照先を分離ツリーで照合しました。研究アルゴリズム、運行条件、凍結本文は編集していません。

## 検証範囲

- 既存のLinux・Python 3.12.11環境で回帰161件が通過しました。検査対象は、人工fixtureのgrouped-v2受付・再開、記述統計、FCFS、勤務・休憩、D局所候補、履歴D/W契約です。SWIGとHiGHSの警告は5件です。
- 履歴の全ファイル保全を検査する2件と、非同梱の正式ODを必要とするS1保存計画の1件は対象外です。旧D3登録を参照する実行・再開試験も公開対象外です。旧登録の絶対パス、実行環境およびソースの一致を要求します。
- 主要12入口のimportと `--help`、固定需要の1000/2000/4000地点の読込み、動的な量子カーネル2件のロードを確認しました。研究仕様1〜7、FCFS_v1、記述統計v1の凍結ハッシュ照合は通過しました。
- 公開試行コンテキストでseed表108,438行を再構成し保存済みCSVのSHA-256と一致しました。公開図表は既存予備の要約です。公開環境からの全量OD生成、正式実験、保存した全計画からの再作図は未実施です。

## 公開の判断

新規公開のデータは、経路や地点を含まない予備集計・著者の図表、公開用に射影した登録ID・seed・ハッシュ、入力来歴に限定しました。原入力の未許諾資料、行動計画、測定ビット列と探索ログ、実験生データ、キャッシュ、第三者依存のバイナリ、認証情報は追加対象外です。古い構成の複製や運用ログは保全側に残します。既存公開資産の削除はありません。既存のライセンスと出典表記を保持しています。過去の監査文書にある記録先の一部は論証の出典で、公開cloneの実行依存ではありません。

## 作業ツリーの既存34変更

| ファイル | 公開判断 |
|---|---|
| `AGENTS.md` | 保留。作業指示と履歴の追補は公開再現に不要。既存公開版を維持。 |
| `BASELINE_A_AUDIT.md` | 採用。研究仕様・歴史的結果の参照先と版境界を整備。 |
| `BASELINE_A_METHOD.md` | 採用。研究仕様・歴史的結果の参照先と版境界を整備。 |
| `README.md` | 採用。最新版・予備・HOLDを冒頭で示し、旧本文を保持。 |
| `configs/toc_delivery/dw_policy_20261117_v1.json` | 採用。旧平均荷待ち経路の設定と互換のため保全。 |
| `configs/toc_delivery/study.json` | 採用。11月19日履歴のロードスキーマと対応。 |
| `docs/research/A_TO_D_COMMON_INTERFACE.md` | 採用。研究仕様・歴史的結果の参照先と版境界を整備。 |
| `docs/research/A_TO_D_COMPARISON.md` | 採用。研究仕様・歴史的結果の参照先と版境界を整備。 |
| `docs/research/BASELINE_A_DESIGN.md` | 採用。研究仕様・歴史的結果の参照先と版境界を整備。 |
| `docs/research/CPU_PARALLEL_EXECUTION.md` | 採用。研究仕様・歴史的結果の参照先と版境界を整備。 |
| `docs/research/DWT_7_FIGURES_SPEC.md` | 採用。研究仕様・歴史的結果の参照先と版境界を整備。 |
| `docs/research/DWT_EXPERIMENT_DESIGN.md` | 採用。研究仕様・歴史的結果の参照先と版境界を整備。 |
| `docs/research/DWT_MULTI_OBJECTIVE_FORMULATION.md` | 採用。研究仕様・歴史的結果の参照先と版境界を整備。 |
| `docs/research/DWT_PILOT_DESIGN.md` | 採用。研究仕様・歴史的結果の参照先と版境界を整備。 |
| `docs/research/DWT_SAMPLE_SIZE_PIPELINE.md` | 採用。研究仕様・歴史的結果の参照先と版境界を整備。 |
| `docs/research/DWT_STATISTICAL_PROTOCOL.md` | 採用。研究仕様・歴史的結果の参照先と版境界を整備。 |
| `docs/research/DW_RESEARCH_POLICY.md` | 採用。研究仕様・歴史的結果の参照先と版境界を整備。 |
| `docs/research/REPRODUCE.md` | 採用。研究仕様・歴史的結果の参照先と版境界を整備。 |
| `docs/research/TOC_DELIVERY_SPEC.md` | 採用。研究仕様・歴史的結果の参照先と版境界を整備。 |
| `docs/research/toc_delivery_common/COMMON_CONDITIONS_V1.md` | 採用。研究仕様・歴史的結果の参照先と版境界を整備。 |
| `docs/research/toc_delivery_common/COMMON_INTERFACE_SPEC.md` | 採用。研究仕様・歴史的結果の参照先と版境界を整備。 |
| `scripts/analyze_dw.py` | 採用。共通FCFS・記述統計への振分けと明示履歴。 |
| `scripts/audit_dw_policy.py` | 採用。互換の履歴設定に対する照合。 |
| `scripts/run_a_area_program.py` | 採用。旧A計画入口を明示履歴として実行するため。 |
| `scripts/run_a_area_study.py` | 採用。旧A計画入口を明示履歴として実行するため。 |
| `scripts/run_a_rule_baseline.py` | 採用。旧A計画入口を明示履歴として実行するため。 |
| `scripts/run_a_rule_v1.py` | 採用。旧A計画入口を明示履歴として実行するため。 |
| `scripts/run_baseline_a.py` | 採用。旧A計画入口を明示履歴として実行するため。 |
| `src/kmd_toc/contracts.py` | 採用。履歴studyのスキーマと版を検査。 |
| `src/kmd_toc/dw.py` | 採用。旧評価の再現用実装と履歴文言。 |
| `src/kmd_toc/termination_v1/master.py` | 採用。共有FCFSの整数完成に接続。 |
| `src/kmd_toc/termination_v1/methods.py` | 採用。現行FCFSの条件を既存方式に渡す。 |
| `src/kmd_toc/termination_v1/solvers.py` | 採用。FCFS構成で正しい完成経路を使用。 |
| `tests/test_dw_policy.py` | 採用。履歴設定の整合性回帰。 |

[公開ファイル一覧](../../results/toc_grouped_v2_20261124/publication_files.csv)に追加・更新の全パスと理由を記録しています。[公開再現ガイド](TOC_PUBLIC_REPRODUCTION.md)に実行時の境界と未検証事項を記録しています。
