# 独立データ監査 — 2026-11-02

## 1. 方法・判定単位

新規independent_audit.pyとsupplement_audit.pyでCSV/JSON/XML/NPZを読取り、標準ライブラリのFraction・算術およびNPZ読込み用numpyで検算した。既存研究モジュール・validator・runnerはimportも起動もしていない。学習、求解、回路simulation、SUMOの実行は0。DCは保存値の差引き・集計と代表1軌跡のscalar検算のみで、460×全感度の科学再計算ではない。

PASSは記載した照合範囲に限る。CONDITIONALは算術が合う条件付きモデル、HOLDは必要証拠・受入不足、FAILは明示的不適合。表の数字は今回の個別行からの再計算。過去報告の集計値を検算として転載していない。道路のFAILは既存監査の保存結果を読んだ判断で、今回の動的再試験ではない。

独立性の留保：既存bridge integrate.pyはControlled-DC、T08 pack_budget、既存モデルをimportするため、それ自身の検証成功を独立物理検証に数えない。公開controlled_dc.pyも凍結sourceのaliasである。同一実装を呼ぶ回帰・scalarチェックと、今回の別実装算術を分ける。材料式の再実装も同じモデル仮定を共有し、文献値の測定妥当性を証明しない。

## 2. CSV・JSON構造

全列名、文字列表現から推定した型、空/NULL/NaN件数、数値範囲、全行重複、key重複はCSV_SCHEMA_AUDIT.jsonに保存。CSVは物理型を持たないので「number/string-encoded」と実数型を区別した。空欄を0へ変換していない。JSONは全対象をparseし、原run status、route、objectiveを照合した。各参照のsource行はB_PLAN_REFERENCES.csvのsource_pathとrep、原CSV位置は先頭headerを1行目として扱う。

|対象|行数|採用key・結果|欠測・意味|
|---|---:|---|---|
|D11 conditions_36|36|scenario_id一意|切替なしのfallbackは空|
|D11 operations_2808|2,808|scenario_id,PID一意、全行重複0|Q採用のfallback関連3列は空。未実行とは別|
|D11 logical_candidates|303|PID,route_identity,t_depart一意|全行LOGICAL_CANDIDATE_ONLY|
|A_NATIVE_TASK_COMPLETION|332|run_id,task_id一意|physical_arrival_timeは未知。real_service_observed=false|
|A_BASELINE_METRICS|83|run_id一意|全83run INDETERMINATE、DIAGNOSTIC_ONLY|
|mirror ALL_SEEDS|69,000|run_id,variant,mode,rep一意|厳密最適値/厳密gapは未知集合に空|
|Grover ALL_SEEDS|9,200|同上一意|同上|
|active p3 ALL_SEEDS|9,200|同上一意|原CSVのnull列0。最適値自体は別参照|
|T08 MATERIAL_ENERGY|4,464|dataset,physical_instance_id,method,rolling_case,scenario_id一意|補機/turn・終端未観測は空。全行を独立軌跡に数えない|
|T09 PACK_20KWH_SENSITIVITY|183|研究行は行番号、物理条件は別signature|全列一致重複59行。183論理行、部材・境界含む既存signatureは117種類。重複を独立実験としない|
|bridge T09_MASS_BOUNDARIES|183|scenario_id一意|未対材料行の比較項目空、未知部材は空|
|bridge DC_MASS_RESPONSE|25,760|pair_id,probe_id,physical_instance_id,rolling_case,reference_running_mass_kg一意|actual_LP/S_pack_massは全て空|
|bridge DC比較|406|series,policy,probe,Crr,scale,reference_mass一意|T08未知差probeは該当なし空|

監査途中の暫定keyではMATERIAL_ENERGYにmethodを、DC比較にreference_running_mass_kgを入れなかったため衝突852/196件を検出した。元CSVの矛盾ではなくkey設計不足と特定し、上表のkeyで再監査して0件。元データを変更して整合させていない。T09の重複59は残し、重複排除後の論理対応を保持する。

## 3. A：取得・採用・出発

原QAOA78 JSONと古典78 JSONをPIDで対応付け、2,808行それぞれの選択経路を原JSONと照合。イベントの早い方を選ぶ独立政策計算と一致した。

|値|独立再計算|判定・範囲|
|---|---:|---|
|QAOA取得|64/78=82.051282%|PASS。78プロセスCOMPLETEDと64経路取得は別|
|未取得|14|PASS。NOT_DELIVEREDには変換しない|
|成功内同一経路/異経路|59/5|PASS。経路同一と最適値一致は別概念|
|選択最適値一致|59/64=92.1875%|PASS、原有理数目的値対保存厳密参照。全78分母なら59/78、未取得gapは空|
|成功内平均gap|0.2007785883%|PASS、取得成功64の単純平均|
|量子採用/古典採用|1,344/1,464|PASS。古典=成功側切替960+未取得側504|
|出発0/120/600/720秒|1,872/192/468/276|PASS。正遅延936判断|
|論理候補|303=83+64+78+78|PASS、原2,808行のPID/訪問順/出発集合と候補CSV集合が同一|
|完全固有走行入力|未確定|HOLD。道路/車両/stop/交通/環境の全signatureがない|
|古典search合計/平均|0.0292021483 / 0.0003743865秒|PASS、78。worker/proc時間と別|
|QAOA wall合計/平均|2,577.5654952 / 33.04571148秒|PASS、78。CPU statevector側の保存wall、仮想T_QやQPU時間ではない|

303件の83出発0基準を受入済み再利用と認めていない。220正遅延候補はnative再実行が必要であり、0秒軌跡の時間シフトでは代替不可。機構4条件の追加参照は303の外に生じ得る。

実装読取り：routing/solver.pyの目的値は有向travel和で、service/waitを目的に加えない。replayはtravel+serviceとready待ちを累積し、dueをサービス開始側で判定する。protocol_v2/science.pyは位置one-hot制約と不可行順列の罰則を構成し、容量/時間窓/帰還を満たす経路だけを測定後採用する。最終独立4096shotsの可行経路から道路目的値最小（tieはbitstring）を選び、なければ未取得。訓練2048shotsの最良候補を最終未取得の代替へ黙って転用しない。これらの公開保存コードの読取りは実装契約確認で、今回QAOAを再実行したものではない。

原stops.xmlのstarted/endedを全332タスクと直接照合し、候補完了=max(started,ready)+serviceを再計算した。83固有run参照では593/593 PE、332/332候補完了、最小余裕3,099秒。これは重複を除いた実需要全体ではなく83runの参照総和である。全古典78の556PE、共通64内の各466PEとは分母が違う。受入済み実サービス完了率ではない。早着待ちで出発差が吸収される可能性、期限余裕による指標飽和を説明する候補証拠に限定する。

**運用成果はHOLD。** D13 phase4の165テスト成功記録は隔離native/通信・契約の技術試験であり、全83run・正遅延・実作業完了の受入を意味しない。全2,808政策でのnative定時率は未取得。

## 4. B：36,800参照と経路重複

正式主入力はstaged/mirror_family/MANIFESTのUNIFIED_NO_CUSTOMER_WINDOWS_V1に属する460 NPZ。全460のSHA256を検証し、原NPZを読んで訪問順・道路目的値を照合。R0〜R4各78、R5=70。R4=100であり旧99先系列ではない。

69,000+9,200+9,200=87,400行にはfixed/dephased対照を含む。original_swap_reproの9,200行を加えた全プログラム96,600測定行とも区別する。主対象はOPTIMIZEDの5 mirror設定23,000、Grover2設定9,200、active1設定4,600、計36,800。各設定460×10、一意key・欠落なし。

全36,800の原JSON route_indices、objectiveをCSVと照合し、全顧客一回・デポ帰還形とNPZの有向travel和を別算術で確認した。不一致0（秒許容1e-7）。原JSONの全対象run状態はPASS。これをQPU実行・走行完了・新規fit36,800件とはしない。

|設定|参照|入力hash+経路の組|
|---|---:|---:|
|MEAN/CVAR10/CVAR01/COHERENT2/COHERENT4 各|4,600|460|
|ACTIVE_ADJACENT_P3_GRID|4,600|460|
|GROVER_P2|4,600|2,494|
|GROVER_P3|4,600|2,494|
|全8設定union|36,800|**4,987**|

4,987は入力と訪問順のpre-dedupであり完全run数ではない。出発/道路/車両/stop/交通/seed/環境を結ぶ新台帳が必要。SUMO36,800回を計画する根拠はない。

B_QUALITY_RECALCULATED.csvは原JSON有理数目的値から参照最適値一致・gap・古典初期差を再計算した48行。厳密参照はR0/R1/R2/R3/R4/R5で78/78/78/78/57/38物理問題、計407。残り53は下界参照で、厳密gapを補完しない。例えばMEAN_P2の平均厳密gapは0/0.0190808356/0.1039532932/2.2154473589/5.0601144552/4.9313137447%。最後2値は既知部分集合に限る。10seedを10倍の独立問題としない。最適値一致は原Fraction等号を用いた。

計時・資源はB_SAVED_TIMING_SCOPES.csvに設定別保存fit wall/CPUの件数・合計・平均、RSS最大を保存した。mirror/Groverのfit時間とactiveのcase全体時間は範囲が異なり、ランキング・全オンライン時間として合算しない。fitは10seedで共有。未保存のRSSを0にしない。回路深さ・ゲート数・QPU所要時間の全36,800行対応はHOLDであり、SOURCE_SNAPSHOTのMPS構造・Grover論理回路と実測物理資源を区別する。

ソース結合ではGrover36件のfit-source参照（18case×2ファイル）が最終snapshotと違った。例R3_001/P2 certified_phase_mc.py：期待db3e3e…、最終e04bd0…、差はhash不一致。SOURCE_AT_INITIAL内に期待hashが一致する原版を全36件確認した。証明式改訂ADOPTION記録も存在する。**歴史版対応PASS、最終版を全fitの実行版とする解釈は不可。** 行別期待/実値/対応版はB_SOURCE_BINDING_GAPS.csvに残した。証明の数学的全監査やraw Born全標本NPZからの再復号は今回はしていない。

**走行/DC接続はHOLD。** 現行8設定の全計画に対応するSUMO軌跡・帰庫・DCは未取得。旧Cの460軌跡がそのまま使えることは件数から導けない。

## 5. C：材料・部材・DC

入力式LP=121/.704=171.875 Ah/kg、S200=194/.99≒195.95959596、保存実行値195.959596。Chen由来の保持試験から逆算した参照で、同一の実用全電池測定や量子計算達成値ではない。設定の利用率1、平均電圧3.5V、gross20kWh、usable18kWhを区別。18kWhを質量式へ代入しない。

T08はQΣ=E_gross/V、m_pos=QΣ/(q_ref u)、正極塗工=m_pos/f_pos、負極活物質=N/P×QΣ/q_neg、負極塗工をf_negで除し、100cell×0.19kgとpack_other15kg等を加える簡略式を別Fraction算術で再実装した。

|値|独立再計算|判定|
|---|---:|---|
|T08 LP / S200簡略質量|96.1456547987 / 90.6973573836 kg|PASS算術、CONDITIONAL工学|
|T08差|5.44829741508 kg|期待照合値と1e-10kg内で一致|
|下側Crr基準総DC / 削減|1,440,101.369798 / 5,941.555975 Wh|旧古典460各行のLP−Sを再集計|
|下側Crr総量加重率|0.412579010061%|CONDITIONAL。個別率平均0.409329419377%とは違う|
|上側Crr総量加重率|0.413590411697%|CONDITIONAL。個別率平均0.410435042400%|
|T09固定担持の既知差|9.722608121108 kg|元PACK部材総和LP−S、B015。完成パック差ではない|
|T09固定LP面積の既知差|5.977891152149 kg|同じく原部材行から照合。設計条件固定に限定|
|T09完成パック空欄|183/183|HOLD。未知部材を0にしない|
|T09対向面積不適合|1/183 FAIL_IF_SAME_STACK_FOOTPRINT|FAIL。条件違反行を保存したまま報告|
|bridge DC感度|25,760行、460軌跡hash|PASS構造/算術、CONDITIONALモデル|

T09の183行について正負活物質/塗工、Al/Cu箔、膜、液、既知総和をFractionで独立再計算し、最大誤差2.85e-14kg以下。箔=coated_face_area/2×厚さ×密度、膜=max(正負面積)×面密度、液=電極空隙+膜空隙+余剰液に液密度。対象LP/Sの密度等は転用仮定であり実測認証ではない。原部材比較72pairはC_RAW_PAIR_DIFFERENCES.csvに元CSV行番号を保存。

25,760行全てでDC差引き、個別率、b−δ、W1〜W4 baseline mask寄与+branch correctionを検算。成分残差最大2.985e-12Wh、率残差2.221e-16ポイント。392個のT09総量比較は元感度行から加重率を再集計、残差2.221e-16ポイント。T08の14比較は460行/規模別の別系列。

460圧縮軌跡のSHA256を全件照合。代表1軌跡について独立scalar区間ループでDCを保存値と1e-7Wh内照合。手計算可能な停止→加速→定速→減速fixture（1秒刻み、m=1200kg、p=4.5bar）の合計20.4410590185Whを保存。全25,760条件を生軌跡から再実行したとは主張しない。

相殺はδ=b、固定担持なら9.722608121108kg、固定面積なら5.977891152149kg。δはS−LPの未知部材差で、LPの未知絶対質量ではない。入力参照質量1200/1400kgを実LP完成パックへ読み替えない。同一速度の域内でDCが質量に厳密増加する条件では軽量・相殺・逆転の符号がDCへ伝達する。域外、異速度、負stock、力学モデル変更には適用しない。

## 6. 未確認・不適合を保持

|ID|場所・期待|実際・差/原因|判定・影響|
|---|---|---|---|
|G-A1|A run全条件を同一化する完全signature|303論理候補のみ。道路/環境等の結合不足|HOLD、確定走行数・再利用件数を主張不可|
|G-A2|native配送完了を採用/出発へ接続|正遅延936判断はnative未評価。83基準は診断|HOLD、正式定時配達率未確定|
|G-B1|Bの経路→走行/DC|4,987入力経路組に対する完全run未結合|HOLD、量子による走行省電力未検証|
|G-B2|fit source=一つの最終snapshotという想定|36参照のhashが異なるが歴史版で一致|履歴PASS。詳細CSVを保持、単一最終版再実行は不可|
|G-C1|T09 complete_pack_mass_kgが定まる|元CSV2〜184行全183空欄|HOLD、完成パック比較不可|
|F-C1|同一stack全面対向の必要条件|PACK_20KWH_SENSITIVITY.csv:184、overlap_condition=FAIL_IF_SAME_STACK_FOOTPRINT。正面積291.6053018545m²に対し負面積174.6031746032m²、差−117.0021272513m²|FAIL、同じfootprintの全面対向として採用不可。全183行に残す|
|F-R1|道路の左側通行/連続幾何/動的受入|旧網の設定・幾何留保、修正版静的改善後も動的受入FAIL|FAIL（保存監査）、実配送一般化/新全件展開を阻害|

道路の後続記録では元B6 183衝突記録、ガード0でも待ち/需要処理/固定青秒の同時受入不成立、修正版不採用。これを旧網受入成功へ読み替えない。各FAILは入力誤差を「修正済み」と称する操作ではなく、研究主張を制限する証拠である。

最終算術判定：CHECKS.json 818件PASS、SUPPLEMENT_CHECKS.json 4,877件PASS。これは監査項目の単位で、科学仮説や全研究にPASSを付けた数ではない。全入力hash・構造・算術の詳細と未実施範囲は00/04/05を併読する。
