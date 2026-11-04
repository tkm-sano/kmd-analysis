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

Bの37を全Bの固有数と呼ばない。BはR0=22、R1=9、R2=6、R3〜R5=0の完全入力。完全候補に結合した元参照は2,820、残る33,980参照は明示UNBOUND。未確定候補に完全run IDを発行していない。4,987の内訳を失わず、別のrecipe IDは未確定識別用としてのみ付与した。

## 2. Aの構築

D11 operationsとD12候補・INPUT_DETAILSを照合し、303候補の元車両XML/hash、原NPZ/hash、道路hash、vType/hash、訪問順・道路edge列・停車lane/endPos/duration/untilを読戻した。新しいA_INPUTSへvehicle XMLを生成し、requested departだけ変更した。untilは絶対時刻のまま保存仕様を維持し、0秒軌跡の時間シフトを使わない。

A_COMPLETE_RUNSは303入力、A_OPERATION_RUN_LINKSは2,808全判断のmethod/取得状態/仮想利用可能時刻/締切/採用/切替/要求出発を保存。actual departureは保存0秒の観測がある場合だけ記載し、正遅延はnull。要求時刻を実測出発へ読み替えない。0秒83候補に既存軌跡hashがあるが、過去環境同等性・配送成果受入が未成立なので全83も再利用承認0。

成功64×36×4=9,216の機構参照も別台帳A_FOUR_CONDITION_LINKSへ対応付けた。政策303に含まれない15組をA_ADDITIONAL_MECHANISM_RUNS/A_MECHANISM_INPUTSへ別に具体化した。政策と機構のunionは318固有入力。303という政策件数を318へ上書きせず、全機構比較まで行う場合は追加15走行が必要。

## 3. Bの構築と残る不足

前回B_PLAN_REFERENCESをそのまま主参照とし、460NPZのnodesとroute_indicesから訪問順を復元。R4=100、R5=70問題を維持。ENDPOINT_READBACKのrole別edge/lane/位置を照合した。現行Bでは出発0、停車duration102秒、untilなし、顧客ready/dueなしを新adapterで明示固定した。旧窓ありのuntilや待機を転用していない。

道路edge列は既存のclassical/canonical/quantum fixed_legs.trips.xmlとrou.xmlから、origin/destination edge・lane・位置が**厳密に一致**する保存区間だけを使って連結した。新しい経路探索は実行していない。物理問題数・PID文字列の一致だけで旧走行を結合していない。ODは元NPZと原input hashに結び、別網のOD/最適値を代入していない。

不足する位置付き区間は219,211固有要求。B_REQUIRED_POSITIONAL_LEGSとB_UNBOUND_LEGSに端点・seed・router/net hash・候補内位置を保存した。これはSUMO走行数ではない。既存cache以外の保存経路が不存在であることの網羅証明でもない。この3cacheから組めないという結果であり、入力を補完してID数を水増ししていない。

B_PLAN_RUN_LINKSにはfamily/config/problem/rep、PCG64 SeedSequence entropyと生成state4、seed規則source hash、元計画source hashを保持。代表12問題のmirror600測定行は保存streamと照合した。Grover/activeは保存source規則でseedを識別し、再測定していない。

古典初期経路460参照はB_CLASSICAL_BASELINE_LINKSとして別保存。すべて4,987組の既存候補へ対応し、独立の460走行を加算しない。主36,800参照から古典参照を差し引かない。

## 4. 完全識別子と環境

RUN_INPUTS.jsonlのpayloadをUTF-8・keyソート・compact JSON・NaN禁止で直列化し、SHA256をrun IDにする。series/input hash、車両属性、vType hash、道路hashとedge列、全stop設定、交通需要/seed、step/FCD/end/teleport等設定、実行環境hash、adapter/ルータ版hashを含む。環境ENVIRONMENTはSUMO1.24、専用fork、libsumocpp、lddで解決した依存library bytes、OS/kernel/arch、Python、関連環境変数を記録。

環境を現在のbytesで固定したことと、旧結果を同一環境で再生成したことは別。専用forkのclean build/一般受入はHOLD。vTypeはlegacy delivery既定で対象EVの実車校正ではない。材料質量を速度力学へ追加していない。走行後Controlled-DCの質量条件は別エネルギーkeyであり、B_ENERGY_INPUT_CONTRACTに明示採用待ちとして保存した。

全runの再hash・materialized XML照合は別readbackで検証。355個の完全入力（A303+機構15+B37）には1件単位のexecution list/argv案もEXECUTION_RECIPESへ具体化したがallow_execution=falseであり、専用forkの固定/tmp出力やclean build/計測契約の受入前には起動しない。完全payloadがあっても過去の道路幾何FAILと受入HOLDは消えない。入出力の詳細はJSONL/CSV、SOURCE_FILES.json、INDEPENDENT_CHECKSを参照。
