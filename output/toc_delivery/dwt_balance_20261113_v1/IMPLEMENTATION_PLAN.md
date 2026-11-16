# DWT実装前計画 2026-11-13

正本をREADME、docs/research/A_TO_D_PIPELINE_FINAL_REPORT.md、A_TO_D_COMPARISON.csv、INDEPENDENT_VALIDATION.md、REPRODUCE.md、共通v1.1、Route v2の実入力、src/kmd_toc/pipeline/{classical,completion,hybrid,execution}.pyと確認した。親/root AGENTS.mdなし。既存変更README/.gitignoreを保全。

## 変更範囲・順序
1. src/kmd_toc/dwt/に外部設定、予算制御、実行器、既存生成器/完成器接続、評価/非支配解析、標準出力、独立検査を追加。旧アルゴリズム・OD・設定・結果は変更しない。
2. configs/toc_delivery/dwt_balance_v1.jsonを予備実験用に固定。B/C/Dは同入力・同W上限・全工程T境界。時間予算は実測Tと別。Aは事前にA2/offset0を単一規則として採用（公開実務の再現ではない）。
3. tests/toc_dwtで単体・人工トレードオフ・制約違反・予算超過・標準出力を検証。
4. ROAD_N6/N20で予備確認後、限定S1行列設定とseedをハッシュ登録してから実行。S1旧保存結果は別再計算し、必要なら旧実装再実行を新規出力に分離。
5. 限定S1をW=0.75*422.45と422.45、T予算30/90秒、B/C/D各1試行で実行。これは本番統計実験ではなく予備の予算反応確認。D古典のみ対照を同条件で追加し候補・完成器寄与を分離。
6. 全可行結果をplan.json/routes.geojson/stops.geojson/berth_events.csv/metrics.json/manifest.json/validation.jsonへ出力。実道路形状は保存Route nodeと同版PBF索引から復元。未保存形状を直線で代替しない。export失敗は成功扱いしない。
7. 全試行CSV/JSON、非支配集合、支配関係、重み/参照感度、予算/epsilon集計、図、4報告/再現手順を生成。別実装からraw OD/時刻/支配関係を照合。

## 条件・完了判定
T=入力読込前→共通検査と第二独立再計算終了。GeoJSON・図出力は別時間。native solverは残時間上限、親watchdogは全工程を監視。時間超過は結果除外し失敗も保存。Tを計画内部目的へ加えない。Dは有限候補最適化で全VRP最適性を主張しない。refsはS1の旧A2 D551.1398/W422.45と仮定Tref60秒、手法共通・事前固定。S2/S3 refsは未確定でnull。重みは等分、距離/待機/時間に0.6/0.2/0.2の設定例。

## 依存・保全
共通OD→生成→共通完成器→検証→T確定→標準出力→解析。環境は既存ad-pipeline-v1を再利用。有料サービス/連絡/commit/pushなし。S2/S3は入力監査と適用可能CLIまで、全条件の本実験は未実行と記録。新コード/新テスト/新設定/新文書/新outputだけ追加。開始hashはPRESERVATION_BEFORE.json。GOは数値・独立検証・標準出力が実際に揃う対象に限定。
