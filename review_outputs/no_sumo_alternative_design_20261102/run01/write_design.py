"""Freeze an audit-stage alternative design, without running its full analyses."""
from support import *
def doc(name,s):(O/name).write_text(s.strip()+'\n')
def main():
 a=js(O/'A_SUMMARY.json');b=js(O/'B_SUMMARY.json');c=js(O/'C_SUMMARY.json');road=js(O/'ROAD_SUMMARY.json');base=js(O/'BASELINE_SUMMARY.json');toy=js(O/'TOY_SUMMARY.json')
 hist=rows(O/'ROAD_NETWORK_VERSION_HISTORY.csv');cases=rows(O/'A_SMALL_CASES.csv');bs=rows(O/'B_RECOVERY_BIAS_DESCRIPTIVE.csv');cert=rows(O/'B_REFERENCE_CERTIFICATE_STATUS.csv')
 def ref(p):
  p=use(p);return f'`{p}` / SHA256 `{SRC[str(p)]["sha256"]}`'
 doc('00_SOURCE_AUDIT.md',f'''
# SUMOなし代替分析の入力監査 — 2026-11-02

本作業は道路修復を停止し、保存計画・固定OD・材料会計を用いる分析の仕様を確定する。新しい地域SUMO、道路診断・修正、経路再探索、QAOA、A/B全件評価、論文編集は実施していない。行集計は保存値の欠測・選択バイアス確認であり、新しい全件配送成果・電力量の計算ではない。

## 保存版と所在

HEADは `1b00bd7927fa1e7688e4772ac1da9db46d9bac11`。作業開始時tracked差分0。旧3レビューの成果物{base['prior_artifacts_verified']}件を各manifestから再ハッシュし、不一致0。レビューMD{base['prior_reports_read']}件、D10、D03読取元、D11／B生成コードを実際に読んだ。最終状態は `PRESERVATION_FINAL.json`、全参照SHAは `SOURCE_INVENTORY.csv`、成果物SHAは `ARTIFACT_MANIFEST.json`。

R=`{R}` は現作業木、U=`{U}` は外部未追跡保全、B=`{B}`／L=`{L}` は外部バックアップ／移設領域。外部資料を公開Git収録扱いにしない。公開Git単独で全入力が再生成できるとの主張は不可。

## 採用入力と生成経路

|系列|入力・生成経路|今回の検査|
|---|---|---|
|A|旧78NPZ→古典／QAOA原JSON→D10政策→D11 operations_2808→前回303政策＋15機構候補|全78入力hash・4需要・102秒・有限OD、取得64／未取得14。新規時刻計算は10経路40taskのみ|
|B|現行no-window460NPZ→staged 3family/8設定ALL_SEEDS・raw records→初回B_PLAN_REFERENCES→前回B_PLAN_RECOVERY_LINKS|36,800参照・4,987候補の保存値と分類を結合。新規cost検算18経路、極小3入力の参照最適値検算|
|C|T08 SCENARIOS→部材・MATERIAL_ENERGY、T09 PACK_20KWH_SENSITIVITY→bridge|T08式、保存460軌跡の加重率、T09代表4行、bridge6行を独立算術で照合|
|道路|N0／rollback／LHT／B2…B6／guard／downstreamの保存版・generation・acceptance|14ファイル12異なるSHA、履歴104資料を読取り。新規診断0|

主要入力：

- {ref(U/'docs/research/CPX01_D10_ADOPTION_DECISION_20261017.md')}
- {ref(U/'review_outputs/cpx01_d11_validation_20261017/operations_2808.csv')}
- {ref(P1/'B_PLAN_REFERENCES.csv')}
- {ref(P3/'B_PLAN_RECOVERY_LINKS.csv')}
- {ref(R/'01_research_design/methodology/CONTROLLED_MASS_TO_DC_MODEL_FREEZE.json')}
- {ref(U/'review_outputs/material_ev_stage2_20261026/run02/SCENARIOS.json')}
- {ref(U/'review_outputs/t09_open_data_model_20261029/run01/PACK_20KWH_SENSITIVITY.csv')}

## 構造・欠測と監査差異

`*_SCHEMAS.json` にrow数、列、NULL、指定PKの重複を保存。Aの入力不足なしは固定ODの代数計算に関する判定で、地域道路・配送成功の受入ではない。BではPK=(family,config,problem,rep)、Aは(policy,PID)。系列間でPIDや件数だけの結合をしない。

旧報告のB回復2,323＋旧cache2＋partial2,662、受入走行0、道路N0 gap563,513・N1保存collision183を保持。今回、厳密参照最適値の**407入力／欠測53入力（R4=21、R5=32欠測）**を明示した。これは旧資料の値を置換したのではなく、最適性評価の適用分母を特定したもの。保存gap欄の欠測8,310は、53入力×7設定×10=3,710と、active系列の列未保存4,600による。activeのうち407入力は今後値から導出可能だが、今回は全件補完していない。

初回B監査コードがexact値を全件で仮定してNULLで停止した。旧コード・ログを `revisions/` に保存し、欠測保持へ修正後に再検証した。科学データの矛盾ではなく監査コードの仮定誤りで、53欠測を除外・ゼロ化していない。

## 独立性と限界

AはFraction逐次式と別のmax-plus閉形式、保存OD再生CSVを照合。Bはraw JSON・NPZから18costを別算術で再計算し、R0/R1/R2各1入力では計150順列を軽量列挙して最適値一致を確認。407件の大規模証明全体を再実行したわけではない。Cは別Fraction式から代表部材と保存値の差・集計を確認した。

材料文献の保存PDF `SOURCES/chen2020.pdf` はpdftotextで新領域へ抽出し、保持試験とVASP記載を確認 (`C_LITERATURE_LOCATORS.json`)。単位Ah/kgとmAh/gは数値同一。既存入力を物性の対象車・完成pack適合へ昇格しない。

PASS＝指定された内部照合が成立、CONDITIONAL＝固定OD・質量・軌跡等の仮定、HOLD＝入力／適用証拠不足、FAIL＝既存不適合を保持。証拠分類OBSERVED等は判定とは別軸である。
''')
 ht='\n'.join(f"|{x['version']} ({Path(x['network_path']).parent.parent.name})|`{x['network_sha256']}`|{x['status']}|" for x in hist)
 doc('01_ROAD_NETWORK_ATTEMPTS_AND_STOP_DECISION.md',f'''
# 道路修復の既往履歴と停止判断

**修士研究の主分析では、地域道路網の追加修復を停止し、案2へ移行する。** 道路FAILを解除する判断ではない。N0/N1は地域実験に不採用、N2は未構築を維持する。

## 既に試した方法

|段階|目的・実変更|保存検証結果・未解決|
|---|---|---|
|N0 run3|外部lane端点をjunction中心へ延長、長さ更新、内部幾何維持|1m超gap563,513、最大97.033728m。FAIL。静的OD費用自体もこの保存網由来|
|A rollback run2|延長前へ戻す|別SHA。左側通行・信号・端点適合が解決したわけではない|
|B LHT|CLIで左側通行を明示、旧TLS保持|旧phaseと新幾何の同時green foe不適合。設定ファイルのLHT指定が上書きされる初回失敗も保存|
|B2|左側幾何＋TLS再構築|残存8gap、信号4対、端点再対応等でFAIL。再生成controlはXML byte差と意味比較を区別|
|B3/B4|8gap局所修正、信号保護分離・G/gとresponse調整|局所改善。全網screen拡大で18対／12junctionをHOLDとして残した|
|B5|18対のfoes/response/intLanes、12TLSを個別保護green|静的回帰PASS、cycle282〜658秒。green比・容量・待ちと配送mappingは未受入|
|B6 priority|信号優先再受入|静的範囲PASS、動的保存183collision record。車体重なり独立照合183/183、5TLS・7順序なしmovement対|
|grouped run01/run02|競合group化でcycle短縮、制約追加|run01は282probe到達でもcollision2。run02静的回帰PASS／最終静的HOLD、動的未実施。両版を区別|
|body-clearance prototype|request6/7補正XML＋5TLS runtime guard|XMLだけのload90はcollision43。guard併用ではcollision0だがarrived9,181→8,584、異常停止388→410、最大phase保持3,411.5秒で運用FAIL|
|downstream control|space-only／clearance等の出力側占有制御|安全の一部改善と待ち・容量の両立が未成立。別背景需要の受入を実配送成功扱いしない|

各版の実ファイル・SHA・目的・変更・判定・参照先は `ROAD_NETWORK_VERSION_HISTORY.csv`、検証JSON・コードへの起点は `ROAD_HISTORY_EVIDENCE_FILES.csv`。直接読んだgeneration／acceptance／回帰報告を根拠に履歴を整理した。今回は新しい診断手法もnative試験も実行していない。

|版（複製control含む）|実ファイルSHA256|保存判定|
|---|---|---|
{ht}

14実体に12異なるhash。B3/B4の再生成一致controlを独立修復成功数に数えない。B2 reproductionはbyte hashが異なるため元版と同一バイトとは呼ばず、保存canonical比較の範囲に限定する。

## OD・既存計画への影響

N1へ旧使用端点6,670roleを移すと958offsetが範囲外、範囲内でも5,700座標が0.1m超移動した。保存355経路すべてで固定lane0距離／自由流時間proxyが変化。新native ODが何秒変わるかは未計算。旧端点・OD・最適値・QAOA目的値の自動再利用は不可。全域mapping→全OD→参照値→計画妥当性→イベント→資源の再受入が必要となる。

地域代表試行はA/Bとも未実施、受入済み既存走行0。過去のprobeや背景交通stress試験を研究の代表配送試行と数えない。過去の衝突記録を独立した現実事故件数とも呼ばない。

## 停止理由と再開条件

研究目的は量子優位・実EV電費の実証ではなく、媒介と成立境界の解明である。計算取得→採用→出発・訪問順→固定OD成果、材料会計→固定速度DCの条件付き関係は地域網受入なしで検証可能。一方、実地域の信号・混雑・速度・電費を結論に必要とするなら修復を省略できない。

今回は前者へ対象を明示的に限定するため追加修復は不可欠ではない。案1は別研究工程として保留する。再開する場合は「現実の動的交通の何を検証するか」、対象5TLSの受入条件、mapping／全行列再計算、時間・人員予算を新計画で固定する。成功まで無制限修復を続けない。全域修復工期は未計測で数値予算HOLD。保存静的診断約73秒／3.04GBは、修復完了工期の見積値ではない。
''')
 ct='\n'.join(f"|{x['case_id']}|{x['scenario_id']}|{float(F(x['departure_s'])):.6f}|{x['F_PE']}|{float(F(x['min_slack_s'])):.6f}|" for x in cases)
 doc('02_SERIES_A_FIXED_OD_FEASIBILITY.md',f'''
# A：固定ODによる配送成果分析の成立性

判定 **CONDITIONAL GO**。旧78入力・36政策すべてのモデル定時率を計算するためのデータが存在する。今回は全2,808判断を再評価せず、10経路40taskだけを検算した。モデル名を `A_FIXED_OD_NO_SUMO_V1` とし、native配送成果と別系列で保存する。

## 入力と正式定義

78NPZすべてのSHAが古典原JSONと一致。nodes、demand PE、travel秒、distance m、ready、due_start、service102、帰庫脚が存在。26親問題・25需要group、各物理問題4配送先。QAOA取得64、未取得14。成功64中59は古典と同じ訪問順、5は異なる。取得を量子実機の成功率とは呼ばない。

D03は元dueがサービス開始期限であることに対応し、完了期限を **due_start+102秒**とする既存採用定義。D10採用MD、D11原CSV、保存 `verify_a.py` のNPZ直接読取りを照合した。新しい期限を導入しない。デポのready0／due32400／service0は顧客期限と別に帰庫制約として保存する。

## 固定ODモデル

固定訪問順r=(0,r1,…,r4,0)、出発d、行列Tについて、a_k=e_(k−1)+T_(r(k−1),rk)、s_k=max(a_k,ready_rk)、c_k=s_k+102、e_k=c_k。最終帰庫=e_4+T_(r4,0)。顧客作業完了時刻c、帰庫時刻、帰庫32400超過flagを区別する。

この式は古典・QAOAの保存ODベーススケジュールと同じ待機・102秒サービスを表現する。**nativeのduration/untilによる停車終了の代替観測ではない**。新モデルではサービスが中断なく成立し、作業完了後ただちに次へ出発すると仮定する。道路区間費用は出発時刻によらず、信号・混雑・lane動作を含む追加時刻変動を計算しない。

遅延して期限を超えても訪問順を再最適化せず、モデル上のサービスを継続しLATEを記録する。32400での強制打切りを新設しない。帰庫制約違反と顧客未完了を混ぜない。有限OD・全訪問が成立する理想モデルでは交通に起因する未到達やサービス中断率を推定できない。入力欠落ならUNKNOWNを需要分母に保持する。

定時c≤due_start+102（等号を含む）。主F_PE=定時PE/固定全需要PE、副F_count=定時顧客数/4。期限超過は分母に残す。未知があれば点値nullと上下限を保存する。native到着・実配達・実速度・DCは出力しない。

## 取得・採用・出発

D10のL={{900,3600,7200}}、T_C120、T_Q={{60,900,3600,7200}}、B={{0,120,720}}、切替600、dispatch120秒、other0を保持。利用可能時刻−L+T、採用締切−B。取得済みかつt_Q≤締切ならQ採用、遅い／未取得は保存規則で古典へ切替し出発≥0。これは仮想運用時刻で、保存CPU求解時間を代入しない。

A1は取得64問題で、CC（古典route・古典departure）、QC（Q route・古典departure）、CQ（古典route・量子優先政策departure）、QQを36条件別に比較。最大9,216参照で、独立標本数ではない。政策がCを採用する時のQ route強制は機構反事実と明記する。

A2は全78×36=2,808の量子優先政策判断に、各同一問題・条件の古典のみ政策を対応させる。未取得14も古典切替で評価。成功例のみのA1と混ぜない。Aの64はB設定・seedの標本ではない。

## 少数検算

既存ラベルに基づいて同順、異順、未取得、正遅延を選び、1問題の4条件機構を追加。政策判断4例は原CSVと一致。全40taskの時刻はFraction逐次式と独立max-plus式が一致し、該当保存OD再生CSVとも一致。入力・途中時刻・deadline・定時flagは `A_SMALL_CASE_TASKS.csv`。

|case|保存scenario|出発秒|PE定時率|最小余裕秒|
|---|---|---:|---:|---:|
{ct}

期限等号／1秒超過の2例は、実入力から出発境界を代数的に導いたfixtureである。D10政策にその出発時刻が存在したとは主張しない。元ready/dueは変更なし。正遅延120秒が早着待機へ吸収され完了時刻が変わらない例を確認したが、全78件の結果として一般化しない。

一般にc_k(d)=max(d+P_k,R_k)というmax-plus形で、出発増分は待機で吸収されるか、0〜同じ増分だけ伝達する。期限を固定したまま最初の遅延が出る出発境界を導出できる。これを必要技術能力・影響消失条件の主分析とする。結果が変わらないことも研究成果である。

## 論文に採用できる範囲

固定された保存OD費用モデル内での採用政策・出発・順序の機構分析として主分析にできる。N0の幾何FAILにより、東京の実旅行時間・信号応答・動的速度・配送達成率を妥当に表現した実証とは言えない。ODは「受入済み地域旅行時間」ではなく、版と限界を固定した研究用費用表として使用する。独立した実旅行時間データがなければ、OD一律倍率感度を実交通校正や確率分布と呼ばない。Aの走行DC接続はUNTESTEDのまま残す。
''')
 scale='\n'.join(f"|{sc}|{sum(x['exact_optimum_seconds']!='' for x in cert if x['scale']==sc)}|{sum(x['exact_optimum_seconds']=='' for x in cert if x['scale']==sc)}|" for sc in [f'R{i}' for i in range(6)])
 bias='\n'.join(f"|{x['group']}|{x['recovery_stratum']}|{x['references']}|{float(x['mean_saved_objective_s']):.3f}|{x['saved_gap_available_n']}|{float(x['mean_saved_gap_percent']):.5f}|" for x in bs if x['dimension']=='scale')
 doc('03_SERIES_B_NO_SUMO_FEASIBILITY.md',f'''
# B：SUMOなし比較と電力量接続の限界

推奨 **B-E3：計画段階を主結論とする（CONDITIONAL GO）**。物理460入力、26親・25需要group、8設定×10測定repの36,800参照を保持する。R0…R5は78/78/78/78/78/70入力、配送先3/4/5/25/100/125。旧時間窓あり系列のR4=99、旧保存460軌跡と混同しない。

## 指標の可用性

|指標|元データ・計算|成立範囲と制限|
|---|---|---|
|目的値／OD時間|raw record、ALL_SEEDS、NPZ travelの訪問脚和（秒）|全36,800参照。今回再計算18経路のみ。実走行時間ではない|
|OD経路距離|NPZ distanceの脚和（m）|全460入力に行列あり、全参照で今後導出可能。edge列回復不要。SUMO走行距離と別名|
|帰庫時刻|出発0＋OD時間＋102n|固定ODで導出可能、顧客待機なし。既存帰庫期限32400は顧客時間窓ではない|
|厳密最適値|元REFERENCE／REFINED、R3 exact-integer DP|407入力で保存。53入力は未確定。メタデータ照合と極小3入力の独立最適値一致。全大規模証明の再実行はしていない|
|global gap・最適値一致|100(J−J*)/J*、完全一致|407入力×8×10=32,560参照が潜在分母。残り4,240を0gapにしない|
|orbit gap|mirror二値chain DPのorbit最小|限定支持上の最適性。global TSP最適値と分離|
|取得・実行可能性|raw status、route permutation／容量・帰庫domain証明、invalid raw samples|保存採用経路と8,192shot全試行の取得確率を区別。参照の存在だけで全shot成功率100%とはしない|
|初期解との比較|同一inputの保存classical initial route/cost|sampled-bestを主値とし、min(initial,sampled)は別のincumbent維持政策。悪化をminで隠さない|
|実CPU時間／RSS|FIT、RESULT、実行ログ、classical resources|fit／検証DP・MC／sampling／前処理を別境界。欠測を0秒にしない。QPU実測値ではない|
|seed変動|rep0…9と元SeedSequence状態|同じ学習結果からの測定変動。10独立学習・10物理問題とは呼ばない|
|qubit／layer／gate|protocol、snapshot、backend stats|mirrorの二値自由度floor(n/2)と物理qubitを区別。p2/p3は論理層。compiled回路深さ・native gate数がない設定はHOLD|
|shots|各protocolの8,192/rep|fitのCVAR1,024、Grover training65,536等と別計上。backend演算回数をhardware shotsと混ぜない|

|規模|厳密参照あり|未確定|
|---|---:|---:|
{scale}

保存global-gap列のNULL8,310は、53入力×7設定×10とactiveの全列未保存4,600。activeの407入力分は原目的値と証明値から今後導出できるが、今回は全件補完していない。参照未証明の53はbest-knownや下界との偏差を別名で報告可能だが、厳密最適性gap・最適値一致率には含めない。

mirror5設定は固定非隣接swapの2^floor(n/2)支持でありn!全探索ではない。同じorbitの古典chain DPを比較対象に残す。Grover P2/P3は全順列の理想初期化を仮定し、n≤25ではDP、n>25では独立MC等によるCPU検証を用いる。active P3は3点angle grid・rank上限の近似MPS。これらのアーキテクチャ・支持・角度探索・誤差・資源が違うため、計算速度の単一順位を量子優位と解釈しない。

旧cpu-matched classical資料は別時期／設定の結果である。現行8設定のfit・検証・測定と同じ時間予算であることを確認するまで、CPU予算一致比較へ自動転用しない。compiled resource旧表も同様。`B_RESOURCE_FIELD_EXAMPLES.csv` は18例のfield所在・scope・NULLを示すだけで全件資源評価ではない。

## 経路回復の偏り

2,323 ORIGINAL_RECOVERED、2旧cache同一性HOLD、2,662 PARTIAL。元OD脚同一性カバー24,333/36,800=66.122283%、構造入力unionカバー24,493/36,800=66.557065%。地域受入0を保持。

保存目的値・gapの分布を全参照と回復群／非回復群で記述した。親、需要group、設定、rep、問題、訪問順hash別の記録は `B_RECOVERY_BIAS_DESCRIPTIVE.csv`。平均値は保存参照の反復加重記述で、独立標本平均や一般化効果量ではない。

|規模|群|参照数|保存目的値平均秒|保存gap有効n|保存gap平均%|
|---|---|---:|---:|---:|---:|
{bias}

回復率はR0約91.0%に対しR4約38.5%、R5=40%。同一規模でも目的値分布が異なる。gap平均は厳密参照のある7設定の保存欄のみなので欠測分母も明示した。回復は無作為抽出ではなく保全履歴と共有脚に依存する。回復subsetを全460の代表とみなさず、回復脚を必要としない目的値・OD距離比較は**全入力を維持**する。coverageで重み補正すれば偏りが消えるという仮定も置かない。

## 電力量の3案

|案|成立性|必要仮定・費用|推奨|
|---|---|---|---|
|B-E1 保存速度＋Controlled-DC|HOLD|現行計画の完全run条件・軌跡対応と道路受入が未成立。旧460を流用不可|Bの主比較には使わない|
|B-E2 OD・距離の解析推定|CONDITIONAL設計可能、現時点主結果HOLD|共通mass、速度・加減速・停止、損失・時間の解釈を新モデルで仮定。追加パラメータ感度が必要|独立補助分析として必要時のみ|
|B-E3 計画段階まで|CONDITIONAL GO|保存数理問題・算法範囲を明示。計画→DCは未検証|主分析に採用|

同じ20m／4秒でも、合成速度2系列はDC20.441059Whと20.269854Whとなった (`B_ENERGY_NONIDENTIFICATION_FIXTURES.csv`、fixture質量1,200kg)。ODのD/Tだけでは加減速・正値化・空気抵抗を同定できない。これはBの推定電費ではなく非一意性の例である。

B-E2を後で行うなら、区間ごとの一定速度D/Tだけで停止損失まで復元したとはしない。速度profileと停止／再発進規則を先に固定した合成モデル、または平坦・端点静止等の条件付き抵抗仕事下界を新IDで設計する。距離に比例する下界の改善は実DCの改善順位を保証しない。旧空荷1,155kgは候補にとどまり、現行B主質量はHOLD。PEをkgへ換算しない。凍結Controlled-DCの式を改変せず、新合成入力／別解析モデルと明示する。

Bには顧客ready/dueを追加しない。別根拠のない顧客定時配達率は算出しない。計画時間・距離と配送電力量の接続を検証済みに見せない。
''')
 doc('04_SERIES_C_CONDITIONAL_EVIDENCE.md',f'''
# C：材料・質量・固定軌跡DCの証拠範囲

判定 **CONDITIONAL GO**。完成packや実EVの改善を確定するものではない。T08とT09は異なるモデルであり、Bの今回の460入力と旧460速度軌跡も別版である。

## 文献事実と入力参照値

保存Chen2020 PDFのFig5g／本文では、1C・100cycle後のLP121mAh/gと保持70.4%、S-200194mAh/gと保持99.0%が報告されている。これは論文中の試験条件での材料結果（OBSERVED_PUBLISHED）で、初期比容量の直接観測・完成full-cell・pack・車両の結果ではない。

121/0.704=171.875、194/0.99=195.95959596 Ah/kgはDERIVED_RETENTION_REFERENCE。保持率をもう一度掛ける等の二重適用をしない。対象材料の実用初期比容量としてはHOLDの条件付き入力である。平均電圧・利用率・正負活物質率・N/P等もSCENARIOSの仮定と文献値を分類して使う。

同PDFのComputationsはVASPによるDFTと記載する。量子力学を使う材料計算と、量子計算機の利用を区別する。量子計算機によってこの材料改善が実現した証拠はない。PDF／抽出textのSHAとlocatorは `C_LITERATURE_LOCATORS.json`、他部材値の出典は元PARAMETER_SOURCES／DATA_PROVENANCEに保持した。

## 独立照合した数値

|対象|今回の再計算|判定・意味|
|---|---:|---|
|T08 LP−S200 mass|{c['T08_mass_difference_kg']:.12f}kg|PASS算術、CONDITIONAL材料・簡略固定部材|
|T08下側Crr総量加重DC削減|{c['T08_lower_weighted_percent']:.12f}%|保存460軌跡のWh差を個別行から集計。実配送電費ではない|
|T09固定担持既知mass差|{c['T09_known_fixed_loading_difference_kg']:.12f}kg|代表pair B015（031/032行ID）の6部材を別式で照合|
|T09固定面積既知mass差|{c['T09_known_fixed_area_difference_kg']:.12f}kg|代表pair B051（103/104行ID）を照合|
|完成pack質量|183行NULL|HOLDを保持|
|全面対向不適合|1行|FAILを保持、rowはC_T09_PRESERVED_FAIL.csv|

T08はQ=E_gross/V、正活物質Q/(q_ref×u)、負活物質Q×N/P/q_neg、両塗工材へ活物質率を適用し、固定cell部材・pack他部材を加える簡略会計。gross20kWh、usable18kWhは別量。

T09は活物質・塗工材に加え、面積・担持・孔隙率、Al/Cu箔、セパレータ、電解液の会計。4代表行の各部材をFraction式で再検算した (`C_T09_COMPONENT_SMALL_CHECKS.csv`)。T08の固定部材19/15kg等をT09へ再加算しない。既知部材sumは完成packではなく、case・tabs・foil margin・pack構造等が未実測で、残差から穴埋めしない。

## 相殺・逆転とDC接続

b=M_known,LP−M_known,S、δ=M_unknown,S−M_unknown,LP と定義。完成全質量削減はb−δ。δ<bで軽量、δ=bで相殺、δ>bで逆転。固定担持b≈9.722608kg、固定面積b≈5.977891kgは指定pair条件での境界であり、他設計すべてへ普遍化しない。

`C_UNKNOWN_MASS_BOUNDARY_FIXTURES.csv` は各境界のδ=b−1,b,b+1を検算。未知部材の実分布を測定したのではない。bridge25,760行は460保存軌跡上の設計・mass probe・Crrの反復で、独立試料25,760ではない。今回6行の差・mass関係を独立readback、全軌跡の再積分はしていない。

凍結Controlled-DCは1秒速度、右端距離、W1転がり・W2空気・W3並進・W4固定回転mass61kgを合計後に正値化、η0.90。回生なし、補機／旋回損失境界外、平坦。材料間で同一速度・共通非pack質量を固定する。branch切替があるため質量差×一定係数と無条件に近似しない。走行時間・距離・restartによる感度を保存列で記述し、同じ軌跡の反復を独立標本にしない。

下側Crrの総量加重削減0.412579010%と個別率平均0.409329419%を区別する。これらはN0由来の保存速度を固定した数理感度であり、道路受入FAILのため地域妥当性を実証しない。未観測終端はunknown、0Whで補完しない。T08/T09の完成pack同士、実EV、量子由来効果として結論しない。

## 追加データなしで完了できる範囲

材料入力の出典・モデル会計・既知mass差、δ相殺境界、保存軌跡下のDC変化・走行条件別感度は整理できる。新SUMO不要。未知部材mass、実用full-cell電圧・利用率・劣化／寿命・安全、実pack設計・対象EV校正は新工学証拠がなければHOLD。量子解析→材料改善の因果接続はUNTESTED。保存結果の再現と工学的妥当性を同じ判定にしない。
''')
 matrix=[
 ('P1-01','計算方法','取得状態・route・CPU時間','method,acquired,route,wall/CPU','raw JSON/ALL_SEEDS; sample readback','A/B raw outputs','A_SOURCES.json;B_SOURCES.json','OBSERVED','PASS_SAVED_COMPUTATION','CPU simulation outputs, not QPU or real fleet','Hardware acquisition performance UNTESTED'),
 ('P1-02','route','目的値・gap・距離','J=sum(T_ij),D=sum(D_ij),gap=(J-J*)/J*','frozen NPZ, exact refs407','B_SMALL_ROUTE_CHECKS.csv','b_existing_metrics.py','DERIVED','PASS_SMALL_CHECKS','Input-bound numerical optimization, not native trajectory','53 exact refs unavailable; full new analysis not run'),
 ('P1-03','取得・仮想利用可能','採用・切替・出発','tQ<=cut, fallback, dispatch','D10/D11','A_SMALL_CASES.csv','a_fixed_od.py','CONDITIONAL','CONDITIONAL','Operational timing scenario, not measured quantum availability','Actual dispatch behavior unvalidated'),
 ('P1-04','出発・訪問順','固定OD配送完了','a=e+T;s=max(a,r);c=s+102','A78 NPZ, D03','A_SMALL_CASE_TASKS.csv','a_fixed_od.py','CONDITIONAL','CONDITIONAL','Ideal uninterrupted service and departure-independent costs','Signal/congestion/reachability not modeled'),
 ('P1-05','モデル完了','固定OD定時率','I(c<=due_start+102), PE weighted','fixed demand, D03','A_SMALL_CASES.csv','a_fixed_od.py','CONDITIONAL','CONDITIONAL','Model timing mechanism and waiting absorption','Not observed customer handover'),
 ('P1-06','地域道路','妥当な地域速度・配送','geometry/dynamic acceptance gates','N0/N1 archived audits','ROAD_NETWORK_VERSION_HISTORY.csv','road_history.py:readback only','INVALID','FAIL','Network remains unaccepted','No new repair/diagnostic; no accepted regional run'),
 ('P1-07','B計画','B速度軌跡・DC','full-run match then frozen DC','no accepted matching trajectories','no B energy outcome','03_SERIES_B_NO_SUMO_FEASIBILITY.md','UNTESTED','HOLD','No B energy-saving claim','Route recovery alone insufficient; mass HOLD'),
 ('P2-01','文献材料試験','保持容量・保持率','reported 100cycles/1C LP/S200','Chen saved PDF Fig5g','C_LITERATURE_LOCATORS.json','pdftotext; c_conditional_checks.py','OBSERVED','CONDITIONAL_APPLICABILITY','Published lab conditions, not quantum-generated performance','Full-cell/pack transfer unvalidated'),
 ('P2-02','容量・保持率','参照比容量','121/.704;194/.99','SCENARIOS, literature locator','C_SUMMARY.json','c_conditional_checks.py','DERIVED','PASS_ARITHMETIC','Retention back-calculated proxy','Initial practical q_ref HOLD'),
 ('P2-03','材料・設計入力','T08mass/T09既知部材','Q=E/V;active/coating/foil/separator/liquid','SCENARIOS, PACK CSV','C_T09_COMPONENT_SMALL_CHECKS.csv','c_conditional_checks.py','CONDITIONAL','CONDITIONAL','Distinct design models, not two completed packs','Unknown BOM and footprint FAIL retained'),
 ('P2-04','既知mass＋未知δ','全mass差の符号','saving=b-delta','T09 known components','C_UNKNOWN_MASS_BOUNDARY_FIXTURES.csv','c_conditional_checks.py','CONDITIONAL','CONDITIONAL','Cancellation boundary, no invented unknown mass','Complete pack183 unknown'),
 ('P2-05','mass＋保存速度','Controlled-DC差','sum(max(W1+W2+W3+W4,0))/eta','T08/bridge, freeze','C_T08_SAVED_DC_AGGREGATE.csv','c_conditional_checks.py; frozen original kernel','CONDITIONAL','CONDITIONAL','Fixed trajectory model sensitivity','Regional/vehicle calibration and tail missing'),
 ('P2-06','量子材料解析','対象材料性能改善','No identified quantum intervention','Chen DFT is VASP, not QPU evidence','no experimental result','04_SERIES_C_CONDITIONAL_EVIDENCE.md','UNTESTED','HOLD','Potential research link only','No causal effect of quantum materials computation'),
 ]
 fields=['edge_id','from','to','variables_or_formula','input','output','implementation_or_evidence','evidence_class','audit_status','claim','unverified'];table('CAUSAL_PATH_EVIDENCE_MATRIX.csv',[dict(zip(fields,x)) for x in matrix])
 mt='\n'.join(f"|{x[0]}|{x[1]}→{x[2]}|{x[7]}|{x[9]}|{x[10]}|" for x in matrix)
 doc('05_CAUSAL_PATH_EVIDENCE_MATRIX.md',f'''
# 因果経路の証拠対応

OBSERVEDは保存された計算実行／文献測定を含むが、観測対象を列で明記する。DERIVEDは入力から再計算可能、CONDITIONALはモデル仮定、UNTESTEDは未検証接続、INVALIDは既存不適合。PASS等の監査判定と別軸であり、モデル内のDERIVEDを実世界因果実証にしない。

|ID|接続|証拠分類|主張可能な範囲|未検証|
|---|---|---|---|---|
{mt}

式・変数・元入力・出力・コード・判定を含む完全表は `CAUSAL_PATH_EVIDENCE_MATRIX.csv`。各source path／SHAは `SOURCE_INVENTORY.csv` と `*_SOURCES.json`、行位置は各検算CSVで対応する。

因果経路1は取得・品質の保存計算と、仮想政策・固定OD配送成果のモデル内介入を接続する。地域速度・実配送・DCへは未接続。因果経路2は文献材料参照→設計会計→未知mass境界→固定速度DCという条件付き接続。入口の量子解析→材料改善と、出口の実EV妥当性は未検証。

QAOA成功64の選択条件を無視した集団効果や、異なるA/B/Cを結合した総合量子効果量を算出しない。実験計算の観測、モデル内反事実、外的妥当性を別の結果表へ分ける。
''')
 protocol={'version':'NO_SUMO_ALTERNATIVE_V1','status':'AUDIT_AND_DESIGN_COMPLETE_FULL_ANALYSIS_NOT_RUN','road_repair':'STOP_FOR_PRIMARY_THESIS_SCOPE','A':{'physical':78,'success_subset':64,'parents':26,'demand_groups':25,'policies':36,'A2_operations':2808,'A1_four_condition_refs':9216,'deadline':'original_due_start+102','model':'A_FIXED_OD_NO_SUMO_V1','primary':'F_PE','secondary':['F_count','completion_time','return_time','slack','departure_boundary'],'missing':'fixed denominator;unknown point null with bounds'},'B':{'physical':460,'parents':26,'demand_groups':25,'settings':8,'measurement_reps':10,'references':36800,'primary':'sampled_best_OD_seconds_minus_fixed_classical_initial','exact_reference_available':407,'exact_reference_missing':53,'energy':'B-E3_PRIMARY_NO_ENERGY_EFFECT_CLAIM','customer_deadline':None,'gap_denominator':'407 inputs, not route-recovery subset'},'C':{'scope':'conditional saved-trajectory mass sensitivity','T09_complete_mass_missing':183,'footprint_FAIL':1,'quantum_material_improvement':'UNTESTED'},'statistics':{'primary':'fixed finite roster descriptive paired contrasts','seed_reduce':'mean within physical problem/config, preserve seed distribution separately','cluster':'25 demand groups, all 26 parents nested, all scales/policies/reps carried together','optional_CI':'10000 whole-group percentile bootstrap95%; sensitivity to hypothetical group population, not deterministic measurement error','bootstrap_seed':20261102,'no_posthoc_sampling':True},'sensitivity':{'A_primary':'analytic departure boundary at unchanged original deadlines','A_optional_OD_multipliers':[0.8,1.0,1.2],'OD_multiplier_interpretation':'illustrative model stress; not calibrated traffic distribution','C_unknown_mass':'delta relative to b, no physical prior inferred','B_primary':'all460, exact407 subset separately, preserve unsupported53'},'prohibited_in_this_run':['full_A_evaluation','full_B_evaluation','regional_SUMO','road_repair','QAOA','thesis_edit']};dump('ANALYSIS_PROTOCOL.json',protocol)
 doc('06_ALTERNATIVE_ANALYSIS_PROTOCOL.md','''
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
''')
 total=sum(js(O/(x+'_SUMMARY.json'))['checks'] for x in ['BASELINE','A','B','C','ROAD','TOY']);times=[]
 for label in ['BASELINE','A','B','C','ROAD','TOY']:
  d=js(O/(label+'_SUMMARY.json'));m=d['metrics'];times.append(f"|{label}|{d['checks']}|{m['wall_s']:.6f}|{m['max_RSS_bytes']:,}|")
 doc('07_FINAL_RECOMMENDATION_AND_NEXT_STEPS.md',f'''
# 推奨方針・次の実装・論文への反映

**案2：既存データ中心を採用することを推奨。固定モデルを主対象とする条件付きGOで、地域配送・実EV電費の実証はNO-GO。** 道路修復は主研究工程から停止する。B-E2は必須ではなく独立補助候補に留める。

|比較項目|案1 SUMO継続|案2 既存データ中心|案3 解析電力量も追加|
|---|---|---|---|
|目的との対応|地域交通を含む伝達を狙えるが未成立|取得・政策・OD完了と材料mass感度の成立境界を明示できる|Bの電力量への仮定依存伝達も検討可能|
|因果経路1|全接続を将来対象、現状未実施|計画→政策→固定OD成果まで、DC接続未検証|合成／解析モデル内でのみDC接続|
|因果経路2|道路修復自体は量子材料改善を証明しない|既知会計・未知mass境界・保存速度DCを整理|同じ材料限界が残る|
|追加データ|道路mapping、動的受入、全OD・参照再計算、対象車検証|主モデル計算には追加実測不要|共通mass採用と速度・加速等の工学根拠／感度|
|費用|全域修復工期・成功確率不明|数値表計算中心、具体的脚加算量を定義可能|中程度の新実装・仕様検証、効果の仮定依存が増す|
|再現性|未採用道路に依存し現状HOLD|入力・式・版を固定し小検算で照合|パラメータ／合成速度を別版保存すれば条件付き|
|論文の主張|現状は道路不適合と未実施のみ|モデル内機構・影響消失／逆転境界|解析仮定下の推定まで、実電費改善でない|
|修士研究の限界|修復自体で研究範囲・費用が拡大|現実交通・実EV・量子材料改善へ一般化できない|追加仮定による見かけの接続を避ける必要|
|採用判定|NO-GO／主工程停止|**CONDITIONAL GO・推奨**|HOLD／別目的で必要性を再判定|

選定理由は容易さではなく、目的に対する識別範囲と証拠の整合である。地域交通を再現できない状態で速度やmassを補作して効果を作るより、モデル内で何が成立し、どの接続が未検証かを直接説明できる。因果経路全体を実証したという元の主張がある場合は縮小が必要となる。

## 次回実装の順序と予算

06の台帳→A固定OD→B全入力計画指標→C条件付き整理→対応集計を新しいanalysis領域へ実装する。Aの政策2,808判断＋64成功例4条件9,216参照、B36,800計画参照を評価するのは**次回以降**。本作業では実行していない。入力は新SOURCE_INVENTORYと元SHAをそのまま固定し、修正が必要なら版を分ける。

新規科学計算の規模はA約318経路5脚、B全参照約159万脚の加算で、経路探索・量子計算は不要。全件wall予算は未実測でHOLD。今回の監査・少数例の測定は以下。importを含むCPU累積とmain内wallの境界差、process peak RSSに注意する。

|処理|独立照合数|wall秒|最大RSS bytes|
|---|---:|---:|---:|
{chr(10).join(times)}

合計{total}照合で不一致0（別単位のfixture・hash・構造検査の合計で、科学標本数ではない）。全件計算の処理時間・メモリ・失敗率として外挿しない。次回の少数batch計測後に数量根拠付き予算を決め、改善や有意差が出るまで試行数を増やさない。

## 未解決事項とGO条件

- A：固定OD／理想連続サービスの条件付き妥当性を本文に明示。全件adapterは未実装。nativeの作業観測HOLDを固定ODの式で解除しない。
- B：厳密407／未確定53、資源scopeの欠測、支持空間と初期解、raw採用規則を保持。電力量と顧客定時率は結論対象外。全460を維持し、回収subsetだけを主分析にしない。
- C：T09完成mass183HOLD・全面対向1FAIL、保存N0速度の地域妥当性留保、量子材料改善未実証を保持。
- 道路：修復停止後もN0/N1受入FAIL。実地域を妥当に表すという主張が必要になった場合は案1の別工程を新たに設計する。

## 論文への反映方針（今回はファイル編集なし）

方法：動的SUMO評価から、版固定ODの離散事象時刻計算へAのestimandを変更し、理想サービス・時間不変費用・D03・D10/D11を記す。Bの支持・seed・CPU/誤差・参照欠測、Cの2種会計と固定速度条件を分離する。

結果：保存計算性能／今回検算／今後の全件モデル評価を区別。Aの36政策と4条件、Bの全460とexact407、Cの既知差・δ境界・保存速度DCを別表にする。地域配送完了やB電費の未実施欄を空白ではなく明記する。

考察：待機吸収、期限余裕、未取得切替、支持制限、未知BOM、正値化branchなどの媒介・消失条件を論じる。道路FAILは単なる実装問題として削除せず、外的妥当性と研究範囲縮小の理由にする。

結論：「量子計算により実EV配送／材料が改善した」「二つの因果経路を全て実証した」を避ける。計算結果と明示仮定の下での伝達・不成立境界を示し、量子材料→性能、計画→地域速度／DC、実pack／車両の未検証を残す。量子優位や実世界有意差を研究完了条件にしない。

## 4つの問い

Q1：地域SUMOの受入なしで、保存計算の取得・品質、仮想採用／切替、出発・訪問順、固定ODモデル完了・定時率・帰庫まで定量化可能。信号・混雑・実速度・走行DCは未検証。

Q2：文献参照値の算術、T08mass、T09既知部材、δ相殺／逆転、固定保存速度下のDC感度を再現可能。完成pack・実EV改善と量子由来材料改善は確定できない。

Q3：案2を完了するには新しい地域実験は不要。次回、固定OD全件adapter、B全入力の計画／資源結合、C条件別集計・必要時cluster感度を実装・検証する。実世界への主張を追加する場合のみ独立旅行時間／対象車／pack等の工学データと新実験が必要。

Q4：方法の評価モデルと仮定、結果の分母・未実施、考察の外的妥当性、結論の因果主張を上記範囲へ変更する。今回は旧docs・DOCXを変更せず、設計成果物を保存して停止する。
''')
 dump('DESIGN_SOURCES.json',list(SRC.values()))
if __name__=='__main__':main()
