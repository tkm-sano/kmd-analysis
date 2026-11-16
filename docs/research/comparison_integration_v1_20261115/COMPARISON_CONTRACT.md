# 方式全体比較契約 v1（2026-11-15）

契約IDは `whole-method-A_rule_v1-20261115-comparison-v1`。主比較は「同一の需要、道路、運行上の物理条件、利用可能計算資源の下で、各方式が生成する配送計画の総走行距離、積込待機時間、検証済み計画を得るまでの計算時間を比較する。積込順・積込開始の決定規則も各方式の一部とする。」で固定する。

Aは凍結A_rule_v1+FCFS、B/C/Dは現行候補生成+共通完成器である。D対A、D対Cの差は方式全体の差であり、量子処理単独の因果効果ではない。他処理を揃えた別対照が必要である。AにもO/H負荷改善がある。Aとの比較を対象事業者の実績改善と説明しない。全方式FCFS化は今回実装せず、別契約の診断拡張候補に留める。CLIヘルプ・全結果metadataにも同じ意味を保存する。

## 識別と入力

研究条件method=A/B/C/D、implementation_id、algorithm_version、method_config_hash（意味内容のcanonical SHA）、method_config_file_hash（実ファイルSHA）、source_hashes、code_version、contract_idを区別する。旧A2、旧DWT内A、旧Tref60秒、旧program_wallを新契約へ改名しない。旧CLIは編集しない。

同一caseに共通inputを一つだけ持ち、run単位のinput/hash/physical/budget/T_kind/config上書きを拒否する。登録時にinput.json、Route OD manifestと3配列をhash固定し、実行時は親・子・BCD内部枝で読込/照合する。完成計画/route poolを入力にしない。正式ケースは凍結A設定のRouteピンと一致しなければ登録不可。synthetic_validationはfixtureと明記し、実需要ケースと混ぜない。

物理条件は `common_conditions_v1_1.json` の固定SHAと入力Problemで検査する。京浜トラックターミナル、単一拠点、大田区ToC、顧客時間窓なし。1地点1単位、60/便、最大2便、120秒/地点、1800秒/非空便、準備0、28800〜72000秒。車両数は利用可能台数で、非稼働許可、空便は生成しない。初便readyは `28800+(3600*(2*v+1))//(2*V)`、第2便readyは前便帰着。各有向arcの移動秒をceilする。旧Table版、900秒準備、上流PEを混ぜない。道路は固定Route manifestの同一Route距離/時間を正本とし、common設定の旧same_table_response文言はこの参照関係で解消する。

地点ID/車両ID/バースIDは共通Problem/Planの元の文字列を保持する。距離m→D km、待機秒→W分、時計はJST日内整数秒。共通物理検証は全地点一回、拠点発着、容量・最大便、便接続、積込終了出発、バース非重複、移動・作業・勤務・非負待機・D/W。A固有FCFS/OH/停止規則の検査はAだけに課す。

## 資源・予算

同じ利用可能な異なる4物理コアを登録し、実行時もCPU topologyを読み、足りなければ拒否する。Aの計画生成は1worker/1コア/native1thread、B/C/Dは既存四枝×1コア/native1thread。親の共通読込/検証はAで同じ1コア、BCDで4コア枠を共有する。新しい親/子の実行管理プロセスは計画方式の並列枝とは別に資源を開示する。Aを4複製しない。方式間は逐次。内部枝は外側1試行の内部候補であり独立需要/反復へ加算しない。

外側wallはcaseごとの必須正有限 `budget_wall_s`。欠落/null/0/無限では登録・実行を拒否する。同一caseでは全方式同じ値。今回のA接続確認は240秒/件。最初の小規模A〜D確認は90秒/件で、BCDが依存import中に停止した全3失敗を保全した。別のr2登録では420秒/件（既存の共通依存初期化上限240秒+native計画90秒+起動/転送/親検証の予約90秒）とする。VALIDATION_AMENDMENT_R2.jsonをr2実行前に保存した。これは後続本実験の上限を決めたものではない。A単独の旧300秒プロセス上限と同一視しない。

Aのnative設定150秒（計画の候補境界で検知）/180秒（workerで強制）/4096MiBと候補10000を保持する。MOVE_LIMITは通常停止。BCDは現行設定・探索を変更せず、共通親の読込とworker初期化後の残wallの90%を既存execute_parallelへ渡す。caseで `BCD_native_cap_s` を明示した場合はその値とのminを取る（r2小規模では90秒）。内部上限は正有限・外側以下を登録時に検査する。既存親はnative上限の80%までを全枝共通締切、残20%を回収/選択/二重検証に使う。新比較親は残りを転送/最終検証用に確保する。予約は遵守保証ではなく、実際の親deadlineを判定する。BCDのεはcaseの明示的 `BCD_epsilon_W_min`（今回はnull）で、物理W制約やAの採否条件とは分けた方式の探索条件である。

PID/affinity、thread環境/観測数、CPU時間、最大RSS、全枝seed・状態・D/W・計算・shots（未選択枝込み）を保存する。終了前に観測できない資源はnullまたは部分量として扱う。RSS合計は共有ページを重複し得るhigh-water markの上界で、同時物理メモリ実測ではない。Dは既存設定のQiskit statevectorシミュレータで、実際のbackend/version/観測回路も保存する。実機・有料計算を追加しない。

## 計時

T_kind=`comparison_parent_wall_including_process_setup_v1`。新比較親が入力読込/hashに入る前に開始し、入力、fresh worker起動、必要な初期化、各方式計画、全枝停止/選択、必要な候補シリアライズ/IPC、変換、共通物理検証、独立Decimal再計算、一致確認と採用用bytes確保までを含む。通常完了ではworker停止・回収までの親wallを採る。native timeを足して代用しない。

全方式の比較親は同じ検証ライブラリ群だけを事前importし、その共通準備をCOORDINATOR_SETUP.jsonで別計測する。route pool・solver・回路は準備しない。登録時には同一caseの共通入力を一度物理検証してpreflight状態を保存するが、各試行で必ず全入力を再読込/hash/検証し、その時間をT_inputに含む。登録検証を理由に試行内読込を省略しない。これにより、物理的に有効と確認済みの入力の読込中に時間切れになった場合も、有効入力の実行分母から除外しない。fresh childの起動と方式に必要なimport/初期化は全方式でT内。この新版は旧native T（依存import/待機枝準備を除外）と別時間種類である。T_nativeをそのまま参照にしない。

T_inputは親の共通読込/hash/入力前処理、T_adapterは候補読込・同定、T_validationは親の二重/固有検証、T_planningは残る親wall（workerの読込/初期化/探索/転送/回収を含む）。四区間は分割として扱う。T_setupはnative報告の観測可能な準備でT_planningと重複する。T_attemptは実際の経過（失敗・cleanup込み）。保管用成果物/最終報告/集計はT外でT_exportを別記。出力名で候補受渡しやIPCをT外へ逃がさない。

OS cache/無関係な共有ホスト負荷は制御しない。新規プロセスだけで完全coldと呼ばず、共有cacheを消さない。需要ごとの再学習は現行方式にない。将来必要ならT内の方式処理へ入れる別契約が必要である。

## 状態と採用

input_state（NOT_CHECKED/VALID/INVALID）、termination_reason、validation_state、adoptableを独立に保存する。通常、A_MOVE_LIMIT、OUTER_WALL_LIMIT、INPUT_INVALID、CHILD_PROCESS_ERROR、RUNTIME_ERROR、CLEANUP_ERROR、NOT_STARTEDを識別する。nativeの停止理由と各枝状態も保持する。plan検証はNOT_RUN/NO_PLAN/NO_FEASIBLE_PLAN/INVALID_PLAN/VALIDATED/NATIVE_DEADLINE_REJECTEDを分ける。

外側上限は検証済み計画を得るまでの上限。親検証と必要なbytes確保が期限内に完了したものだけ採用する。期限後に初めて検証した候補は遡及採用しない。期限前に保存済みの採用チェックポイントがある場合はそのT_programと計画を保持し、後の上限停止・cleanupまでのT_attemptは分ける。通常のBCDではnativeが全枝回収後に候補を渡す。cleanupの生存確認が失敗した場合は採用しない。

採用なしではD/W/W内訳/T_programはnull。棄却計画・診断・T_attemptは保存する。勤務超過だけの候補と構造的に不正な候補も検証状態で識別する。ヒューリスティック未発見を問題の実行不能証明にしない。リトライは別run_id/attempt_id/retry_ofで追加し、元試行を置換しない。集計の主対応比較では元試行を使い、リトライを黙って代用しない。

## D/W・参照・集計

Dは非空便全arc（拠点往復込み）の物理距離総和/1000、WはΣ(load_start−ready)/60。W=W_first+W_reloadを保存し、作業1800秒は含めず、負待機は補正しない。ペナルティをDに足さない。稼働数、非空便数、車両別最終帰着/L/O、全便イベント、バース利用区間を保存する。初便待機を方式共通定数として差し引かない。FCFSの360/720/1440分検算を非FCFSへ強制しない。

Jと全試行/対応比較の詳細は [REFERENCE_AND_AGGREGATION_SPEC.md](REFERENCE_AND_AGGREGATION_SPEC.md)。今回のphaseはcontract_checkのみで、p値/CI/統計優越性/正式T_A_refを出さない。正式なシナリオ・件数・反復・予算・参照会員は後続manifestで指定し、未指定のテンプレートは実行不可である。
