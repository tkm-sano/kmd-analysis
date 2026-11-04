# 統合実験仕様 v1.0 — 2026-11-02

状態：監査後の研究仕様を固定。全件実行は未開始。旧成果のfreezeを変更しない。今回の依頼を計画作成の採用根拠とし、過去資料のNOT_AUTHORIZED表記は当時の記録として保持する。因果効果の改善、量子優位、統計的有意性を合格条件にしない。

## 1. 母集団と比較を固定

|series_id|母集団・証拠|目的・比較|除外する解釈|
|---|---|---|---|
|A_OLD_TW_R1|旧4配送先78物理問題。D10正式採用36条件、D11、原古典・QAOA JSON|取得→採用→出発・経路→配送先別完了・定時性|取得率を定時配達率にしない|
|B_NOW_NO_TW_R0_R5|UNIFIED_NO_CUSTOMER_WINDOWS_V1。78/78/78/78/78/70、先数3/4/5/25/100/125。11月2日stagedの最適化済み8設定|古典初期経路対各保存測定経路→走行・帰庫・Controlled-DC|旧R4=99や旧460軌跡と結合しない。顧客時間窓を追加しない|
|C_MATERIAL_CONDITIONAL|T08 stage2 run02、T09 run01、bridge run01、旧古典460保存軌跡|同一速度・共通非パック質量で材料条件→部材質量→DC|材料解析の量子寄与、完成パック比較、実EV削減率にしない|

Bの8設定はMEAN_P2、CVAR10_P2、CVAR01_P2、COHERENT2_P2、COHERENT4_P2、GROVER_P2、GROVER_P3、ACTIVE_ADJACENT_P3_GRID。mode=OPTIMIZED、rep=0…9に限定した主比較とする。固定非零・脱位相対照、旧p1、旧MAIN、11月1日p2は独立補助表に残し、混ぜて分母を増やさない。各設定のSOURCE_SNAPSHOT・PROTOCOL・CONFIGURATION_FROZEN・保存結果を一組で固定する。証明実装の歴史版は対応するSOURCE_AT_*を使用する。

## 2. Aの運用政策

L={900,3600,7200}、T_C=120、T_Q={60,900,3600,7200}、B={0,120,720}秒、other_C=other_Q=0、switch=600、dispatch=120。要求時刻=-L、利用可能時刻t_C=-L+120、t_Q=-L+T_Q、採用期限=-B。成功かつt_Q≤期限なら量子採用。成功でも間に合わなければ期限で古典へ切替。未取得は失敗判明時刻と期限の早い方で切替。古典利用可能を待ち、切替600秒とdispatch120秒を加え、出発は0秒以降とする。

この仮想時刻をCPUシミュレーション実測時間や将来QPU性能へ置換しない。14未取得にも古典代替を割り当て、需要を分母に残す。全78×36の政策評価が主運用集計である。

成功64物理問題では各運用条件について次の機構確認を別表にする。

|condition|経路|出発時刻|
|---|---|---|
|CC|古典|古典政策の出発|
|QC|QAOA|古典政策の出発|
|CQ|古典|量子優先政策の出発|
|QQ|QAOA|量子優先政策の出発|

量子優先政策が切替となる条件にも量子経路を入れるQC/QQは、取得後の反事実的機構比較であり実採用ではない。未取得14件はこの64件比較に入れないが全78件政策表から除かない。最大64×36×4=9,216参照であり実行数ではない。CCとの差で経路効果、出発効果、交互作用QQ−QC−CQ+CCを報告する。時間窓・需要・期限を差が出るよう変更しない。

## 3. 配送指標とイベント

固定需要集合Dに対しF_PE=Σq_i I(完了_i≤deadline_i)/Σq_iを主指標、F_count=ΣI/|D|を副指標とする。配送先ごとにON_TIME、LATE、NOT_COMPLETED、INDETERMINATEを保持する。未配達・未知を除いて分母を縮小しない。未知がある場合、確定値を欠測とし、既知定時PE/全PEを下限、(既知定時PE+未知PE)/全PEを上限として併記する。未知を未配達確定にしない。

旧dueはサービス開始期限。Aの採用済みD03完了期限=due_start+serviceを維持し、元のdueも残す。モデル完了候補=max(native stop started,ready)+serviceは診断指標であり実サービス完了ではない。到着、停車開始、作業開始、作業完了、停車終了、帰庫を別列にする。until・durationによる停車終了と作業完了の差を測定し、正式受入前は候補値に限定する。右打切り、出発不能、経路不能、teleport、collision、出力欠損を別状態とする。rc=0のみで配送成功としない。

## 4. 電力量と材料

Controlled-DCの観測済み1秒区間を主分析として維持する。W1=転がり、W2=空気抵抗、W3=並進慣性、W4=回転慣性。各区間でW1+W2+W3+W4を合算後max(合計,0)/η、η=.90、J/3600でWh。成分ごとに正値化して合算しない。旧モデルは平坦・回生なし・補機除外・回転等価質量61kg、CdA=1.175、ρ=1.2041、g=9.80665、Crrの圧力条件をfreeze通り使用する。未知の終端区間を0Whにしない。3Bの回生・補機・SOC拡張は別版・別感度表とする。

Bは帰庫・走行距離・観測距離・走行時間・停止・再発進・未完了を併記する。古典と量子のサービス対象・完了状態が一致しない場合、低Whを省電力達成にしない。差はQ−C Wh、削減はC−Q Wh、個別削減率平均とΣ削減/Σ古典DCの総量加重率を区別する。

Cはgross=20,000Wh、usable=18,000Wh。q_refはLP=171.875、S200=195.959596 Ah/kg、追加利用率・平均全電池電圧・正負活物質率・N/Pは保存シナリオの明示値を使用する。保持率と初期損失を再適用しない。T08は簡略固定部材会計、T09は幾何・箔・膜・液の既知部材会計で、固定19/15kgをT09へ再加算しない。

b=M_known,LP−M_known,S、δ=M_unknown,S−M_unknown,LPと定義し、全質量削減=b−δ。δ<bなら軽量、等号で相殺、δ>bで逆転。部材未知値はnullのまま。DCへの符号伝達は保存質量領域・同一速度・厳密増加を満たす場合に限定する。branch切替があるので単純比例は仮定しない。B0/B1/B2を材料主入力に復活させない。

## 5. 共通台帳の実装契約

|table / 主キー|必須列|
|---|---|
|problem / (series_id,input_sha256)|problem_id、parent_id、demand_group_id、版、固定需要、原入力・生成来歴|
|plan / plan_id|series_id、input_sha256、method、config_id、fit_id、measurement_seed、rep、取得状態、route、objective、参照値・参照状態、source_path/hash|
|operation / (plan_id,policy_id,condition_id)|採否、利用可能、採用期限、切替理由、出発、時刻の実測/仮想区分|
|run_input / run_signature|road_sha256、route edge/lane/pos、depart、vehicle/type/mass、stop duration/until/parking、traffic設定/seed、SUMO/fork/library・OS・環境hash、出力契約|
|plan_run_link / (operation_id,run_id)|再利用根拠、全元参照、比較条件、受入状態|
|event / (run_id,task_id,event_type,event_seq)|時刻、単位、観測/モデル候補、完了状態、deadline、q_PE、失敗理由|
|energy / (trajectory_sha256,mass_condition_id,dc_model_hash)|走行質量、W1〜W4、合計DC、観測境界、状態、部材未知・設計条件|
|evidence / evidence_id|source_path、source_sha256、位置、独立検算、PASS/CONDITIONAL/HOLD/FAIL、未確認事項|

run_signatureは上記全走行入力を正規化したJSONのSHA256で作る。未知項目が一つでもあればUNBOUNDとし完全重複排除を認定しない。訪問順だけでrunを共有しない。同じPID文字列・件数だけで系列を結合しない。4,987入力・経路組はpre-dedupでありrun_signatureではない。全36,800参照・全2,808判断を対応表に保持する。

## 6. 統計と変更規則

物理問題、親問題、需要群、論理条件、fit、測定seed、交通seed、軌跡、材料条件を別IDで保持する。主比較は同一物理問題内の対応差。測定seedを平均して物理問題を等重みとし、親依存は親clusterによる区間または記述統計で扱う。26親群と複数需要条件・共通fitの依存を保持し、25,760感度行を独立標本にしない。交通seedは変動の存在を確認した後に反復数・推定対象を事前登録する。検定のための事後的な期限・標本数変更は禁止。A/B/C合算の「総合量子効果量」は算出しない。

変更が必要なら本版を保持してv1.1の理由・対象・影響を記録する。改善ゼロ・逆転も、媒介イベント・質量境界から説明できれば研究上の受入対象である。
