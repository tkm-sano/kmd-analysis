# 接続監査（2026-11-15）

AGENTS.md、README、git status、HEADを読み、開始HEAD `8605d5412f6af62229a83095c35ab04c8c7dd9b1` を確認した。README/.gitignoreの既存変更、多数の未追跡研究資産を保持する。開始状態はINITIAL_GIT_STATUS.txt、328既存ファイルのhashはPRESERVATION_BEFORE.json。旧Aの7実装/設定/テストは専用freeze JSONにも記録する。今回の編集は新しいcomparison_v1パッケージ、比較CLI、schema/設定例、新規テスト・文書・結果の追加に限定する。

同名を混同せず `baseline_a_rule_v1_20261115` のFINAL_REPORT_JA/BASELINE_A_RULE_SPEC/EXPERIMENT_CONTRACT/REPRODUCE/DECISION/ALL_ATTEMPTS/REPRODUCIBILITYと、参照先の実コード・設定・plan/validationを照合した。S2原本2回のraw SHAは依頼の `64114d3fed738a14198c0958a4c3cdd6bafb9c9d81926bdaf276250bd651f4d9` と一致した。保存済み結果は主設定4件+感度2件、VALIDATED5件/NO_FEASIBLE_PLAN1件で、2バースの採用D/W/Tはnull、診断計画と勤務超過が残っていた。これは保存された物理検証ログの確認であり、その時点での新たな独立再計算とは区別する。新版接続確認の実行により、同一bytesの計画へ親の共通・独立再計算も実施する。

## 呼出経路一覧

|経路|実際の生成・完成・検証|入出力・ID・単位|計時・失敗|
|---|---|---|---|
|新A単独（原CLI）|run_a_rule_v1.worker→rule_inputs.load_input→rule_v1.generate→validate_plan+audit_rule（内部でDecimal audit_plan）|共通Problem→Plan。元stop/vehicle/berth文字列ID。距離m、時計整数秒、D km/W min|一般import後・input/hash直前〜一致完了。native180/計画150/外側300。VALIDATED/VALIDATED_LIMIT/NO_FEASIBLE_PLAN/INPUT_INVALID等|
|旧DWT内A|run_dwt→experiment.run_registered→worker.execute→methods.generate(A)→construction.create_plan(A2)→complete→complete_routes|同じProblem/Planだが完成器で車両/便/積込開始を変更し得る|既存native TとA除外/人手参照メタデータ。新Aではない|
|B|worker.execute_trial→parallel.execute_parallel→4×worker.execute→methods.generate(B)→directed_cw→complete→complete_routes|供給便ルートはOD index、完成Planは元ID|setup/待機枝をnative T外。枝停止・候補選択・最終二重検証まで親native wall。枝失敗も保持|
|C|同じ四枝→directed_cw→routing_pool(OR Routing)→complete|CW/OR候補pool→元ID Plan|同じ資源/計時。予算時は検証済みincumbentを保持し得る|
|D|同じ四枝→directed_cw→hybrid→seed完成→車両日master→AOA→拡張pool→最終complete|有限CW/macro/time候補、実装済みQiskit statevector、Plan.execution_kind=quantum_circuit_simulator|未選択枝も回路/shots/CPUを保持。実機なし。native backend環境と実観測を別記|
|新版A〜D|run_comparison_v1→登録case→共通親input/hash→fresh comparison worker→A直結または既存execute_parallel→candidate bytes→親共通/独立/固有検証|同じ元Problem/Plan、形式変換による割当・訪問・全時刻の変更なし|新T_kindはchild起動/初期化/IPCも含む親wall。旧native Tは別欄。全試行四軸状態と採用null規則|

## 共通完成器・検証の実体

`pipeline/completion.py:complete_routes` はCP-SATにより有限route poolの選択、物理車両/便所属、積込開始を決める。D/W整数目的の辞書式tieとε条件、各枝native1threadがある。`assemble` は選ばれたstartを保持してバースintervalを彩色し、供給された便の内部訪問順は反転・再最適化しない。これはコードで確認した事実であり、実経路出力でもpool membershipを照合する。

`common.validation.validate_plan` は独立にOD.legと整数ceilを使い、物理制約とD/W/W1/W2を検査する。`baseline_a.program_validation.audit_plan` は生成器の関数を呼ばずDecimalで全arc・時刻を加算する。`rule_validation.audit_rule` はさらに別のリストイベントでAのFCFSを再構成する。新比較はA固有規則をBCDの物理制約へ加えない。

共通v1.1は1地点1単位、60/便、最大2便、積込1800/配達120/準備0秒、08:00〜20:00、unused_vehicles_allowed=true、既定ready式で依頼と一致した。実ODは登録Route版の同一Route距離/時間である。旧same_table_response文言はAの新版参照契約と同じくRoute manifestを道路正本として扱い、物理設定原本を変えない。input/OD/凍結需要ピンは新登録・各試行内にも照合する。

## 旧評価と必要な最小接続

`dwt/evaluation.py` は旧COMPLETE/program_wall/standard_output/ε状態を必要とし、AをJから除外する。`dwt/analysis.py` は既存config.referenceの60秒等と重み感度を使い、限定B/C/Dを扱う。これらを破壊的に変更すると旧結果の意味が変わるため、新しいreference/aggregateを独立実装した。BCDアルゴリズムへ渡す旧config内のreference欄は保全するが、新評価はそこを参照しない。

最小接続は、専用registry、共通case登録、凍結A直結worker、既存BCD四枝worker呼出、bytes非改変のPlan受渡し、親の共通二重検証、共通wall watchdog、四軸状態、事前A参照groupと二層集計である。既存ソースやAの探索規則を変更しない。実呼出証拠のwrapperは関数の引数/返値を変えず、呼出点/PID/affinityだけを別ログへ残す。

## 確認された差分・留保

既存AはMOVE_LIMITで通常終了しており、外側時間切れではない。Aの単独Tは依存importを除くため、新比較Tとは同一範囲ではない。BCD native準備除外も同じく別時間種類として保存する。S2原本のbytesは確認済みで、新形式Plan読戻し時のmetadata tuple→listはJSON表現の差と判明したため、raw bytesと順序を保つcanonical semantic hashで区別する。期待計画hashを新出力へ合わせて変更していない。

開発ログ01は新テストの構文誤りでcollection失敗、02はこのtuple/listの比較方法で1件失敗。修正は新テスト/アダプタ契約の範囲であり、Aは一切編集していない。失敗ログは残し、03/04と最終コードの検証を別ログに保存した。回帰には任意Qulacs依存の未導入によるskipがあり、Qiskit実経路と混同しない。実行結果・未実行範囲の確定はVALIDATION_RECORD/FINAL_REPORTを参照する。
