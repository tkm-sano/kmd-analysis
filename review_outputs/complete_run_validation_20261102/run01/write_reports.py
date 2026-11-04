"""Create this phase's six reports and final evidence/preservation manifests."""
import json,collections,statistics,subprocess
from common import *
def main():
 protect_previous();summary=read(O/'RUN_MANIFEST_SUMMARY.json');gate=read(O/'ROAD_AND_EXECUTION_GATE.json');unit=read(O/'UNIT_TEST_RESULTS.json');native=read(O/'NATIVE_UNIT_SUMMARY.json');ind=read(O/'INDEPENDENT_VALIDATION.json');processes=read(O/'NATIVE_UNIT_PROCESS_RESULTS.json');c=read(PREV/'C_RECALCULATED.json');a=rows(O/'A_COMPLETE_RUNS.csv');b=rows(O/'B_COMPLETE_RUNS.csv')
 assert unit['successful'] and not native['failed_assertions'] and not ind['failed']
 pilot=[]
 for series,name in [('A','A_PILOT_CANDIDATES.csv'),('B','B_PILOT_CANDIDATES.csv')]:
  for x in rows(O/name):
   fullid=x.get('full_run_id',x.get('run_id',''))
   pilot.append({'series':series,'candidate_id':x['candidate_id'],'run_id':fullid,'input_sha256':fullid[4:] if fullid else None,'status':'NOT_EXECUTED_GATE_BLOCKED','reason':x['pilot_gate'],'wall_s':None,'CPU_s':None,'max_RSS_bytes':None,'traffic_seed':20260930,'teleport':None,'collisions':None,'unreachable':None,'return_s':None,'missing_trajectory':None,'DC_Wh':None,'independent_validation':'NOT_APPLICABLE_NO_EXECUTION'})
 table('PILOT_EXECUTION_STATUS.csv',pilot)
 A=summary['A'];BB=summary['B'];walls=[x['wall_s'] for x in processes];cpus=[x['CPU_s'] for x in processes];rss=[x['max_RSS_bytes'] for x in processes]
 boundscale=collections.Counter(x['scale'] for x in b if x['run_id']);boundrefs=sum(int(x['references']) for x in b if x['run_id'])
 write('FULL_RUN_RESOURCE_ESTIMATE.json',{'status':'HOLD_REGIONAL_PILOT_NOT_EXECUTED','regional_wall_s_per_case':None,'regional_CPU_s_per_case':None,'regional_max_RSS_bytes':None,'regional_failure_rate':None,'traffic_repetitions':None,'total_wall_estimate_s':None,'cost':None,'known_A_policy_inputs':303,'known_A_policy_mechanism_union':318,'known_B_complete_inputs':37,'unbound_B_candidates':4950,'formula':'sum_by_scale(N_s * repetitions_s * measured_t_s), with measured parallel/I-O/retry constraints','synthetic_unit_values_must_not_be_extrapolated':True})
 def report(name,text):(O/name).write_text(text.strip()+'\n')
 report('COMPLETE_RUN_MANIFEST.md',f'''
# 完全走行台帳 — 2026-11-02

開始HEAD `1b00bd7927fa1e7688e4772ac1da9db46d9bac11`。前回reviewの35成果物をSHA256照合して一致。前回の算術を全面再実行せず、採用仕様・既存判定を引き継いだ。旧研究ソース・入力・結果・FREEZE・前回レビューは変更しない。

ここで「完全」は**固定した現環境で走らせる入力内容が揃うこと**を指す。道路の受入、過去実行との環境同等性、clean build、実配送妥当性、未実行結果の保証は別判定。完全入力候補にIDが付いても実行を承認した意味ではない。

## 1. 件数と結合

|項目|A 旧窓あり4先|B 現行窓なしR0〜R5|
|---|---:|---:|
|元の主参照|2,808運用判断|36,800計画参照|
|入力/PID・訪問順・出発等の候補|303論理候補|4,987入力・訪問順組|
|完全入力で確定した固有run|303|37（判明部分集合）|
|入力不足で固有数を確定できない候補|0|4,950|
|既存成果の受入済み再利用|0|0|
|ゲート解消後に必要な新規走行|303|既知部分37＋未確定部分。総数未確定|
|今回の地域代表走行/全件走行|0 / 0|0 / 0|

Bの37を全Bの固有数と呼ばない。BはR0=22、R1=9、R2=6、R3〜R5=0の完全入力。完全候補に結合した元参照は{boundrefs:,}、残る{36800-boundrefs:,}参照は明示UNBOUND。未確定候補に完全run IDを発行していない。4,987の内訳を失わず、別のrecipe IDは未確定識別用としてのみ付与した。

## 2. Aの構築

D11 operationsとD12候補・INPUT_DETAILSを照合し、303候補の元車両XML/hash、原NPZ/hash、道路hash、vType/hash、訪問順・道路edge列・停車lane/endPos/duration/untilを読戻した。新しいA_INPUTSへvehicle XMLを生成し、requested departだけ変更した。untilは絶対時刻のまま保存仕様を維持し、0秒軌跡の時間シフトを使わない。

A_COMPLETE_RUNSは303入力、A_OPERATION_RUN_LINKSは2,808全判断のmethod/取得状態/仮想利用可能時刻/締切/採用/切替/要求出発を保存。actual departureは保存0秒の観測がある場合だけ記載し、正遅延はnull。要求時刻を実測出発へ読み替えない。0秒83候補に既存軌跡hashがあるが、過去環境同等性・配送成果受入が未成立なので全83も再利用承認0。

成功64×36×4=9,216の機構参照も別台帳A_FOUR_CONDITION_LINKSへ対応付けた。政策303に含まれない15組をA_ADDITIONAL_MECHANISM_RUNS/A_MECHANISM_INPUTSへ別に具体化した。政策と機構のunionは318固有入力。303という政策件数を318へ上書きせず、全機構比較まで行う場合は追加15走行が必要。

## 3. Bの構築と残る不足

前回B_PLAN_REFERENCESをそのまま主参照とし、460NPZのnodesとroute_indicesから訪問順を復元。R4=100、R5=70問題を維持。ENDPOINT_READBACKのrole別edge/lane/位置を照合した。現行Bでは出発0、停車duration102秒、untilなし、顧客ready/dueなしを新adapterで明示固定した。旧窓ありのuntilや待機を転用していない。

道路edge列は既存のclassical/canonical/quantum fixed_legs.trips.xmlとrou.xmlから、origin/destination edge・lane・位置が**厳密に一致**する保存区間だけを使って連結した。新しい経路探索は実行していない。物理問題数・PID文字列の一致だけで旧走行を結合していない。ODは元NPZと原input hashに結び、別網のOD/最適値を代入していない。

不足する位置付き区間は{BB['missing_positional_leg_requests']:,}固有要求。B_REQUIRED_POSITIONAL_LEGSとB_UNBOUND_LEGSに端点・seed・router/net hash・候補内位置を保存した。これはSUMO走行数ではない。既存cache以外の保存経路が不存在であることの網羅証明でもない。この3cacheから組めないという結果であり、入力を補完してID数を水増ししていない。

B_PLAN_RUN_LINKSにはfamily/config/problem/rep、PCG64 SeedSequence entropyと生成state4、seed規則source hash、元計画source hashを保持。代表12問題のmirror600測定行は保存streamと照合した。Grover/activeは保存source規則でseedを識別し、再測定していない。

古典初期経路460参照はB_CLASSICAL_BASELINE_LINKSとして別保存。すべて4,987組の既存候補へ対応し、独立の460走行を加算しない。主36,800参照から古典参照を差し引かない。

## 4. 完全識別子と環境

RUN_INPUTS.jsonlのpayloadをUTF-8・keyソート・compact JSON・NaN禁止で直列化し、SHA256をrun IDにする。series/input hash、車両属性、vType hash、道路hashとedge列、全stop設定、交通需要/seed、step/FCD/end/teleport等設定、実行環境hash、adapter/ルータ版hashを含む。環境ENVIRONMENTはSUMO1.24、専用fork、libsumocpp、lddで解決した依存library bytes、OS/kernel/arch、Python、関連環境変数を記録。

環境を現在のbytesで固定したことと、旧結果を同一環境で再生成したことは別。専用forkのclean build/一般受入はHOLD。vTypeはlegacy delivery既定で対象EVの実車校正ではない。材料質量を速度力学へ追加していない。走行後Controlled-DCの質量条件は別エネルギーkeyであり、B_ENERGY_INPUT_CONTRACTに明示採用待ちとして保存した。

全runの再hash・materialized XML照合は別readbackで検証。355個の完全入力（A303+機構15+B37）には1件単位のexecution list/argv案もEXECUTION_RECIPESへ具体化したがallow_execution=falseであり、専用forkの固定/tmp出力やclean build/計測契約の受入前には起動しない。完全payloadがあっても過去の道路幾何FAILと受入HOLDは消えない。入出力の詳細はJSONL/CSV、SOURCE_FILES.json、INDEPENDENT_CHECKSを参照。
''')
 report('SIMULATION_EVENT_CONTRACT.md','''
# 道路・車両・配送イベント契約

## 1. 道路と実行ゲート

正式保存網はSHA256 `460554c7716fe5e3e1410bbee790e69745a2c423146bac88e51e3a2b95f051b2`。今回ストリーム読取りで468,439laneと582,202種類のedge接続対を検査した。後者は重複を集約した対数で、既存auditの598,016 connection行数とは違う。完全A/B候補のedge接続・配送車通行可lane・stop位置範囲/順序は検査範囲PASS。未確定Bは既知のstop等だけを検査し、経路到達をPASSにしない。

保存幾何監査では>1m gap563,513、最大97.033728m、lefthand指定欠落、全保存軌跡の座標不連続留保がある。今回はhashと監査記録を引き継ぎ、全幾何差を再計算していない。修正候補は静的改善後も動的安全・待ち・需要処理等を同時に受入できず不採用。旧網や修正網を合成網の単体試験成功で受入へ昇格させない。

**地域網の代表試行ゲートはNO-GO**。Aは道路/環境/作業完了受入、Bは加えて経路不足が影響する。別網を採用するなら新しい版・端点mapping・OD・参照目的値・経路来歴が必要で、旧OD/最適値の自動転用は禁止。本作業で道路を修正していない。

## 2. 動作条件

候補はisolated single delivery vehicle、背景交通なし、seed20260930、step/FCD1秒、time-to-teleport=-1、既定collision.action=warnをbinaryで固定、基本end86400秒。Aは既存の各capも照合。異常警告を抑えて成功扱いしない。対象EVの動特性・積載校正とは別のlegacy配送車モデルである。

Aのstopはduration102と既存absolute untilを保持。Bはduration102だけでuntilを省略。SUMOのstop終了は、stop開始からのdurationとuntil等の制約を満たす時刻であり、業務の作業完了を直接観測したものではない。早着待機と作業102秒を明示分離する。

## 3. イベント辞書

|イベント|記録と意味|欠測・留保|
|---|---|---|
|配送地点到着|実地点への物理到着は独立観測欄|native stop startedから同一時刻を補作しない。離散FCDは通過区間の証拠に限定|
|停車開始|stopinfo.started|道路上のstop到達であり建物内作業開始とは別|
|作業開始|モデルではmax(stop started,ready)。Bはreadyなし|MODEL列で明示。実作業観測は別欄|
|作業完了|モデル開始+102秒|stop endedと無条件に等置しない。候補と実測を分離|
|停車終了|stopinfo.ended|until等による追加保持を別列に保存|
|走行再開|stop ended以降の最初の正速度FCD|1秒観測の再開指標。停車終了と同時とは限らない|
|デポ帰着|tripinfo.arrivalと最終端点/route終了の対応|未帰着arrival=-1、単なるtime cap到達、undepartedを区別|
|未完了|完全な観測期間で未出発/未完了を確認|需要集合に残す|
|記録欠測|出力欠損/途中破損/観測打切り|INDETERMINATE。未配達確定と混ぜない|

Aの期限はD03=due_start+serviceを保持。等号を期限内とし、判定用の許容時間を加えない。単位は秒、102秒を分へ誤変換しない。実測時刻と仮想policy時刻を別欄にする。Bに顧客期限や定時率を追加しない。

## 4. 完了・率の受入

ON_TIME/LATE/NOT_COMPLETED/INDETERMINATEを配送先ごとに保存する。PE主指標・件数副指標は固定需要を分母にし、未知があれば点推定はnull、確定定時/全需要を下限、未知を加えた値を上限とする。未取得14件も古典切替として需要を保持。

モデル正式版への移行には、研究上の作業開始/完了イベントの明示計測、native holdとの整合、4タスク/帰庫/失敗の完全観測、凍結deadline、道路・環境の適用範囲の受入が必要。実配送の完了率と呼ぶには実作業観測による妥当性確認も必要。今回の保存83runと合成試験はformal_outcome=HOLDのままである。

## 5. Controlled-DC入力契約

timestamp_s/speed_m_sの行順を保存し、有限・非負速度・同長1次元・2標本以上・厳密1秒間隔を必須とする。欠測/重複/並べ替え/補間/速度paddingを拒否。距離は右端速度×dtの和で、tripinfo.routeLengthとの自動一致を要求せず、計量境界と離散化を説明する。

W1転がり、W2空気抵抗、W3並進慣性、W4回転慣性61kgをJで求め、4成分合計後に正値化、η=.90で除し3600でWh。signed成分の合計は正値化後DCとは違う。回生なし・補機除外・平坦・既存Crr2条件・18000Wh stockを維持する。新3BやSOC制御へ置換しない。

走行質量と車両条件をエネルギーkeyに必須とし、材料を変えても同一速度・共通非パック質量の条件を守る。Bの科学比較質量はまだ正式に指定されていないためHOLDで、単体1200kgを主分析の採用値へ昇格させない。T08/T09の条件付き質量は前回証拠を保持する。

arrivalから最終標本までの未観測区間はgap秒とenergy=nullを残す。今回の合成試験では1秒gapがあり、停止補間や0Wh補完をしていない。出発までの非走行待機も走行軌跡へ合成追加しない。
''')
 report('UNIT_VALIDATION_REPORT.md',f'''
# 単体検証・独立readback結果

## 1. 実施と結果

test_contracts.py：**{unit['test_methods']}試験メソッド成功、失敗0・例外0**。内部に2,808政策のsubtestと多数の拒否ケースを含む。native単体：7実行・11assertion成功。独立readback：{ind['checks']:,}項目成功、失敗0。各件数は検証粒度が違うため合算して研究仮説の成功率にしない。

|対象|実施した検証|判定|
|---|---|---|
|政策|取得/未取得、期限等号、失敗判明、遅延、全2,808判断一致|PASS|
|イベント|102秒、早着待機、期限ちょうど/超過、stop終了との区別、未完了/欠測、不可能なhold拒否|PASS（モデル契約）。正式配送成果HOLD|
|率|未配達と未知を固定PE/件数分母へ残す、未知区間|PASS|
|識別子|JSON key順非依存、道路/車両/出発/stop/seed/環境変更でID変化、未確定拒否|PASS|
|入力|全参照keyと303/37完全入力の独立SHA、XML一致、追加機構15、stop順序・車種通行|PASS（検査範囲）|
|seed|代表12問題×5mirror×10seed=600保存streamと規則を照合|PASS、再測定なし|
|DC|凍結kernel/readerと別scalar、停止/加速/定速/減速、欠測・NaN・重複拒否、質量/Crr、終端null|PASS（条件付きモデル）|

原保存A stopinfoを新adapterに通した332タスクは前回候補完了値と一致した。A_SAVED_EVENT_READBACKに記録し、物理到着と実サービス観測の未取得を維持した。これは既存算術の理由なき全面再実行ではなく、新しいadapterの互換性検査である。

## 2. native小規模検証

新規の1000m・1edge合成網で、早着、120秒出発、240秒出発の遅着、until600による追加hold、同seed再現、異seed2件を実行した。正式地域網を変更したものではなく、standalone SUMOによる単体試験である。専用forkの地域再現性を認定しない。

earlyのモデル作業完了222秒とextra_holdのnative停車終了600秒は区別できた。同じseedの速度時系列hashは一致し、異seed3本はすべて異なった。入力・argv・プロセス終了・native出力・イベント・速度CSV・DCをNATIVE_UNIT配下と対応表に保存。

新生成7軌跡はstrict reader→凍結kernel→別scalarで接続し、DC差は各1e-7Wh以下。例earlyは129.395161187618Wh、観測距離998.889597542mに対しnative routeLength999m、最終標本からarrivalまで1秒。距離境界・離散化・終端未知を明記し、完全往復Whとしない。手計算fixture20.4410590184856Whも凍結kernelと一致した。

## 3. 検出した実装上の問題と対応

台帳構築途中、欠損区間を飛ばした既知経路片同士を連結判定し、派生的なLEG_STITCH_MISMATCHを付ける問題を検出した。欠損区間があれば全連結を未知として保留するよう新adapterを修正し、未知区間と真の非接続の回帰試験を追加した。元研究データは変更せず、最終台帳では不足区間として報告する。

同一edgeで後方のstopへ移る場合は同じedgeの次の出現を要求する検証も追加した。これらは新実装に対する修正であり、前回PASSや保存成果を都合よく変更したものではない。

道路幾何FAIL・動的受入不成立、B経路不足、歴史環境同等性、実サービス意味、B主DC質量は未解消。単体検証成功によってHOLD/FAILを解除しない。
''')
 report('PILOT_EXECUTION_REPORT.md',f'''
# 代表試行の実施判定と実行資源

## 1. 地域代表試行

**A/B地域代表試行は0件。全件SUMOも0件。** 道路ゲート不成立のため未実行であり、失敗率0%と報告しない。wall/CPU/RSS/失敗率/地域seed反復数/全件工期はnull・未計測。PILOT_EXECUTION_STATUS.csvに全候補をNOT_EXECUTED_GATE_BLOCKEDとして保存した。

AはD12の固定10候補を保持。出発0/正遅延、経路変更、未取得切替を含むが、地域上の実行はしていない。期限等号・超過等は純粋fixtureと合成nativeで検査し、期限を変更して地域の成功ケースを作らない。

BはR0_001、R1_001、R2_001、R3_001/040/078、R4_001/040/078、R5_001/036/070の12問題。主計画960参照は192入力経路組、完全に道路edgeを組めるものは0。古典12参照も既存候補に対応し、合計972参照。完全入力の37件へ都合よく代表を差し替えていない。

## 2. 合成単体実行の実測（地域試行と別）

|指標|7件合成native単体|
|---|---:|
|プロセスwall範囲|{min(walls):.6f}〜{max(walls):.6f}秒|
|プロセスCPU範囲|{min(cpus):.6f}〜{max(cpus):.6f}秒|
|最大RSS|{max(rss):,} bytes|
|実行失敗|0/7|
|観測衝突/teleport|0 / 0|
|同seed同速度時系列|一致|
|異seed速度時系列|3本中3種類|

各実行のwait4 rusageでCPU/maxRSS、monotonicでwallを記録した。wallは10ms pollの待ちを含み、この小さな値を精密な性能benchmarkにしない。入力ID、終了理由、seed、帰着、FCD/stop、欠測、W1〜W4/DC、独立照合はJSON/CSVに保存。1edgeの値を大規模地域網へ外挿しない。

単独車両・背景交通なしでも、既定speedDeviation/driver randomnessによりseedで変わる合成証拠が得られた。正式fork/地域で同じ変動量が生じることや必要反復数は未確認。交通反復を不要と断定せず、将来代表で同seed再現＋異3seedを確認し、推定誤差目標と依存構造から反復数を事前固定する。

## 3. 計算資源・工期の扱い

台帳構築は今回wall {summary['builder_wall_s']:.3f}秒、CPU {summary['builder_CPU_s']:.3f}秒、最大RSS {summary['builder_max_RSS_bytes']:,}bytes。これは入力の静的処理で、SUMOの1件資源ではない。必要区間219,211要求を新規routerで解く費用も未計測。全件走行の工期・金額の数値見積りはHOLD。

ゲート解消後はscale別の固有入力N_s、実測処理時間t_s、反復r_s、失敗再試行上限k_s、出力容量d_sを測定し、ΣN_s r_s t_s と並列数・I/Oを使って工期幅を算出する。同時worker数は実測RSS×workerとreserveの範囲で固定する。旧実験のwallや合成32〜35MBを地域網の予算として採用しない。

A政策は303r走行、機構までのunionは318rが基本枠（再利用0の現判定）。Bは37確定＋4,950未確定候補で、全件Nそのものが未確定。未完了・再試行、各seedを独立問題に数える誤り、費用未確認の展開を避ける。ここで見積不能を0秒・0円と補完しない。
''')
 report('SERIES_C_EVIDENCE_STATUS.md',f'''
# 系列C：既存証拠の状態を維持

新材料改善・完成パック質量を仮定した実験は行っていない。前回C_RECALCULATEDとSOURCE台帳のSHAを引き継ぎ、全材料/DC感度の再計算はしていない。今回の合成DC単体は実装互換性であり、T09の未知部材を埋める証拠ではない。

|接続|保存・監査済み値|状態|
|---|---|---|
|材料入力|LP q_ref171.875、S200195.959596Ah/kg、利用率1・全電池平均電圧3.5V等の条件|CONDITIONAL。量子計算達成値ではない|
|T08簡略会計|LP96.1456547987kg、S20090.6973573836kg、差{c['delta_T08_kg']:.12f}kg|算術PASS、工学CONDITIONAL|
|T09固定担持の既知差|9.722608121108kg|CONDITIONAL、既知部材比較のみ|
|T09固定面積の既知差|5.977891152149kg|CONDITIONAL、設計条件固定|
|未知部材差|δ=M_unknown,S−M_unknown,LP|HOLD、nullを0にしない|
|T09完成パック|183/183未確定|HOLD|
|同一stack全面対向|元CSV184行の不適合1行|FAILを維持|
|固定軌跡DC|460hash、25,760感度、下側Crr総量加重0.412579010061%（T08）|算術PASS、旧軌跡/モデルCONDITIONAL|
|量子材料解析→対象性能改善|未実証|HOLD|

相殺はb−δ=0、軽量はδ<b、逆転はδ>b。bは上記の既知部材差で、完成パックの実差ではない。同一速度・共通非パック質量・保存質量領域のDC増加条件でのみ、質量の符号をDCへ伝達できる。回生/補機/SOCや速度変化を追加した主指標に変えない。

追加SUMO不要：材料算術の記述、未知δの相殺/逆転境界、保存軌跡の限定scalar照合、部材来歴整理、条件付き結果/考察。新工学データが必要：対象LP/Sの実密度・空隙・厚さ/担持/面積・膜/液/Li、全電池電圧と利用率、外装/冷却/BMS、出力・熱・寿命・安全、量子由来改善の対照証拠。

追加SUMOが必要になり得るのは、A/Bの別経路へ質量感度を交差させる別版分析や、道路を変更した場合の新速度軌跡だけ。現時点では計画せず、既存Cを完成させる前提にしない。旧B0/B1/B2を材料主入力として復活させていない。
''')
 report('FULL_RUN_GO_NO_GO.md',f'''
# 全件走行GO/NO-GO — 作業停止判定

本作業は台帳・単体・ゲート判定まで実施し、全件SUMOへ進まず停止する。改善ゼロ・悪化でも説明/追跡できれば受入対象。単体の成功を道路/現実妥当性の成功としない。

|系列|今回確認できた範囲|次の限定作業|全件/科学的主張|
|---|---|---|---|
|A|303政策完全入力、2,808対応、追加15機構入力、単体/保存event互換|CONDITIONAL GO：環境/サービス計測・道路受入の解消|**NO-GO**：道路FAIL、正式完了/歴史環境HOLD。新規政策303、機構union318がゲート解消後の必要数|
|B|36,800参照、4,987組、完全37、未確定4,950、全対応|CONDITIONAL GO：経路回復・入力/質量条件確定|**NO-GO**：道路FAIL、代表全12の経路不足、科学比較質量/地域資源未確定。新規必要総数未確定|
|C|監査済み条件付き材料/質量/DC境界を保持|**CONDITIONAL GO**：既存証拠整理、工学資料回収|完成パック・量子材料改善・実EV効果の確定は**NO-GO**。新SUMOは不要|

## 判定の内訳

PASS：参照の全件対応/未確定明示、完全入力の決定論的SHA、既知経路・stop・通行の静的検査、単体{unit['test_methods']}件、native合成7件、独立readback{ind['checks']:,}項目、凍結DC互換。CONDITIONAL：legacy車両・旧道路に基づく内部入力と限定モデル、単体速度。HOLD：B不足区間、過去環境同等性/clean build、実作業完了、B科学比較質量、地域seed反復と計算費用。FAIL：保存道路幾何/修正候補の動的受入、T09全面対向1行を保持。

## 全件前に必要な意思決定

1. 道路の扱い：不採用修正候補を成功扱いしない。別版の受入済み網を用意する場合、mapping/OD/参照値を再構築する範囲を定める。旧網の診断だけを続けるなら別目的・制限を明示したprotocol改訂が必要で、今回のゲートを黙って緩めない。
2. Bの位置付き経路219,211要求を、追加の保存cache回収で満たすか、道路受入後に新規routerで構築するか決める。後者は別出力・source/seed/hashと資源試行を伴う。4,950未確定組を走行数と断定しない。
3. Aの作業開始/完了を計測するmodel契約と正式受入、既存83基準の再利用要件を定める。現判定は再利用0なので、220追加だけで済むとは計画しない。
4. Bの共通Controlled-DC走行質量を明示採用する。単体1200kgや未完成T09パックを無断転用しない。物理速度のlegacy vType質量と、保存軌跡を評価するDC質量を分ける。
5. 固定代表12問題を維持した地域native試行の後、scale別wall/CPU/RSS/失敗/出力量とseed変動から反復数・並列数・費用/工期上限を固定する。現時点の地域見積りはHOLD。

## 再実行入口と成果

新領域のbuild_run_ledger.py→test_contracts.py→native_unit_validation.py（合成網だけ）→validate_outputs.py→write_execution_recipes.py（起動しない）→write_reports.py。保存研究runnerを呼ばず、凍結出力へ書き込まない。再実行は新しいコピーで行う。PILOT_EXECUTION_STATUSは代表未実行を記録し、NATIVE_UNITの7実行と混同しない。

今回の停止条件を満たした：全参照は完全入力または明示UNBOUNDへ対応。単体・DC互換と失敗拒否を検証。未受入範囲の代表/全件は実行せず、未計測資源を数値で埋めていない。T09と道路のFAIL、材料量子寄与未実証、A正遅延地域成果未取得を保持した。
''')
 # Protect all read old inputs and the entire previous review; exclude changing new artifacts.
 allsources={}
 for n in ['MANIFEST_SOURCE_FILES.json','UNIT_SOURCE_FILES.json','NATIVE_UNIT_SOURCE_FILES.json','VALIDATION_SOURCE_FILES.json','RECIPE_SOURCE_FILES.json']:
  for x in read(O/n):
   if not Path(x['path']).is_relative_to(O):allsources[x['path']]=x
 for k,x in SOURCES.items():
  if not Path(k).is_relative_to(O):allsources[k]=x
 changed=[p for p,x in allsources.items() if sha(Path(p))!=x['sha256']]
 write('SOURCE_FILES.json',list(allsources.values()))
 status={'protected_sources':len(allsources),'changed_sources':changed,'previous_review_hashes':'PASS_35_ARTIFACTS','tracked_diff':subprocess.check_output(['git','diff','--stat'],cwd=R,text=True),'git_status':subprocess.check_output(['git','status','--short'],cwd=R,text=True),'regional_pilot_runs':0,'full_SUMO_runs':0,'synthetic_native_unit_runs':7,'prior_arithmetic_full_rerun':False}
 write('FINAL_PRESERVATION.json',status)
 if changed or status['tracked_diff']:raise RuntimeError('Protected input mutation')
 artifacts=[]
 for p in sorted(O.rglob('*')):
  if p.is_file() and p.name!='ARTIFACT_MANIFEST.json':artifacts.append({'path':str(p.relative_to(O)),'bytes':p.stat().st_size,'sha256':sha(p)})
 write('ARTIFACT_MANIFEST.json',artifacts);print(canon(status))
if __name__=='__main__':main()
