"""Render review documents from evidence, never alter historical artifacts."""
from evidence import *
def doc(name,s):(O/name).write_text(s.strip()+'\n')
def main():
 base=read(O/'BASELINE_RECONFIRMATION.json');net=read(O/'NETWORK_DIAGNOSIS_SUMMARY.json');route=read(O/'ROUTE_RECOVERY_SUMMARY.json');rec=read(O/'FINAL_RECOVERY_REVIEW.json');unit=read(O/'MEASUREMENT_VALIDATION_SUMMARY.json');final=read(O/'FINAL_REVIEW.json');miss=read(O/'MISSING_FEASIBILITY_SUMMARY.json');sup=read(O/'NETWORK_SUPPLEMENT_SUMMARY.json')
 for p in [P1/'B_PLAN_REFERENCES.csv',P1/'independent_audit.py',P2/'build_run_ledger.py',U/'docs/research/CPX01_D10_ADOPTION_DECISION_20261017.md',U/'review_outputs/causal_engineering_audit_20261027/run01/verify_a.py',B/SC/'sumo_od_full_baseline_20261001/full_run.py',R/'01_research_design/methodology/CONTROLLED_MASS_TO_DC_MODEL_FREEZE.json']:use(p)
 def ref(p):
  p=use(p);return f'`{p}` — SHA256 `{SOURCES[str(p)]["sha256"]}`'
 doc('00_SOURCE_AND_PROVENANCE.md',f'''
# 道路・経路・計測契約の独立レビュー — 2026-11-02

判定：A・Bの地域代表試行はともに **NO-GO**。今回の成果は静的診断、保存元経路の回収、モデル計測契約、算術単体検証である。新規SUMO/native実行0、経路探索0、地域代表試行0、全件実行0、QAOA再学習0。N2道路網は作成していない。

## 版と保全

HEAD `{base['HEAD']}`。開始時と終了時のtracked差分は空。前2レビューの成果物875件を開始時に照合し、不一致0。終了時は `FINAL_SOURCE_HASH_CHECK.csv` の{final['source_files_rehashed']:,}ファイルを再ハッシュし、不一致{final['source_hash_failures']}。`GIT_DIFF_FINAL.patch`、`GIT_STATUS_FINAL.txt` に最終状態を保存した。検査対象外の全バックアップについて変更なしを証明したとの主張ではない。

実体の所在を区別する。

|略号|所在|取扱い|
|---|---|---|
|R|`{R}`|現在の作業木。Git追跡状態はgit statusと照合|
|U|`{U}`|外部の未追跡保全コピー。公開Gitに含まれると扱わない|
|B|`{B}`|外部保存用バックアップ|
|L|`{L}`|移設保全領域|

全参照元・実装・入力のSHA256、所在区分、旧期待ハッシュは `COMBINED_SOURCE_FILES.csv`。新規生成物は `ARTIFACT_MANIFEST.json`。行証拠にsource_path/SHAまたはpartition/rowがある場合、この台帳と結合する。

## 旧状態の再確認

|項目|旧報告|今回のreadback|差異|
|---|---:|---:|---|
|A運用判断／政策候補|2,808／303|2,808／303|なし|
|A機構追加／union|15／318|15／318|なし|
|B参照／候補|36,800／4,987|36,800／4,987|なし|
|B既知完全／不足|37／4,950|37／4,950|なし|
|B位置付き区間要求|219,211|219,211|なし|
|前回単体／readback／合成native|26／6,605／7|26／6,605／7|なし・再実行せず|
|受入済み既存A/B走行|0／0|0／0|道路受入不成立を保持|

今回の2,323元OD回収候補は新発見の保存証拠であり、旧37という当時の台帳値を誤りとして置換しない。2つの旧既知入力について元OD同一性を保留したことも明示する。

## 主要生成経路

1. A：D10採用判断→D11 `operations_2808.csv`・`logical_candidates.csv`→前回 `A_OPERATION_RUN_LINKS.csv`、303政策＋15機構入力。政策・仮想利用可能時刻・出発を変更していない。
2. B：staged 3familyの `ALL_SEEDS.csv`＋460入力NPZ／MANIFEST→初回 `independent_audit.py` が8設定・OPTIMIZED・rep0…9を抽出→`B_PLAN_REFERENCES.csv`→前回 `build_run_ledger.py` が4,987候補、219,211不足区間、37既知入力を保存。
3. 今回：NPZのnodes/partition/travel/distance→`CHECKPOINT_ROWS.json`／`ROUTE_NUMERIC_PARTITIONS.json`→元parquet行→保存 `lane_feasible_routes.rou.xml`／補正・loop記録→ `RECOVERED_OD_LEGS.jsonl.gz`→新しい全B経路payload。既存の全B走行結果を発見したという意味ではない。
4. 道路：run2→外部lane端点・長さの変更→N0。N1はrun2への復帰、左側通行再構築、局所・信号補修を含むB6。差分と保存nativeイベントを独立readback。
5. 計測：凍結DC＋SUMO公式資料／1.24.0ソース→今回の `measurement_contract.py`＋別算術→35fixture。既存FREEZE変更なし。

主要起点：

- {ref(P1/'B_PLAN_REFERENCES.csv')}
- {ref(P1/'independent_audit.py')}
- {ref(P2/'build_run_ledger.py')}
- {ref(U/'docs/research/CPX01_D10_ADOPTION_DECISION_20261017.md')}
- {ref(R/'01_research_design/methodology/CONTROLLED_MASS_TO_DC_MODEL_FREEZE.json')}

## 再実行入口

すべて今回のレビュー領域のみへ出力する。Python/pyarrowは既存 `.conda/bin/python`、pyarrow19.0.1。依存関係追加なし。前2レビューが必要な外部保全データを含むため、公開Git単独で完全再現できるとは判定しない。

```bash
.conda/bin/python -B review_outputs/network_route_contract_20261102/run01/evidence.py
.conda/bin/python -B review_outputs/network_route_contract_20261102/run01/recover_routes.py
.conda/bin/python -B review_outputs/network_route_contract_20261102/run01/review_recovery.py
.conda/bin/python -B review_outputs/network_route_contract_20261102/run01/diagnose_network.py
.conda/bin/python -B review_outputs/network_route_contract_20261102/run01/network_supplement.py
.conda/bin/python -B review_outputs/network_route_contract_20261102/run01/missing_feasibility.py
.conda/bin/python -B review_outputs/network_route_contract_20261102/run01/validate_measurements.py
.conda/bin/python -B review_outputs/network_route_contract_20261102/run01/final_review.py
.conda/bin/python -B review_outputs/network_route_contract_20261102/run01/write_reports.py
.conda/bin/python -B review_outputs/network_route_contract_20261102/run01/seal_artifacts.py
```

出力先が既にある再実行では今回の診断出力を更新するため、第三者はレビュー一式を別ディレクトリへ複製し、保全先をread-onlyにして実行する。元の科学runnerは実行しない。`final_review.py` は集計コードの数値転記でなく、参照結合・payloadハッシュ・道路接続・stop順・保全を別手順で検査する。

## 修正と残存状態

独立レビューで134制御区間のうち欠落1行が中間台帳から落ちていたため、HOLD行を復帰。133PASS＋1HOLDを正式分母とした。修正前コード・CSV、差分、再検証は `revisions/`。経路回収の初回は同一大ファイルの反復ハッシュで遅くなり中断し、キャッシュ化後に実行完了した。初回ログを保持。計算式・元データの改変なし。

Cは前回の条件付き成果を継承：T08差5.448297415kg、下側Crrの総量加重削減0.412579010%、T09完成パック183行HOLD、全面対向1行FAIL、未知部材相殺境界、量子材料改善未実証。新しい材料値・完成質量を設定せず、旧B0/B1/B2を材料主入力へ復活させていない。
''')
 doc('01_NETWORK_ROOT_CAUSE.md',f'''
# 道路不適合の原因と影響

## N0：正式保存網 — FAIL

実体 `{net['N0']['path']}`、SHA256 `{net['N0']['sha256']}`。XML version1.20はネットワーク形式であり、実行SUMO版とは別。保存command・config・binary台帳はSUMO1.24.0系を使用。完全な元OSMからの再生成は未検証。

外部laneの端点をjunction中心へ延長し長さも更新する `repair_network_geometry_lengths.py` が、内部laneの接続幾何を保ったまま適用された。XML接続IDが存在することと幾何連続は別である。config snapshotの長さ維持という説明と実際の長さ更新に来歴不一致があり、`MAX_GAP_ROOT_CAUSE_CASE.json` と保存変換report／実装を優先して記録した（完全再生成HOLD）。

独立に全468,439lane／598,016connectionを検査。接続primitiveの端点距離>1mは **563,513件**、52,603junctionに分布、最大 **97.0337281568m**。同一connectionから複数primitiveが生じるためconnection行数と同一の分母ではない。欠落lane参照0は接続の形式検査PASSに限る。

最大例：junction`448039303`、内部lane`:448039303_2_0`終端 `(14066.14,5435.71)` と外部lane`38093006_0`始端 `(14146.84,5381.83)`。run2では同じ位置で連続していた。N0の当該外部lane長158.816254m、旧run2長61.67m。原始記録510027を `N0_GAP_PRIMITIVES.csv.gz` で追跡できる。全件のfrom/next/to lane・junction・gapを保存した。

単なる表示差とは判定できない。保存AのPID`{sup['known_trace_PID']}`の軌跡で、1秒のXY移動弦長が速度×dtより1m以上長い区間を25件、最大超過25.752048m確認した (`SAVED_TRACE_DISCONTINUITY_READBACK.csv`)。これだけでnative速度が全件誤りとは言えないが、実空間で妥当な走行の受入証拠にはならない。

既存の完全入力A303＋追加15＋B37の全355経路、今回回収B2,323全経路に、外部経路と直接対応する不良primitiveが存在。各candidate/run/問題IDと影響junction数は `SAVED_RUN_NETWORK_EXPOSURE.csv`、`RECOVERED_B_NETWORK_EXPOSURE.csv`。これは全経路が衝突したという判定ではない。未回収Bの経路は検査不能HOLD。保存ODの算術的整合と地域道路としての妥当性を区別する。

## N1：既存B6候補 — 動的FAIL

実体 `{net['N1']['path']}`、SHA256 `{net['N1']['sha256']}`。N0の単純な表示修正ではない。lefthandを明示し、外部形状・長さ、内部接続・信号を広く変更している。`NETWORK_ELEMENT_DIFF.csv.gz` は要素ID／変更前後内容ハッシュを保存。内部ID再採番があるので、同じ内部IDを同じmovementと決めつけない。

|要素|追加|変更|削除|
|---|---:|---:|---:|
|edge|5,703|53,839|973|
|lane|6,606|462,475|4,535|
|junction|2,357|99,127|286|
|connection|198,670|331,713|196,599|
|tlLogic|0|1,257|0|

幾何端点gap>1mは0、最大0.610328mで、この静的閾値のみPASS。完全な交差部安全性の証明ではない。保存native記録183件について、車体の前後端・幅から別の分離軸検査を行い、183/183で車体矩形の重なりを確認した。独立事故数や人身事故の実測値ではない。

|保存イベント原因|件数|
|---|---:|
|下流赤・queueにより内部lane内停止|150|
|短い下流出力の後部がjunctionを占有|2|
|上記占有からの内部foe閉塞連鎖|28|
|移動車両の残存クリアランス重なり|3|

TLSは `1063596961,1883302384,1910535633,256367939,8917306614` の5箇所、方向付きlink対8、順序を除くmovement対7。局所の信号・内部停止・車体占有が相互作用し、処理能力にも波及する。位置・車両・lane・時刻・sourceは `COLLISION_EVENT_CAUSES.csv`／`COLLISION_LANE_RECONSTRUCTION.csv`／`COLLISION_BODY_OVERLAP_INDEPENDENT.csv`。

runtime guardではcollision record183→0となるが、scheduled19,775に対してarrived9,181→8,584、異常停止388→410。保存最大phase保持3,411.5秒で、green配分・待ち・需要処理を同時に受入できない。XML requestのみの修正でもload90で43件残存。collisionを0にするだけでは採用条件を満たさない。

## 最小再現と限界

保存最小probeは予定540車両、最初の`probe:001`は940.5秒、TLS`256367939`、link11/6、lane`:256367939_11_0`／`:256367939_18_0`、被衝突側停止。`MINIMAL_REPLAY_EVIDENCE.json` に保存済みコマンド・binarySHA・入力hash・時刻整合を収録。保存observer replayは183イベントのsignatureを再現した。540車両probeが数学的な最小入力とは証明していない。2台へ縮小したwitnessはHOLD。

今回native再現0。原記録と独立幾何readbackで不採用を判断できるため再実行は不要。将来の局所診断は対象TLS・入力SHA・目的・件数を先に固定し、最大10回、各wall120秒でtimeout、超過時HOLD停止。保存コマンドを出力先そのままで実行しない。地域代表12問題へ拡大しない。

再検証入口：`diagnose_network.py`、`network_supplement.py`。出典SHAは `NETWORK_SOURCES.json`／`NETWORK_SUPPLEMENT_SOURCES.json`。新たなnative値を推定・補完していない。
''')
 doc('02_NETWORK_ADOPTION_DECISION.md','''
# 道路網の採用判断

今回、地域実験へ採用できる道路網は確定していない。道路選択はHOLD、地域代表試行はNO-GO。保存N0は歴史的計算結果の参照先として保持する。

|項目|N0：正式保存網|N1：B6修正候補|N2：新規別版|
|---|---|---|---|
|幾何受入|FAIL：563,513不良primitive|CONDITIONAL：>1mは0、安全性とは別|HOLD：未構築|
|接続性|PASS：既知入力の形式接続検査。欠落BはHOLD|HOLD：旧経路・全ODの同等性未証明|HOLD|
|車両通行|CONDITIONAL：配送車許可を静的screen|HOLD：新mapping／lane経路の再受入が必要|HOLD|
|停車成立|HOLD：保存位置と形式的範囲のみ|FAIL：使用端点958件が範囲外|HOLD|
|動的受入|FAIL：幾何と保存軌跡の留保|FAIL：車体重なり・guardの待ち／需要処理不適合|HOLD|
|既存ODとの整合|PASS：同一hash下の元数値。現実妥当性は別|FAIL：旧位置の直接転用。新OD数値一致はHOLD|HOLD：別版として検証必要|
|既存QAOA結果との整合|CONDITIONAL：旧数理問題内の結果|HOLD：旧目的値・gapの転用不可|HOLD|
|追加計算|不適合修正か受入不能条件の研究上の限定が必要|全mapping・OD・参照値と政策の再評価|全来歴と再計算範囲の固定から必要|
|採用|NO-GO|NO-GO|HOLD／未構築|

## 比較可能性の独立screen

使用ORIGIN/DESTINATIONのrole付き端点6,670件で、N1にlane欠落0だが958件の旧offsetが新lane長を超える。範囲内でも5,700件が0.1mを超えて座標移動する (`ENDPOINT_REUSE_N0_N1.csv`)。同一点へのアクセスを保持したとは言えない。投影位置は宣言lane長に沿った形状内挿の診断で、実建物へのアクセス検証ではない。

保存355経路すべてで、固定edge列・lane0の長さ／自由走行時間proxyが変わる (`SAVED_RUN_NETWORK_EXPOSURE.csv`)。このproxyは新native ODや新しい最短値ではない。proxy差を新OD差と報告しない。それでも旧offset無効と長さ変更により自動転用を禁止する根拠となる。

## N2の実装仕様と再計算範囲

N0の外部端点だけを内部laneへ接続し直す簡単な補修は、既存の長さ・停車・費用定義を変える。N1でも広域再構築と信号変更が必要だったため、採用条件を満たす最小変更が見つかったとは主張しない。N2のID・SHAは未発行。候補を作るなら以下を別の研究版として固定する。

1. 基準OSM／端点／SUMO netconvert・forkを固定し、lefthand、形状、長さ、交差部内部形状を一貫して構築。変更要素・理由・before/after hashを保存。
2. 全使用地点のlane・positionを再mappingし、通行方向・vClass・停車範囲を静的検証。旧位置をclampして成功扱いしない。
3. 5TLSの局所混雑／停止／クリアランス診断を別版で行い、collision／teleport／経路不達0、停車成立、事前固定需要処理・待ち・信号配分条件を同時に満たす。衝突無視・無制限guardは不可。
4. 旧／新の全対応OD時間・距離と経路を比較。選ばれた計画の区間だけでなく、最適化に利用する全行列要素を対象とする。B460入力とA78の影響範囲を台帳化する。
5. 値が変わる場合、古典初期経路・厳密最適値またはbound・gap分母・QAOA目的値の妥当性を再評価。再学習等が必要な範囲を新PROTOCOLで定める。旧QAOA訪問順を固定して新道路へ流す場合は「旧計画の新網replay」と明示し、新条件で最適化した量子結果と呼ばない。
6. D10/D11の時刻政策を維持する場合も、新経路の配送イベント・採用政策の評価対象・需要を明示。旧ODによる配送成果を新網実測へ混ぜない。

本段階は再計算範囲の確定までで、大規模OD再生成・最適化・科学走行は実施していない。保存網のFAILを解消する証拠がないまま地域試行に進めない。
''')
 coverage=rows(O/'B_FINAL_COVERAGE.csv');scales='\n'.join(f"|{x['group']}|{x['references']}|{x['original_OD_identity_covered']}|{float(x['original_coverage_percent']):.6f}%|" for x in coverage if x['dimension']=='scale')
 doc('03_B_ROUTE_RECOVERY_FEASIBILITY.md',f'''
# Bの区間経路回復可能性

状態：元OD edge列の保存回収は部分的PASS、未保存区間の完全復元はHOLD、地域実行はBLOCKED_BY_NETWORK。新たな最短経路探索・SUMO実行をしていない。

## 不足項目の分解と回復

|項目|前回状態|今回の確認|
|---|---|---|
|物理入力・訪問順|460入力、4,987候補で既知|全候補を元NPZ／8設定36,800参照へ対応|
|出発・車両・交通・環境|前回payload契約で固定|出発0、単車、背景交通なし、seed20260930、102秒、untilなしを継承|
|stop edge/lane/position|既知|role付き端点同一、元parquetとの照合|
|各区間と帰庫のedge列|旧37候補のみ完全|173parquet群の元区間230,372キーを確認、217,123edge列回収、13,249未保存|
|道路版・OD数値|N0・保存parquetで既知|全230,372キーのNPZ時間・距離・端点・network一致。不一致0|
|探索規則・router|保存manifest・binaryあり|旧baselineとlane修正規則を区別。欠落16partitionは旧schemaでlane-mode/source-hash列なし|
|道路受入|FAIL|全候補BLOCKED_BY_NETWORK、受入既存結果0|

元parquetはNPZのpartition番号から特定。157群に保存bulk route XMLがあり、残り16群ではprovenance／loop／PAIR_CORRECTIONSを追跡した。`R<row_index>`と始終端、edge数、full cost、OD数値、network SHAを照合する。保存値を別探索値で置換しない。

旧219,211位置付き要求は、不足候補から抽出された端点・位置・道路・車種・router・seed付きキーであり、独立再構成でも重複0。全候補の230,372元ODキーは別の母集団・単位で、差を欠損や実行数に読み替えない。新たな219,211回の経路計算は行っていない。

## 回収結果とID

|排他的分類|候補数|意味|
|---|---:|---|
|ORIGINAL_RECOVERED|2,323|全元OD区間edge列を保存物から直接回収|
|EXACT_RECONSTRUCTED|0|欠落区間の同一再生成は未実施|
|ALTERNATIVE_RECONSTRUCTED|2|前回の固定leg cacheは完全だが元OD同一性HOLD。今回の新探索ではない|
|PARTIAL|2,662|一部の元OD区間が未保存|
|UNRECOVERABLE|0|永久復元不能と断定する証拠なし。未回復を成功へ昇格しない|

上の分類とは別のnetwork_status列で4,987全件をBLOCKED_BY_NETWORKとする。このため実行受入0。`B_FINAL_RECOVERY_CLASSIFICATION.csv` が正式な行台帳で、中間 `B_ROUTE_RECOVERY_STATUS.csv` のPARTIAL2,664には後述2旧cacheも含まれる。

2,323件は元OD脚を連結した**新しい全B経路payload**である。過去に全B経路がnativeで走った証拠ではない。`RECOVERED_OD_LEGS.jsonl.gz` に脚ごとの元source・SHA・parquet行・OD値を保存。`RECOVERED_RUN_INPUTS.jsonl` に全payloadと決定論的SHA IDを保存。訪問順だけでなく出発・道路・vType・stop・交通・環境・generatorを含む。未確定2,662件へ完全IDを発行していない。

元OD同一性が成立する完全入力の固有数2,323、旧cacheの2件を含む利用可能な構造入力union2,325。前回37から追加で2,288候補の構造が判明した。新generator採用に伴うID版の差は同一実走行数の増加を意味しない。新規B全走行結果0、受入済み0。将来必要な走行数は採用網・質量・不足復元を固定するまでHOLD。

## 37既知候補による同一性検証

35件で完全edge列・方向・stop順が旧cacheと一致。B-01993／R0_034、B-04253／R1_034は同じ元OD区間1本のedge列が未保存のため比較不能であり、差があるとも同一とも判定しない。元37の入力を削除せず、2件をALTERNATIVE_RECONSTRUCTEDへ明示した。

37制御に必要な固有OD脚134のうち、133で保存tripinfo.routeLengthと元OD距離が完全一致、残る1脚はHOLD。133だけを分母にしない。全回収対象のNPZ時間／距離は元parquet行と一致。**旅行時間は当時の静的OD重みで、今回の走行所要時間ではない**。単車隔離実行のrouteLengthとも区別する。新探索の距離・時間が近いことによる同一性判定は使っていない。

`KNOWN37_IDENTITY_COMPARISON.csv`、`KNOWN37_RAW_NATIVE_DISTANCE_CHECKS.csv`、`final_review.py` で照合可能。回収2,323payloadすべてで方向付きedge接続・delivery許可lane・stop順の独立静的screenも実施。これはnative lane変更・停車成立を保証しない。

## カバー率と偏り

元OD同一性カバー **24,333／36,800＝66.122283%**。旧2cacheを含む構造入力カバー24,493／36,800＝66.557065%。二つを混ぜない。

|規模|全参照|元OD同一性を満たす参照|カバー率|
|---|---:|---:|---:|
{scales}

設定別・測定rep別・460問題別の分母と分子は `B_FINAL_COVERAGE.csv`。config各4,600参照で、6設定3,040、GroverP2 3,048、GroverP3 3,045。欠落は大規模側に偏り、回収済みsubsetを460問題全体の効果へ一般化しない。測定repを独立物理標本として数えない。

事前固定12問題のうち7問題は80参照すべて回収済み、5問題（R3_078、R4_001、R4_078、R5_001、R5_070）は0。成功例へ恣意的に差し替えない (`PILOT_INPUT_RECOVERY_COVERAGE.csv`)。古典側12参照も独立に完全性を確認してから試行する。

## 残る復元と工数

13,249固有欠落OD区間／16partitionの全数値行は存在する。元baseline `full_run.py` は正常scratchを削除し、loopだけを保存するため、bulk edge列欠落を説明できる。保存原本の追加発見を先に行う。

元baseline実行manifestの保護入力2,942件はhash一致 (`OD_GENERATOR_PROTECTED_INPUTS.csv`)。後期lane-routerソースも保全されているが、欠落旧schemaにそのsource-hash欄がなく、このソースを元生成器とみなさない。原ルータbinary・費用・端点・seed・tie規則・loop補正を固定した小数制御脚で完全edge列を再生成し、37制御で同一性を検証してから不足を展開する。今回その再生成は未実施。決定性を推測してEXACT_RECONSTRUCTEDへ昇格していない。

元脚を再生成できてもN0道路受入FAILは残る。N1/N2で得る経路は新条件の代替であり元実験完全復元ではない。必要な計算時間は未実測のため全件工期HOLD。`missing_feasibility.py`、`MISSING_OD_GENERATOR_PROVENANCE.csv`、`B_UNRECOVERED_INTERVALS.csv` が具体的な入力・行・再生成対象である。
''')
 doc('04_DELIVERY_EVENT_CONTRACT.md','''
# 配送イベント契約 SERVICE102_V1

判定：**モデル定義と算術境界PASS、native継続監視・地域実装への接続HOLD**。正式に定義するのは「モデル上の配達完了」であり、実際の荷物引渡しではない。既存の候補指標や過去83走行を本契約受入済みへ昇格しない。

## 記録する時刻

|イベント|定義・証拠|
|---|---|
|物理的到着|独立観測された配送地点への到着。未観測ならnull|
|native停車開始a|stop-output.started。task ID、actType、stop順、lane・positionに結び付ける|
|モデル作業開始s|A=max(a,ready)、B=a|
|モデル作業完了c|s+102秒。ただし当該場所でcまで連続したnative停車を検証した場合だけ確定|
|native停車終了|stop-output.ended。車両が走行を再開する時刻|
|最初の正速度標本|native終了後のFCD/状態記録。1秒観測の別時刻|
|デポ帰着|tripinfo.arrival>=0、期待最終edge/lane/position・route完了と対応|

公式 [StopOutput](https://sumo.dlr.de/docs/Simulation/Output/StopOutput.html) と [v1.24.0保存資料](https://raw.githubusercontent.com/eclipse-sumo/sumo/v1_24_0/docs/web/docs/Simulation/Output/StopOutput.md) に照合。stop行は停車が終了した時に出力される。startedは停車開始、endedは走行再開であり、配達作業の観測ではない。未出力行だけで未配達とは断定できない。取得ページ・URL・hashは `official_sources/`。

[車両・stopの公式定義](https://sumo.dlr.de/docs/Definition_of_Vehicles,_Vehicle_Types,_and_Routes.html) のdurationは最低停車時間、untilは最も早い再開時刻。早着時に「readyまで待機＋その後102秒」を自動で意味するとは限らない。既存Aのduration102・absolute untilを保持し、実際の保持がモデル完了に足りるか検査する。不足ならFAILとして残す。

## 場所と連続性

予定laneと観測laneが一致し、観測停車位置が宣言startPos…endPos内であること。SUMO1.24.0ソースの既定startPosはmax(0,endPos−0.2m)。厳密なendPos一点一致は要求せず、根拠のない許容距離は追加しない。位置・lane違いをclampやfriendlyPosで補正しない。

1秒stepごとにtask対応、stop状態・位置・中断・teleport・collisionを記録し、s…cの区間が連続していることを確認する。stop-outputだけで完了しない停車を観測するため、active-stop ledgerを必須とする。実装はまだ既存native runnerへ接続しておらず、G4全体はHOLD。

## ケース別判定

|条件|処理|
|---|---|
|予定時刻／遅着|aを確認しsを計算、102秒の成立を確認してc確定|
|早着|Aのreadyまで待機を別記し、sから102秒連続停車を確認|
|停車がc以降も続く|cとendedを別時刻に保存。endedまで作業時間を延長しない|
|endedがなく、active ledgerがcまで証明|モデル完了を確定、native再開はnull|
|102秒の途中で終了|評価horizon時点のIN_PROGRESS。Aの期限がhorizonより後なら定時性INDETERMINATE、期限を過ぎた完了不足はNOT_COMPLETED。最終配送完了と観測打切りを分ける|
|c前に走行再開|サービス中断FAIL、NOT_COMPLETED。都合よく102秒を補完しない|
|場所が違う／task対応不明|FAILまたはHOLD、完了時刻null、INDETERMINATE|
|stop行欠落・出力破損|連続監視がなければHOLD／INDETERMINATE|
|到達不能・未出発／未サービスを完全に確認|NOT_COMPLETED、理由と観測期間を保存|
|完了後に帰庫不能|各taskの完了は保持しreturnは別FAIL。低DCを効率改善にしない|
|異常終了|既に証明したtaskのみ保持、残りは証拠に応じ未完了／未知。runは受入不可|

安全異常や位置不適合のあるrunは主比較から成功扱いしない。ただし台帳から消さず、不適合とtask状態を併記する。

## Aの期限・固定分母

D03期限=d_i=元NPZのdue_start_i+service_i、service=102秒。根拠は保存 `causal_engineering_audit_20261027/run01/verify_a.py` のNPZ読取り／D03式、行別 `A_NATIVE_TASK_COMPLETION.csv`、D10/D11採用記録。元のdue_startも別列で保存。D10/D11の36条件・未取得14の古典切替を変更しない。

ON_TIME iff 証明済みc_i≤d_i（等号を含み時間許容なし）、LATE iff 証明済みc_i>d_i。NOT_COMPLETED、INDETERMINATEを別保存。

主指標 F_PE=Σ(q_i×I[ON_TIME])/Σq_i、副指標 F_count=ΣI[ON_TIME]/|D|。Dは各問題で固定された全配送需要。未取得・未配達・未知で分母を縮小しない。未知がある点率はnullとし、PE下限=定時PE/全PE、上限=(定時PE+未知PE)/全PE。件数版も同じ上下限原理を使う。依存した36政策や測定seedを物理独立標本と数えない。

## Bと受入出力

`UNIFIED_NO_CUSTOMER_WINDOWS_V1`を維持。ready／顧客deadlineをAから追加しない。モデル完了・未完了・未知の件数と固定PE、帰庫時刻、観測境界を報告し、根拠のない定時率は計算しない。

必須出力：完全入力・binary/library環境hash、effective route／vType／stop XML、stop-output、active-stop ledger、FCD速度・時刻・lane・position、tripinfo（unfinished/undeparted含む）、collision／warning／teleport、exit理由・horizon・資源。sourceの欠損状態をtask別に保存する。作業イベントはMODEL、native時刻はOBSERVED_SIMULATION、実荷物引渡しは未観測と列で区別する。

実装入口 `measurement_contract.py:measure_service`、テスト `validate_measurements.py`。今回35fixture中18サービス境界＋固定分母等を保存 (`MEASUREMENT_TEST_CASES.csv`)。過去26単体・7合成nativeのPASSを保持するが、今回の追加契約をnativeで検証したとは主張しない。G4をPASSへ進めるには極小網でactive ledgerとnative出力の対応を検証し、その後に受入済み地域網へ接続する。
''')
 doc('05_COMMON_DC_SPECIFICATION.md','''
# Bの共通Controlled-DC仕様

凍結 `CONTROLLED_MASS_TO_DC_V1`を保持。入力契約・算術kernelはPASS、**現行Bの主比較質量はHOLD**。材料改善・回生・補機・SOC制御を主評価へ追加していない。

## 入力と積分

timestamp_s、speed_m_sは同長の1次元有限配列、2標本以上、速度非負、隣接差厳密1秒。native時刻順を保持し、並替え・補間・padding・重複時刻・欠測を拒否。時刻は当該車両の観測標本であり、出発待機を合成して付けない。軌跡SHA、run入力SHA、mass条件、freezeSHA、pressure条件で結果を識別する。

区間t−1→tについてv=v_t m/s、u=v_(t−1)、ds=v×1秒。加速度を使うなら(v−u)/1だが慣性仕事は隣接運動エネルギー差で厳密に計算する。

|項目|式・値|単位・出典|
|---|---|---|
|Crr|0.005+(0.01+0.0095×(3.6v/100)^2)/p|p=4.5または2.6barの2境界、freeze。中間値なし|
|W1|m×9.80665×Crr×ds|転がり仕事J|
|W2|0.5×1.2041×1.175×v²×ds|空気抵抗仕事J|
|W3|0.5×m×(v²−u²)|並進慣性J|
|W4|0.5×61×(v²−u²)|回転慣性J、61kgを質量条件で変更しない|
|区間DC|max(W1+W2+W3+W4,0)/(0.90×3600)|Wh、4成分の合計後に正値化|
|距離|Σv_t×1|m、右端速度離散化|

W1…4はsigned値をJまたはWhと明記して保存。成分別maxを加算したものやsigned仕事総和はDC総量ではない。平坦、grade0、accepted regen0、turnとauxは境界外null。CdA1.175m²・rho1.2041kg/m³・g9.80665m/s²・η0.90は凍結共通値で、対象車の実測校正ではない。パラメータ原資料・cacheSHAはFREEZEのsource_refs／input_hashesを保持する。

FCD速度積分距離とtripinfo.routeLengthは計量境界が異なるため、両方を保存し差を診断する。終端は最後の観測時刻までで止め、arrivalとの差をterminal_gap_s、未観測電力量をnullで保存。端の欠測を停止0Whで埋めない。主表はOBSERVED_WINDOW_CONTROLLED_DCで、完全帰庫DCと主張する場合は終端が観測された証拠が必要。未確定tailを含む全行程の厳密比較はHOLD。

stock18,000Whは研究上usable仮定の累積会計。negativeならFAIL flag、clampや速度変更なし。gross20,000Whと区別する。経路へのSOC制約や電池枯渇による運行可否を実証したモデルではない。

## B質量と比較可能性

凍結mass会計には旧B0車両1,100kg（pack111.111111kgを含む）＋driver55kg＝**1,155kg**、共通非pack988.888889kg、cargo0がある。これは由来のある候補だが、現行no-window Bの主質量として採用された記録は確認できない。したがって今回のB_main_mass_kgはnull。

候補B1=1,134.797980kg、B2=1,123.888889kgは旧比エネルギー感度であり、Bの主比較へ自動採用しない。T08の条件付きmassは別の材料比較、T09完成massは183行未確定。単体試験1,200kgはfixtureに限る。

216PEは配送需要・積載能力の単位で、kg対応なし。PE→kg換算0件、配達による荷重変化も凍結空荷controlでは未実装。積載を主分析に入れるなら原荷物kg・荷卸し規則・別版が必要。

次段階で現行Bの共通車両・pack含有・driver・cargo0等を正式に採用し、全方式へ同じmassを適用する必要がある。速度生成はlegacy配送vTypeで、材料massは走行動特性を変えず外部DCへだけ入力する条件付き比較である。背景交通なし、seed、道路・stop・出発はrun契約どおり。実EVの積載走行消費と同一視しない。

## 独立検算と主比較

`validate_measurements.py` は別スカラー式と凍結kernelを比較。定速・加速・減速・停止・再発進、同一入力再現、massのみ変更、欠測・NaN・重複・終端未観測を検査。Decimal手計算の10m/s×2秒例も保存。`DC_INDEPENDENT_FIXTURES.csv`、`MEASUREMENT_TEST_CASES.csv` に期待・実測・差を保存。35fixtureは35PASS／0FAILで、地域走行やmass実証ではない。

比較は固定全需要が両方式で完了、両方式が帰庫、観測境界同等、共通mass等が成立した場合のみ効率主比較を受入。未配達や経路不達で低Whになったrunは未完了として保持し、効率改善へ数えない。C−Q Whと個別率平均、Σ(C−Q)/ΣCの加重率を区別する。新しい回生・補機・SOCモデルは独立拡張感度とし主評価を置換しない。

CのT08/T09/bridgeは同一保存速度・共通非pack質量による条件付き感度を継承する。未知部材差δに対し既知削減b−δ、δ=bで質量相殺、δ>bで逆転。完成packの工学的妥当性と量子解析→材料改善は未実証で、A/Bの走行結果へ合算しない。固定軌跡算術には新SUMO不要、材料・pack・積載の実証には別の工学データが必要。
''')
 timings=[]
 for label,name in [('元経路回収','ROUTE_RECOVERY_SUMMARY.json'),('道路静的診断','NETWORK_DIAGNOSIS_SUMMARY.json'),('回収独立照合','FINAL_RECOVERY_REVIEW.json'),('幾何追加照合','NETWORK_SUPPLEMENT_SUMMARY.json'),('不足来歴確認','MISSING_FEASIBILITY_SUMMARY.json'),('35算術fixture','MEASUREMENT_VALIDATION_SUMMARY.json'),('最終独立レビュー','FINAL_REVIEW.json')]:
  m=read(O/name)['metrics'];timings.append(f"|{label}|{m['wall_s']:.6f}|{m['CPU_s']:.6f}|{m['max_RSS_bytes']:,}|")
 doc('06_NEXT_STAGE_GO_NO_GO.md',f'''
# 次段階ゲート判定 — A/B地域代表試行はNO-GO

## ゲート

|ゲート|A|B|理由・GOに必要な証拠|
|---|---|---|---|
|G1道路|FAIL|FAIL|N0幾何不連続、N1動的不適合。採用版の幾何・接続・車種・停車・動的受入が必要|
|G2比較可能性|CONDITIONAL|CONDITIONAL|N0保存数理条件では対応、修正版はHOLD。新網は端点・全OD・目的値・参照最適値・計画の再評価範囲固定が必要|
|G3 B経路|対象外|HOLD|2,323元OD全回収、2旧cache同一性HOLD、2,662partial。固定12対象の5問題未回収|
|G4配送イベント|HOLD|HOLD|モデル契約・fixtureはPASS。active-stop監視、native出力との極小網統合未受入|
|G5 DC|DCを評価する場合HOLD|HOLD|凍結kernelPASS。現行B共通mass採用・native軌跡adapter／終端条件の受入不足|
|地域代表試行|**NO-GO**|**NO-GO**|重大必須条件未成立。AはBの全復元を待つ必要はない|

仕様でc=max(started,ready)+102を定めたことは、過去の候補定時率を正式実測へ昇格させることではない。道路FAILもモデル算術PASSで相殺しない。

## 次に行う具体的作業

|優先|作業・使用ファイル・入口|期待成果物|合格／停止条件・資源|
|---|---|---|---|
|1|N0変換元、N1 B6、`MAX_GAP_ROOT_CAUSE_CASE.json`、5TLS記録に基づき別道路版の修正方針を固定|NETWORK_REPAIR_PROTOCOL、変更要素台帳、局所witness|幾何連続と停車・安全・信号／待ち・需要処理を同時に受入。全域再計算前に限界固定。局所nativeは事前に目的／件数を明示し10×120秒以内|
|2|`measurement_contract.py`を新しい極小native adapterへ接続、既存合成fixtureとactive-stop ledger照合|イベント行、FCD・stop・tripinfo・異常ログの結合表|途中終了、ended未出力、early until不足、誤位置、未取得切替を保持。102秒の連続停車証拠がなければHOLD|
|3|`B_UNRECOVERED_INTERVALS.csv`、元baseline `full_run.py`／manifest、37制御を用い小数脚の同一生成テストを計画|再生成source版、exact-edge比較、routeSHA|元edge完全一致でEXACT。近似距離だけは不可。13,249脚の一括探索は事前試験・資源見積後|
|4|`MASS_EVIDENCE.json`、FREEZE、no-window PROTOCOLからB共通質量を正式採用|MASS_ADOPTION、DC入力契約・端点ledger|根拠ある空荷1,155kg候補等の研究上の条件を明記。PEkg創作不可。未採用ならG5HOLD|
|5|採用道路のendpoint・OD・古典参照・QAOA目的値を旧版と比較|新MANIFEST、全行列差、影響計画・政策台帳|変わる場合は新series版。旧最適値・gap自動転用不可|
|6|全ゲート通過後、事前固定の地域代表設計を実行計画化|PILOT_PROTOCOL、計測wrapper、件数・予算|今回実行しない。wall/CPU/RSS/失敗率を測定後に全件費用を決定|

## 許可条件を満たした後の最小代表設計

A：前回の固定pilot候補を維持し、出発0／正遅延、早着、期限等号／超過、未取得古典切替、訪問順のみ／出発のみ変更を含める。等号等を自然な地域入力で保証できない場合は極小native境界試験と区別し、期限を結果に合わせて変更しない。303政策＋15機構＝318入力を今回走らせない。正遅延を0秒軌跡のシフトで代用しない。

B：R0_001、R1_001、R2_001、R3_001／040／078、R4_001／040／078、R5_001／036／070。12問題の960量子参照＋12古典参照の対応を保持。成功した7問題への恣意的縮小は不可。前回192入力経路組はpilotの事前候補数であり受入run数や実行回数ではない。完全入力のunionを再集約してから数える。

単車・背景交通なしを維持し、seed変動は未計測。初めは同一入力の少数seed比較で変動の有無を確認する。変動なしを独立交通反復と数えない。背景交通追加は別条件。full実行予算・失敗率・交通反復数は地域native未実測につきHOLD。

## 今回の検証実績

追加fixture35／PASS35／FAIL0、最終独立readback {final['checks']}／PASS{final['passed']}／FAIL{len(final['failed'])}。既存26単体・6,605readback・7合成nativeは旧証拠として保持。保存collision183車体照合一致、37controlのnative距離134脚中133PASS・1HOLD。これらは異なる単位であり合計して科学標本数としない。

|処理（すべて静的／単体）|wall秒|CPU秒|最大RSS bytes|
|---|---:|---:|---:|
{chr(10).join(timings)}

CPUはprocess累積でimport時間を含む。wallは各main内timerで、特に小fixtureではimport前の時間を含まずCPUと直接比べない。RSSはprocess peak。初回経路回収の中断は効率改善前の試行としてログ保持し、地域走行失敗率には数えない。

新規native0、地域試行0。地域wall／RSS／失敗率は **未計測**。静的最大RSS約3.04GBをSUMO1件の実測値や全件工期へ換算しない。

## Cと残存研究限界

Cは条件付き材料会計・固定速度DCの整理にCONDITIONAL GO、新しい完成pack性能主張はNO-GO。T09完成pack183行HOLD、全面対向1行FAIL、量子材料改善未実証を維持。追加SUMOは既存質量算術／相殺境界に不要。実材料・電極・packの未知部材・電気化学・寿命／安全等は新工学証拠が必要である。

保存結果確認と再計算入力の一部回収は進んだが、原資料からの完全再生成・現実配送／車両妥当性は未達。「研究全体の再現性を確保」と書かない。改善ゼロ・逆転を含め、入力→採用→イベント→DCの伝達を説明できることを最終の研究合格条件とする。

**現時点でAまたはBの地域代表試行を開始できるか：両方開始できない。** AはG1とG4、Bは加えてG3とG5を解消し、変更網ならG2の再計算／比較可能性を受入する必要がある。今回の作業はここで停止し、地域代表試行・全件SUMOを自動開始しない。
''')
 # A compact, machine-readable contract preserves nullable physical observations.
 write('SERVICE_STATE_SCHEMA.json',{'version':'SERVICE102_V1','interpretation':'MODEL_NOT_PHYSICAL_HANDOVER','required_evidence':['task_binding','native_stop_started','native_lane_position','continuous_stopped_coverage','observation_horizon','run_abnormality_log'],'nullable_physical_arrival':True,'service_s':102,'completion_rule':'max(started,ready_A_or_zero_B)+102 only if bound continuous stopped coverage proves service','A_deadline':'original_due_start+102','B_customer_deadline':None,'outcomes':['ON_TIME','LATE','NOT_COMPLETED','INDETERMINATE','COMPLETED_NO_CUSTOMER_DEADLINE'],'missing_stop_row':'HOLD unless live ledger or complete non-service proof','native_integration_status':'HOLD'})
 write('B_DC_INPUT_CONTRACT.json',{'freeze_path':str(R/'01_research_design/methodology/CONTROLLED_MASS_TO_DC_MODEL_FREEZE.json'),'freeze_sha256':sha(R/'01_research_design/methodology/CONTROLLED_MASS_TO_DC_MODEL_FREEZE.json'),'B_main_mass_kg':None,'mass_status':'HOLD','fixture_mass_is_not_adopted':True,'pressure_bar':[4.5,2.6],'dt_s':1,'missing':'REJECT','terminal_gap_Wh':None,'boundary':'OBSERVED_WINDOW_CONTROLLED_DC','SOC_constraint':False,'cargo_PE_to_kg':None,'primary_comparison_requires_equal_complete_service_and_return':True})
 sources('REPORT_SOURCES.json')
if __name__=='__main__':main()
