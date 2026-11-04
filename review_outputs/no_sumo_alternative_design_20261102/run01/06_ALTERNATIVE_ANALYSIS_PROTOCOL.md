# 推奨分析プロトコル NO_SUMO_ALTERNATIVE_V1

主分析は案2。新仕様は本レビュー内の `ANALYSIS_PROTOCOL.json` に保存し、旧FREEZE・D03/D10/D11・Controlled-DCを変更しない。今回は全件分析未実施。次回はこの仕様を確認した後、新領域へ実装する。

## 比較・分母・分析単位

|分析|比較・主指標|分母・単位・欠測|
|---|---|---|
|A1成功64|CC/QC/CQ/QQ、主PE定時率差、経路／出発／交互作用|64問題、36条件を別表。全4顧客需要。未取得14をこの機構比較へ混ぜない|
|A2運用78|量子優先政策対古典のみ政策、主PE定時率差|78問題×36政策。未取得14は古典切替で残す。各政策のpooled PE率を主、問題macro平均を副|
|B全460|各設定のsampled-best OD秒−同一入力classical initial、OD距離差を副|8設定×460×10。repを先に問題内で平均。改善率・取得率は対象入力全数と成功条件を併記|
|B厳密参照407|gap／完全最適値一致、mirror orbit gap別表|参照がある407入力のみ。53欠測を失敗や0gapにしない。raw取得失敗なら取得分母に残す|
|C固定速度|同じtrajectory・pressure・設計条件のLP−S mass/DC、δ相殺境界|460旧trajectory、2Crr、設計probeを保持。25,760行を独立標本にしない|

全系列は26親を含み、A/B親の元group対応は25需要group。Aは古典JSONのgroup_id、Bは同じ親への対応を検査済み。配送実態に対する独立抽出が証明されていないため、主結果は固定rosterの記述的・対応差とする。

10測定repは同じfitからの標本化変動。rep同番号でも異なる設定間で同一乱数とは仮定しない。個別shotを物理問題数へ加算しない。代表例の追加training seed99/100/101は補助、主cohort学習数を水増ししない。時間仮定T_QをCPU時間に読み替えない。

## 推定・区間

Aは政策ごとにΣ定時PE/Σ全PEと件数率、対応差を計算。QC−CC、CQ−CC、QQ−QC−CQ+CCを同じ64問題で報告し、採用政策の効果と分離する。出発／完了／余裕の分布と最初の遅延境界を併記。未知があるなら点率null、固定分母による下限・上限を出す。

Bは10repを各物理問題内で平均し、規模別の問題等重み平均差を主とする。全規模pooledは事前の78/…/70構成に依存する補助記述。最良seedだけを主値にしない。global exact一致は元有理数で判定し、シリアライズ差に対する照合許容と「最適一致」の定義を混ぜない。raw sampled-bestとinitialを併記し、incumbent維持minは別の政策表とする。

固定rosterの値に必須の信頼区間はない。仮想的な需要group母集団へ一般化する補助感度を行うなら、25groupを丸ごと10,000回、seed20261102で再標本化し95%percentile区間を使う。同じgroupに属する親・規模・rep・政策をまとめて複製する。需要分母も毎回再計算する。未知・欠測で定義不能なreplicateは記録し黙って削除しない。これは実世界の無作為標本や校正誤差を保証しない。

Cは同一速度条件内の決定論的差と上下Crrのenvelopeを主とする。Crr幅を信頼区間と呼ばない。旧trajectoryを親・需要groupへ確実に対応できた場合だけ同じcluster感度を使い、未対応ならtrajectory-level記述に留める。material/δ反復を標本数にしない。多数の政策や設定に対する事後的有意差探索はしない。検定が必要な別RQは比較・多重性処理を先に追記し、現設計の主結論にp値を必須としない。

## 感度と限界

Aの主境界は元ready/dueを固定した解析的出発限界。36政策のT_Q/L/Bは保持。補助OD一律倍率0.8/1.0/1.2を事前固定する場合は研究用stressとして別表にし、実地域の混雑分布とは呼ばない。期限を差が出るよう変更しない。時間帯依存、信号、停止失敗、DCは未評価。

Bは全460で計画指標を保持し、元edge回復有無・規模・親・設定・repによる分布を併記する。未回復を除外する必要のない指標に除外を適用しない。参照最適値407への制限とedge回復2,323候補への制限も別々に示す。

Cは固定担持／面積、既存利用率・電圧、Crr、δ=b付近の既存probeを用いる。未知部材の実測値・分布を新規に仮定しない。B-E2は今回は採用せず、必要となった場合だけmassと速度／加速仮定を別プロトコルで固定する。

## 実装順・入口・合否

1. **台帳・contract**：今回のA_INPUT_COVERAGE、B_PLAN_REFERENCES、B_PLAN_RECOVERY_LINKS、元NPZ、source SHAから新 `analysis_v1/INPUT_LEDGER` を作る。将来入口 `run_manifest.py`（未実装）。全参照が既知／未知へ対応しPK重複0、系列版混同0がPASS。
2. **A adapter**：今回 `a_fixed_od.py` の10例とmax-plus閉形式を受入fixtureとし、将来 `run_a_fixed_od.py --protocol ANALYSIS_PROTOCOL.json` を実装。政策78×36と機構64×36×4を別出力。改善の有無を合否に使わず、全task・帰庫・分母・政策時刻が追跡できれば合格。
3. **B plan adapter**：将来 `run_b_plan_metrics.py`。全8設定、10rep、460入力のroute permutation、原OD cost／距離、参照407／未確定53、初期解、fit/measurement資源を結合。18例の独立算術・3極小最適値を回帰fixtureにする。既存classical orbit最小も別比較。証明がないgap、欠測CPUを推測で補完しない。
4. **C整理**：将来 `summarize_c_conditions.py`。保存MATERIAL_ENERGY、T09部材、bridgeを再集計しδ境界と走行条件別感度を出す。既存50検算に一致、183NULL／1FAIL保持、加重率と個別率を区別できれば合格。新SUMO不要。
5. **統合・統計・論文用表**：将来 `paired_summary.py`。必要時のみ事前固定cluster感度。因果matrixのUNTESTED／INVALIDを残し、A/B/C総合効果を作らない。まず表と解釈をレビューし、その後別依頼で論文へ反映する。

全件入口名は次回作成予定であり、本領域に実装・実行したとは主張しない。今回の再現は support.py→a_fixed_od.py→b_existing_metrics.py→c_conditional_checks.py→road_history.py→alternative_fixtures.py→write_design.py→finalize_review.py。すべて `.conda/bin/python -B`。pdftotext抽出コマンドはC_LITERATURE_LOCATORSのPDFを入力し、新領域CHEN2020_TEXT.txtへ出力する。

## 計算量と停止

Aは既知318個の(input,route,departure)unionをcacheし、参照2,808＋機構9,216へ戻せる設計。4task＋帰庫の約1,590脚計算が核となるが、元参照対応は省かない。Bは全参照を直接積分しても1,591,680脚のOD数値加算、古典460経路は19,896脚。これは新経路探索や回路計算ではない。入力最大126×126、出力をstream化する。

今回測ったwallは監査I/O込みで、全件工期に線形外挿しない。次回は入力hash固定後に少数batchでwall/CPU/RSSを計測し、残り数量から予算を明記する。新しいsolver/SUMO呼出し、ソースhash変化、参照欠落の無表示、期限定義の変更があれば停止。結果が同じ・悪化・非有意でも追跡性があれば合格。
