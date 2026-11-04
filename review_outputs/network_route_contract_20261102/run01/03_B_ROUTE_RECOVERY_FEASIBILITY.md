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
|R0|6240|5680|91.025641%|
|R1|6240|5440|87.179487%|
|R2|6240|5200|83.333333%|
|R3|6240|3372|54.038462%|
|R4|6240|2401|38.477564%|
|R5|5600|2240|40.000000%|

設定別・測定rep別・460問題別の分母と分子は `B_FINAL_COVERAGE.csv`。config各4,600参照で、6設定3,040、GroverP2 3,048、GroverP3 3,045。欠落は大規模側に偏り、回収済みsubsetを460問題全体の効果へ一般化しない。測定repを独立物理標本として数えない。

事前固定12問題のうち7問題は80参照すべて回収済み、5問題（R3_078、R4_001、R4_078、R5_001、R5_070）は0。成功例へ恣意的に差し替えない (`PILOT_INPUT_RECOVERY_COVERAGE.csv`)。古典側12参照も独立に完全性を確認してから試行する。

## 残る復元と工数

13,249固有欠落OD区間／16partitionの全数値行は存在する。元baseline `full_run.py` は正常scratchを削除し、loopだけを保存するため、bulk edge列欠落を説明できる。保存原本の追加発見を先に行う。

元baseline実行manifestの保護入力2,942件はhash一致 (`OD_GENERATOR_PROTECTED_INPUTS.csv`)。後期lane-routerソースも保全されているが、欠落旧schemaにそのsource-hash欄がなく、このソースを元生成器とみなさない。原ルータbinary・費用・端点・seed・tie規則・loop補正を固定した小数制御脚で完全edge列を再生成し、37制御で同一性を検証してから不足を展開する。今回その再生成は未実施。決定性を推測してEXACT_RECONSTRUCTEDへ昇格していない。

元脚を再生成できてもN0道路受入FAILは残る。N1/N2で得る経路は新条件の代替であり元実験完全復元ではない。必要な計算時間は未実測のため全件工期HOLD。`missing_feasibility.py`、`MISSING_OD_GENERATOR_PROVENANCE.csv`、`B_UNRECOVERED_INTERVALS.csv` が具体的な入力・行・再生成対象である。
