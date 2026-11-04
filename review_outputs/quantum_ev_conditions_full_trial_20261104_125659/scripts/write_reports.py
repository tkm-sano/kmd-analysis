from pathlib import Path
import csv,json,hashlib,sys,textwrap,datetime
import pandas as pd
from docx import Document
O=Path(__file__).resolve().parents[1];R=O.parents[1];P=R/'review_outputs/no_sumo_full_analysis_20261102/run01';U=Path('/home/takuma/kmd-analysis-pre-clean-20261102-112222/untracked')
def md(n,s):(O/n).write_text(textwrap.dedent(s).strip()+'\n')
def tab(n,rows):pd.DataFrame(rows).to_csv(O/n,index=False)
def markdown_table(frame):
 cols=list(frame.columns);out=['|'+'|'.join(cols)+'|','|'+'|'.join(['---']*len(cols))+'|']
 for row in frame.itertuples(index=False,name=None):out.append('|'+'|'.join(str(x).replace('|',' / ').replace('\n',' ') for x in row)+'|')
 return '\n'.join(out)
run=json.loads((O/'ANALYSIS_RUN.json').read_text());q=pd.read_csv(O/'PATH1_QUALITY_COMPARISON.csv');ss=pd.read_csv(O/'PATH2_SENSITIVITY_SUMMARY.csv');bounds=pd.read_csv(O/'PATH2_BOUNDARY_RESULTS.csv')
md('SOURCE_AUTHORITY_AND_CONFLICTS.md','''
# 根拠の優先順位と矛盾の扱い

1. 今回の依頼（2026-11-04）：寄与条件へ重点移行、定時配達率を主指標から除外、既存境界維持、全変更をtrial提案とする。正式記録は変更しない。
2. 最新方針との整合確認：poster_policy_revision_20261104/run02/01_POLICY_AND_SCOPE.txt は条件候補・制約・未接続を重視し、インタビュー・RIQ・M1作成を工程から外している。今回も新しい面接結果を作らない。
3. 現行数値の主系列：no_sumo_full_analysis_20261102/run01 の全件CSVと、その上流NPZ・保存計画・SCENARIOS.json・保存速度。新規解析はハッシュを確認し、Bの全目的値とCの質量・DCを再計算した。
4. 正式凍結・旧ガイド：数式と過去の位置付けの根拠である。READMEの定時率・面接中心、QUANTITATIVE_GUIDEの時間窓あり・R4=99を、現行Bへ適用しない。旧正式量子は3/4顧客、現行Bは3/4/5/25/100/125である。
5. 原稿：tmp_RsrchMstrDc_1026_results_integrated.docx は5章に現行A/B/Cが入り、旧節を付録Bに保存し、11月3日統合記録が指すファイルであるためtrialの元に選定した。更新日時のみの選択ではない。tmp_RsrchMstrDc_1026_revised.docx と revisions/v07_results_integrated.docx も候補として照合対象にした。

旧レビューのPASSは、当時の算術・再現範囲に限定する。研究解釈CONDITIONAL、道路N0/N1 FAIL、T09完成pack HOLD、全面対向1件FAILを優先的に保持した。旧「新規計算禁止」「論文編集禁止」は当時のタスク境界であり、今回依頼はtrial内の軽量分析・複製編集を許可している。ただし物理モデルの凍結仕様は変更しない。

文献は11月2日の未同定表より、11月3日のREFERENCE_UPDATESと今回の一次照合を優先する。Papachristos2018の元引用意図は未確定のままである。

AGENTS.md は祖先3階層と対象リポジトリ（環境・第三者ツールを除く探索）で該当を確認できなかった。既存Git未追跡ファイルは開始時に存在しており、本trialで生成したものと区別してGIT_STATUS_START.txtに保存した。
''')
md('RQ_REDESIGN_TRIAL.md','''
# 研究目的・RQのtrial提案

研究目的は、量子計算の技術的能力が配送計画または電池材料評価を通じてEV配送システムの設計・運用へ反映されるための条件と、その伝達を妨げる制約・未接続を、保存実験と一次文献に基づき特定することである。改善量の実証や量子優位の確認を研究成立の必須要件としない。

|ID|trial研究質問|既存実験の回答範囲|暫定判定|
|---|---|---|---|
|RQ0|量子計算は、どのような技術能力・適用・効果成立条件の下で、対象EV配送システムへ寄与し得るか。|Bの品質と保存CPU工程、Cの条件付き質量・DC、文献の候補接続。実運用全体は未検証|CONDITIONAL|
|RQ1|同一の配送問題で、量子アルゴリズム由来の解が古典対照を上回り、許容時間内の配送計画へ採用されるために何が必要か。|B全460、厳密407、8設定10測定rep。統一end-to-end時間・実機速度優位は不足|CONDITIONAL／時間閾値HOLD|
|RQ2|材料入力の変化がセル・パック・車両質量を介して走行時DCの差へ伝達される条件と、相殺される境界は何か。|T08連続入力・固定速度、T09既知部材差。完成品・量子由来改善は未検証|CONDITIONAL|
|RQI|両経路の寄与が技術能力の改善だけでは決まらないのはどの接続条件によるか。|技術→適用→結果の三層とHOLDの比較。社会制度の因果効果は測定していない|解釈のtrial提案|

A=技術能力条件、B=適用条件、C=効果成立条件とする。観測条件（保存データ上成立）、仮定条件（モデルで固定）、必要条件（指定した成果定義から要請）、十分条件（明示モデル内の不等式で保証）を台帳で分ける。必要条件を一つ満たしても全経路の十分条件としない。

旧目的の「需要充足と電力量の両立」「定時率をサービス水準の主指標とする」記述はこのtrial主分析と整合しない。旧成果を削除せず履歴・指標選定根拠として保存する。既存の正式RQ・H1〜H3の文言は上書きしない。
''')
indicators=[
('OD道路旅行時間','s','Σ travel[πk,πk+1]。待機・サービスを除く','RQ1','B36,800全行','同一NPZ・古典初期','実走行時間・電力量とは異なる'),
('最適性ギャップ','%','100*(T−T*)/T*','RQ1','407入力、53未確定','保存厳密参照','未知53を除く明示分母。下界gapと混同しない'),
('最適値一致率','%','exact objective fraction一致数/厳密参照測定数','RQ1','407×8×10','同一問題のT*','同じ訪問順の率ではない'),
('古典初期との差','s','Tsample−Tinitial。負が改善','RQ1','460×8×10','固定初期解','最強古典対照・同一予算の保証なし'),
('保存best実行可能率','%','独立検査可行計画数/保存計画参照数','RQ1','36,800','順列・216PE・帰還32,400s','shots単位・現実配送成功率ではない'),
('求解工程時間','s','FIT/selected/final validation/initial をscope別保存','RQ1','保存CPU wall/CPU。一部工程未保存','同scopeのみ','QPU時間・end-to-end speedup算定不能'),
('量子計算資源','count','符号化、層、shots、反復、ゲート等を別項目','RQ1','shots8192、p2/p3等','同一符号化・同一回路条件','compiled回路・誤り訂正物理資源HOLD'),
('正極参照比容量','Ah/kg','T08:保持率からの逆算参照。q_eff=q*u','RQ2','171.875〜195.959596','同一試験系列の条件付き参照','実用全電池・量子計算結果ではない'),
('平均全電池電圧','V','gross Wh/セル容量総和Ah','RQ2','3.5仮定','同電圧比較','Li対極の試験窓と別'),
('セル質量','kg/cell','両極塗工材/100+0.19','RQ2','T08簡略モデル','同固定部材','T09未測定外装を補完しない'),
('パック質量','kg','100*mcell+15+additional','RQ2','T08算術、T09完成品NULL183','同会計境界','既知部材合計を完成packとしない'),
('車両・走行質量','kg','共通非pack+新pack。走行質量=vehicle+55','RQ2','T08非pack走行質量1043.888888889','同一軌跡・同積載0','車両総質量は本研究の空荷＋運転者条件に限定'),
('Controlled-DC','Wh','Σ max(W1+W2+W3+W4,0)/0.9','RQ2','保存観測窓460×2Crr×入力','同軌跡・同Crr','回生なし・補機範囲外・末端1s未知'),
('DC削減率','%','100*(ΣEref−ΣEalt)/ΣEref。個別率平均を別報告','RQ2','PATH2_SENSITIVITY_SUMMARY','同cohort LP','総量比と個別率平均を混同しない'),
('ゼロ効果境界','kg/fraction/V','mass saving=0 または Eref−Ealt=0','RQ2','T08/T09設計別','共通対照','任意の目標0.1/0.25/0.4/0.5%と区別'),
('定時配達率（補足）','%','旧Aの期限内需要PE/総需要PE','主RQ非対応','旧A2808等を保存','旧固定OD政策','今回の主指標から除外。取得率で代用しない')]
tab('INDICATOR_DEFINITIONS.csv',[dict(indicator=a,unit=b,calculation=c,RQ=d,data=e,comparator=f,limitation=g) for a,b,c,d,e,f,g in indicators])
md('INDICATOR_DEFINITIONS.md','# 指標定義（trial提案）\n\n全16指標の単位・算式・RQ・取得状況・対照・限界はINDICATOR_DEFINITIONS.csvに記載する。\n\nBは入力内10repを平均してから入力を等重みに集計する。最適値一致率は保存有理数による一致を用い、丸めた秒数の一致で代替しない。試行間SDは10測定repの記述であり、学習10回の分散ではない。親26・需要群25の依存を残し、36,800を独立した都市標本としない。\n\n定時配達率は主指標から除外するが、デポ帰還期限・サービス時間・固定需要の維持というモデル条件は維持する。数値欠測、非適用、物理ゼロを分け、空欄には理由を対応付ける。')
md('RESEARCH_BOUNDARY.md','''
# 研究境界（trial提案、元モデルは不変）

主対象は大田区の合成配送問題、単一デポDEP_006、車両割当・台数固定である。Bの1問題は単一車両による固定顧客集合の訪問順であり、都市全体の配送・車両割当を最適化したものではない。容量216PE、サービス102秒/顧客、計画出発0秒、デポ帰還期限32,400秒を維持する。途中充電、顧客再割当、台数増加、SOC再計画を含めない。

現行Bは顧客時間窓なし。旧Aおよび旧凍結量子実験の顧客時間窓あり（開始期限・幅7,200秒）は補足系列であり、主Bに混ぜない。帰還期限が残ることと、定時配達率を主指標にしないことは両立する。道路旅行時間の最小化に待機・サービスを加算しない。

Cは共通保存速度・1秒刻み、右端速度による距離、隣接速度二乗差の慣性項、平坦、回生なし、補機範囲外、回転等価質量61kg固定、駆動効率0.9、空荷0kg・運転者55kgを維持する。gross20kWhを質量設計、usable18kWhをstock会計に用いる。末端1秒は未観測であり電力量を0補完しない。Crrの2条件は係数包絡であり、前後輪加重や信頼区間ではない。

道路N0幾何・N1動的受入の既存FAILを保持する。新規軌跡生成・背景交通校正・実車妥当性検証は実施しない。本trialの結果は研究用固定OD／観測窓での条件付き結果である。新しい社会制度・利用者行動の因果効果は同定していない。
''')
exp=[
 dict(series='A_LEGACY_WINDOWS',purpose='計画取得・採用時刻政策の固定OD診断',inputs='4顧客78、量子取得64／未取得14',scale='旧R1=4顧客',methods='古典のみ／量子優先、機構4条件',trials='36政策×78=2808、機構9216行',outputs='A_POLICY_DECISIONS_2808.csv等',metrics='旧PE定時率・採用時刻・帰還。今回主指標外',environment='元量子理想状態ベクトル／固定OD；保存元資源別表',reproducibility='旧全件独立検算の記録をハッシュ確認。今回A率会計を別途点検',authority=str(P)),
 dict(series='B_CURRENT_NO_WINDOWS',purpose='現行8設定の解品質・保存CPU資源',inputs='460固有NPZ、26親・25需要群、exact407／HOLD53',scale='3/4/5/25/100/125；78/78/78/78/78/70入力',methods='mirror5、Grover P2/P3、active grid；古典初期・orbit DP・global exact',trials='8設定×460×10測定rep=36800、fit3680',outputs='B_PLAN_REFERENCES_36800、B_RESOURCES_PER_FIT等',metrics='OD秒・gap・一致率・可行性・scope別CPU時間',environment='MPS/DP/MCのCPUシミュレーション、当時統一環境HOLD',reproducibility='今回全計画の原NPZ目的値・順列・容量・帰還を再検算。solverやQAOAは再実行しない',authority=str(P)),
 dict(series='C_T08',purpose='材料入力→簡略質量→固定速度DC',inputs='qLP171.875,qS195.959596；3scenario；gross20kWh',scale='4464行、うち古典2760=460軌跡×3×2Crr',methods='LP/S/同一対照の簡略会計、Controlled-DC',trials='744 dataset/method軌跡参照／465固有速度、独立標本ではない',outputs='C_T08_ENERGY_FULL.csv',metrics='セル・pack・走行kgと観測窓Wh',environment='保存速度、凍結Controlled-DC CPU再積分',reproducibility='今回T08全行massと古典920端点の再計算、連続49点45080行',authority=str(P)),
 dict(series='C_T09_BRIDGE',purpose='部材会計・未知部材差の境界',inputs='T09設計183、代表B015/B051、δ7probe、参照1200/1400kg',scale='183部材行＋25760bridge行',methods='独立有理数部材式／既知差−未知差／固定速度DC',trials='460×2設計×7probe×2Crr×2mass；独立実験数ではない',outputs='C_T09_COMPONENTS_183、C_BRIDGE_MASS_DC_FULL',metrics='既知kg・相殺kg・W1〜W4・Wh',environment='元公開電極資料と条件付き会計、完成pack質量はNULL',reproducibility='今回183×8成分の独立有理数照合、25760行の質量・成分分解会計を照合',authority=str(P))]
tab('EXPERIMENT_INVENTORY.csv',exp)
md('ADDITIONAL_ANALYSIS_DECISIONS.md','''
# 追加分析の必要性と実行判断

|課題|分類|今回の実施|理由・次作業|
|---|---|---|---|
|B品質・既存最適参照|1 既存再分析|全36,800を原NPZ・保存測定と照合|保存値で結論を判定可能。学習の再実行不要|
|B時間工程|1 既存再分析|fitを一意化し工程別集計|保存scopeからend-to-endを補完しない|
|C連続入力と任意目標の閾値|2 軽量計算|既存端点内49点、460速度×2Crr、利用率49点、二分法|離散端点のみでは連続条件の数値表示がない。新規SUMO不要|
|T09既知成分|1 既存再分析|183×8成分を独立有理数式で照合|完成packの不足部材を埋める計算ではない|
|A定時率|1 保存成果の監査|旧結果保全・率会計点検|主指標外であり新たな政策分析を追加しない|
|厳密参照53|3 新規の大規模計算が必要となり得る|未実行|現結論に必須でなく、既存のsolverログだけで新たな厳密解を確定できない。53入力の再求解はn=100/125。環境・停止時間・完了率データ不足のため信頼できる所要時間／必要RAMは算定不能。まず各1代表を制限付きpilotする提案のみ|
|公平な古典・量子end-to-end時間|4 現データで判定不能|HOLD|同環境・同予算・前後処理・全測定・入出力を含む新測定が必要。実行時間・QPU利用可能性は未確認|
|compiled深さ・ゲート・物理qubit|4 現データで判定不能|HOLD|対象ハードウェア、gate set、配置、誤り訂正等の仕様が不足。外挿しない|
|T09完成packと実車効果|4 現データで判定不能|HOLD|外装・タブ・余白・pack構造・電力/熱/寿命/安全の工学入力が必要|
|新規地域交通・実車・量子材料実験|5 今回の範囲外|未実行|本trialの条件整理には不要。入力の外的妥当性は継続HOLD/FAIL|

追加計算は決定論的で乱数seed非適用。元のB測定seedは各計画行に保存されており今回再生成しない。今回の環境・wall/CPU/RSSはANALYSIS_RUN.json、実コードはscripts/analyze.py、入力hashはSOURCE_BASELINE.csvである。大規模実験を既存結果から代替できる範囲は再実行していない。所要時間が不明な大規模実験について架空の見積値を与えない。
''')
md('PATH1_METHOD_AUDIT.md','''
# 経路1の比較条件監査

主系列Bを時間窓なしとして固定した。全36,800保存参照を、上流の460入力NPZと保存測定JSONに接続し、訪問順・目的値・容量216PE・帰還32400秒を検算した。厳密証明ファイル407と未確定53の出典hashを確認した。証明solverの再実行ではない。

目的はデポ発着の有向OD旅行時間総和である。探索中の平均エネルギー/CVaR等と最終sampled-bestのOD秒を区別する。raw bestをmin(initial,sampled)で置換していない。保存8192shotsのbestが全行可行であることは、全raw shotが可行なことを意味しない。raw invalid countは一部未保存である。

mirror5は同一初期経路の対称位置の部分swapを用い、支持は2^floor(n/2)である。全顧客を保持するが全n!順列ではない。同支持の古典chain-DP最適値と初期目的値が一致していたため、この支持の内部で初期目的を上回る余地がない。Groverは一様順列初期状態・全順列支持であり、同じ初期状態・同じ実装予算の比較ではない。activeはt={0,.5,1}の限定gridである。

mirrorはp2、Groverはp2/p3、activeはp3であり、最適化の開始点・評価上限・精度検査はsourcesにピン留めした元PROTOCOLを参照する。mirrorの関数評価上限64、Grover68、active3gridという違いを保持する。保存trace件数をoptimizer反復回数へ読み替えない。

測定10repは各学習済み状態の測定反復であり独立学習10回ではない。入力内平均→規模内等重みを主とし、厳密407のgap分母と全460の初期差分母を分ける。25需要群・26親の依存と非確率抽出を維持する。規模間の差は規模だけの因果効果ではない。

旧Aは時間窓あり、小規模の別符号化・理想状態ベクトルであり、R0=3/R1=4取得78/64等は旧系列としてのみ示す。旧R4=99と現B R4=100を混合しない。
''')
md('PATH1_RESOURCE_REQUIREMENTS.md','''
# 量子計算資源の確認範囲

|由来|確認できる条件|確認できない条件|
|---|---|---|
|符号化|旧正式小規模は位置表現n²二値変数（3/4で9/16）。B mirrorの有効二値方向はfloor(n/2)、支持2^floor(n/2)。Grover支持n!|支持サイズ・シミュレータ変数数を実機論理qubit数と同一視できない|
|アルゴリズム|B mirror p2、Grover p2/p3、active p3。8192shots/測定rep、10rep/fit。3680fitを一意に数える|全学習回路のshots総数・実optimizer反復・compiled回路深さとgate数の一貫した記録|
|計算アーキテクチャ|binary matching MPS、subset DP／certified MC、active-label MPS。保存backend two-site演算・bond等をscope別に追跡可能|backend演算をnative量子gateとみなす換算、DP/MCのCPU時間からQPU時間への換算|
|量子ハードウェア|本実験はCPU上の理想化・近似シミュレーション|ハードウェア接続、native gate set、compiled depth、noise、誤り訂正、論理／物理資源|

必要資源はアルゴリズム・符号化・許容誤差・サンプリング成功確率・ハードウェアに依存する。pは層数であり回路depthそのものではない。旧n²を現行全Bへ適用しない。n=125のmirror有効二値方向62という数を「62論理qubitで配送全探索」と表現するのは不適切である。

全順列を一意に表すための情報量下界ceil(log2(n!))は数学上書けるが、回路・補助qubit・実装コストを与えないため、本trialではハードウェア要求値として数値採用しない。誤り耐性物理資源を断定する根拠はない。Delgado等の材料計算の資源数を経路問題や本T08へ移植しない。
''')
md('PATH1_CONTRIBUTION_CONDITIONS.md','''
# 配送経路計算の寄与条件（trial提案）

## 技術能力条件A

同一の目的・制約・入力について可行解を取得し、明示した古典対照よりT_Q<T_Cを満たすことが、旅行時間改善を寄与と定義する場合の必要条件である。実機一般の必要条件ではなく、本比較指標に対する条件である。最適値T*に一致した場合、それ以上の旅行時間改善余地は当該目的関数内で0である。

Bのmirror5は全460で初期解と同じ目的値であり、支持内最適値も初期解と一致する。改善には、改善解を含む支持、そこへの振幅・探索能力、取得の成功が必要となる。支持拡張だけで十分とはいえない。activeは保存grid全460でt=0が選ばれたという観測であり、連続角最適化一般の不能を示さない。

Grover P2/P3は3〜5顧客で保存厳密参照に一致したが、25/100/125顧客では平均初期差が正であった。R1/R2の初期改善平均は約0.160/1.099秒である。これを最強古典への優位としない。厳密参照53入力不足、精度・状態準備・回路資源不足の条件が残る。

## 適用条件B

計画作成に許される時間をH_planとすると、T_pre+T_fit+T_measure+T_validate+T_post+T_transfer <= H_plan が採用の時間条件となる。配送計画の締切や入出力時間は未確認であり、数値閾値H_planはHOLDとする。CPUのfitのみを左辺に代入しない。旧Aの仮想T_Qやlead timeもCPU実測値ではない。

計画が取得され、静的制約を満たし、実際に採用され、道路の実行可能性と需要の同一性が維持されることが接続条件である。途中充電や割当最適化を追加して改善を作らない。旧道路受入FAIL、現B計画の速度・DC未接続を保持する。

## 効果成立条件Cと不成立

T_Q<T_Cと時間内採用は、本研究の固定OD下で旅行時間の短い計画を使う条件候補である。実交通の総移動時間短縮や省電力の十分条件ではない。目的が旅行時間である以上、同一軌跡・エネルギー評価なしにDC改善を帰属できない。

解品質が同じで両者とも締切内なら、求解時間差が運用結果へ伝達しない場合がある。ただし短時間化が計算費用等に別の価値を持つ可能性までは否定しない。品質未改善、予算不足、未採用、道路未妥当、データ不足を分ける。「量子一般に効果がない」という結論は支持されない。

判定：保存品質の算術PASS、固定ODとCPU方式に限定した知見CONDITIONAL、end-to-end／QPU速度優位・実配送寄与HOLD。
''')
md('PATH2_MATERIAL_BRIDGE_AUDIT.md','''
# 材料計算との接続監査

Aは入力を変えたモデル結果、Bは文献に基づく条件付き材料シナリオ、Cは量子計算で実際に達成した物性・精度である。本trialの数値はAであり、参照の由来の一部がBに相当する。対象物質の量子計算機による実測・計算結果Cは保存されていない。

Chen et al.2020はVASP/DFTとLi対極セル実験を用いる。Fig5gにある1C・100cycleの容量/保持率を元に、旧研究がLP=121/0.704=171.875、S200=194/0.990を小数6桁参照195.959596 Ah/kgへ整理した。これは研究上の逆算参照であり、初回容量、Li在庫、実用黒鉛全電池容量、量子計算で予測した比容量ではない。温度、質量分母、活性化履歴等の未確認を保持する。

物性予測（電圧、反応・安定性、イオン移動等）と材料設計の採用、電極・セルの利用率、部材・安全設計、pack設計を別リンクとして扱う。Delgado et al.は候補計算経路であり、当該LP/S200への計算精度、材料選定の改善、電極実装を実証しない。

量子予測→設計選択→作製・評価→量産性能という未接続に対し、電極から配送DCへの条件付き計算を実施したことをもって遡及的な実証としない。対象の全電池平均3.5V、利用率、N/P、電力・熱・寿命・安全は別途証拠が必要である。
''')
md('PATH2_MODEL_VALIDATION.md','''
# T08/T09・Controlled-DC監査

T08：Q=20000/V。正極活物質=Q/(q*u)、正極塗工材=Q/(q*u*0.75)、負極活物質=1.1Q/360、負極塗工材=1.1Q/(360*0.98)。100セルで両極塗工材を分割し、0.19kg/cellを一度加え、pack15kgとadditionalを一度加える。gross20kWhは質量設計、usable18kWhは運転stockであり交換しない。保持率・ICEを利用率へ重ねて適用しない。

T09：183行で正極・負極活物質／塗工材、Al/Cu foil、separator、liquidを独立Fraction式で1464照合した。Alはface area/2×厚さ×2699、Cuはface area/2×厚さ×8960、separatorは最大face area×面密度。液量は両極の空隙とseparator空隙とextraを明示して加算する。使用密度4458/2200/1300kg/m³と両面規約は元モデル入力であり独立計測値の妥当性まで保証しない。

完成packは全183行でNULL。casing/tabs/foil margins/pack structureが未測定であり、残差を埋めない。T09_ROW_183の全面対向条件FAILを保持する。正負面積の必要条件が十分な製造・安全条件とはいえない。T08の0.19kgや15kgをT09既知成分へ再加算しない。

T08とT09は同じ完成品の代替予測ではない。比較できるのは会計境界が一致する部材と、条件を明示した差の相殺式である。T08のpack総質量を実測完成packとして採用しない。

Controlled-DC：W1=m*g*Crr(v)*ds、W2=0.5*rho*CdA*v²*ds、W3=0.5*m*Δv²、W4=0.5*61*Δv²。各区間の合計を正値化して0.9で割る。個別成分の正値化ではない。W2/W4は質量置換で共通でも、正値区間maskは変わり得る。成分分解はbaseline正値maskとbranch補正の和であり、branchを省いた単純比例は一般には成立しない。

今回、T08古典920端点について公開凍結kernelと区分線形式を照合し、最大差2.73e-12Whであった。最初の保存軌跡について別のscalar和も両端点・両Crrで照合した。これは実装Verificationであり実車Validationではない。末端1秒の未観測電力量を補完していない。
''')
md('PATH2_CONTRIBUTION_CONDITIONS.md','''
# 材料・車両経路の寄与条件（trial提案）

## 技術能力条件A

量子計算が対象物性を、設計上必要な精度・所要時間・資源で予測し、古典評価に対する追加的価値を持つことが量子への帰属を判断する条件候補である。対象材料での達成はHOLDである。モデルのq変更は量子計算の達成精度を表さない。

## 適用条件B

文献由来の半電池参照が実用全電池へ移転し、平均電圧・利用率・N/P・部材・熱・電力・寿命・安全が両立し、その性能が同じgross容量で軽量化へ使用されることを条件とする。性能向上を容量増加へ配分すれば、本trialの質量経路の結果はそのまま適用できない。T08は簡略会計、T09は既知部材のみである。

## 効果成立条件C

T08の共通V、負極、部材を固定すれば、q_S*u_S>q_LP*u_LP が正極塗工材の軽量化の必要十分条件である。未知・追加部材が変わる一般の場合、b=既知または簡略会計のLP−S差、δ=未知／追加S−LP差として、全質量差はb−δとなる。δ<bで軽量、δ=bで相殺、δ>bで逆転する。これは指定質量会計内の必要十分条件であり、実用電池性能や量子寄与の十分条件ではない。

T08の相殺δは5.448297415kg、qS固定で利用率境界0.877094072、平均全電池電圧境界3.193155684Vである。電圧変更時は負極の必要Ahも変わる。T09代表B015/B051の既知差境界は9.722608121/5.977891152kgである。完成packの未知差δは未測定なので、いずれも無条件な軽量化保証ではない。

同一保存速度・指定質量区間・Crrの下ではDCの質量傾きが正であることを920条件で確認した。従って本区間内では質量相殺とDC差ゼロが対応する。全走行様式への一般命題としない。固定部材が共通であれば正極由来の絶対kg差を消さないが、総質量に対する割合を希釈する。S側の追加部材差は相殺・逆転を生じ得る。

q=171.875〜195.959596、u=1、V=3.5の連続分析で、終点の総量加重DC削減率はCrr下側0.412579010%、上側0.413590412%であった。0.25%という説明用任意目標にはq約185.705045/185.668669 Ah/kgが必要である（同一460軌跡の総量比）。この目標は採用基準ではない。0.5%の交点は今回区間内にないため範囲外HOLDであり、外挿しない。

判定：算術PASS、質量・DC感度CONDITIONAL、完成pack／実EV／量子由来改善HOLD。
''')
ops=pd.read_csv(O/'PATH2_OPERATION_INTERACTIONS.csv');ot=[]
for rc,g in ops.groupby('rolling_case'):
 ot.append({'rolling_case':rc,'trajectories':len(g),'mean_saving_percent':g.saving_percent.mean(),'min_saving_percent':g.saving_percent.min(),'max_saving_percent':g.saving_percent.max(),'W1_sum_Wh':g.W1_mask_DC_Wh.sum(),'W3_sum_Wh':g.W3_mask_DC_Wh.sum(),'branch_sum_Wh':g.branch_correction_Wh.sum(),'correlation_saving_distance':g.saving_Wh.corr(g.distance_km),'correlation_saving_restart':g.saving_Wh.corr(g.restart_count),'interpretation':'DESCRIPTIVE_NOT_INDEPENDENT_CAUSAL_EFFECT'})
tab('PATH2_OPERATION_SUMMARY.csv',ot)
md('PATH2_OPERATION_INTERACTIONS.md','''
# 走行条件との交互作用

PATH2_OPERATION_INTERACTIONS.csvは460保存速度×2Crrの距離、移動時平均速度、停止後再発進数、正の速度二乗差総和、質量傾き、W1/W3寄与、branch補正を記録する。PATH2_OPERATION_SUMMARY.csvは規模混合の記述的集計であり、因果回帰ではない。

速度は転がり係数・空気抵抗・dsを介し、加減速はW3/W4と正値maskを介し、停止・再発進は繰返し加速の仕事を介して関係する。ただし同一走行条件を操作した独立実験ではないため、距離や再発進との相関を個別の因果効果と呼ばない。

W2とW4の直接質量差は0である。W3のsigned総和は末端速度で望遠和になり、小さくても正値区間における加速寄与は大きくなり得る。baseline maskにおけるW1/W3差とbranch補正を用い、実DC差との保存会計を確認した。回生・勾配・補機・積載を新設していない。

460全軌跡、両Crr、T08のLPからSまでの質量区間において、区分線形凸関数E(m)の最小片側傾きが正である。これが今回の質量減少→DC減少というモデル内条件である。異なる速度応答、回生制御、空調、車両効率までの一般化は未検証である。
''')
conds=[
('A1','技術能力','解品質・探索支持','対象物性の予測精度','アルゴリズム・計算仕様','必要条件候補','B同支持改善余地0、Grover規模差','対象物性精度HOLD','CONDITIONAL'),
('A2','技術能力','全求解時間・資源','物性計算の時間・資源','計算アーキテクチャ','未検証条件','CPU工程のみ、QPU不明','文献候補、対象未達成','HOLD'),
('B1','適用','同需要・制約・採用締切','同容量・実用セル・pack設計','システム設計','仮定／必要条件候補','固定割当・単一車両、予算不明','20/18kWh、完成pack不明','CONDITIONAL'),
('B2','適用','実行可能な道路・計画採用','未知部材・電力熱寿命安全','対象システム','未検証条件','道路N0/N1 FAIL、B_DC未接続','未知mass183・対向1FAIL','HOLD'),
('C1','効果成立','T_Q<T_Cかつ採用','b−δ>0かつEの正のmass傾き','運用・モデル','指定モデル内条件','旅行時間目的のみ','920条件の正傾き／相殺式','CONDITIONAL'),
('C2','不成立','支持内改善余地0／時間超過／未採用','δ=b相殺、δ>b逆転','伝達過程','観測／仮定を区別','mirror目的値同一、時間超過は未観測','boundary算定、未知δは未測定','CONDITIONAL'),
('D1','一般化','実機・実配送の優位','量子由来完成pack・実車削減','外的妥当性','未判定','end-to-end未測定','量子→材料未検証','HOLD')]
tab('CROSS_PATH_CONDITIONS_MATRIX.csv',[dict(condition_id=a,layer=b,path1=c,path2=d,depends_on=e,logic_kind=f,path1_evidence=g,path2_evidence=h,status=i) for a,b,c,d,e,f,g,h,i in conds])
md('INTEGRATED_CAUSAL_MODEL_TRIAL.md','''
# 統合概念因果モデルのtrial提案

この図は作用経路と証拠状態の表現であり、構造方程式の推定や実証因果グラフではない。実線も実世界の因果証明ではない。Eは保存比較、Mはモデル算術、Hは未検証接続を表す。

```mermaid
flowchart LR
 Q1[量子アルゴリズムの能力] -->|E: BのCPUシミュレーション| P1[解品質・可行解・計算工程時間]
 P1 -.->|H: 総時間予算・採用| A1[配送計画への適用]
 A1 -.->|H: 道路・走行・需要同一性| O1[運用上の総移動時間等]
 Q2[量子材料物性計算の能力] -.->|H: 対象物性精度と設計価値| D2[材料・電極・電池設計]
 D2 -.->|H: 実用化・未測定部材| M2[セル・パック質量]
 M2 -->|M: 共通非packを固定| V2[車両走行質量]
 V2 -->|M: 固定速度・Controlled-DC| O2[観測窓DC電力量]
 C1[単一デポ・固定割当・帰還期限] --> A1
 C2[同容量・利用率・平均電圧・未知質量差] --> M2
 C3[速度・加減速・Crr・評価境界] --> O2
```

旧M0の定時配達率を主たる到達変数とする構造は、trial本文では主分析から外す。旧図はsource DOCXおよび元研究記録に保全する。RIQやM1という調査成果の呼称を新たに付さない。B計画とC旧軌跡を共通母集団とみなす横断矢印も作らない。

A技術能力→B適用→C結果という三層が共通構造である。量子入力の改善を仮定しただけでは、各経路の未接続区間は埋まらない。質量相殺や支持制限は伝達制約として記述できる一方、制度・組織・採用行動の実証は未実施である。
''')
md('DISCUSSION_TRIAL.md','''
# 統合考察のtrial提案

両経路に共通するのは、技術能力の出力とシステム上の成果の間に適用過程が存在することである。配送では支持・解品質・計算工程・採用時点、材料では物性評価・設計選択・実用セル・未測定部材が媒介する。異なる指標を単一の量子改善率へ集約することはできない。

経路1の負の結果は、今回の支持や限定grid、古典初期解、CPUバックエンドの組合せに関する情報である。mirrorが改善しないことは、初期が同支持で最適であるという観測と整合する。Groverの小規模での最適値一致と大規模での悪化は、アルゴリズム・探索・初期状態・規模を条件として説明すべきである。量子一般の不能や可能性の確率へ読み替えない。

経路2では、材料入力の改善があっても利用率・電圧・固定部材の配分・追加部材が伝達を制約する。共通固定部材は絶対差を消さず相対差を希釈し、材料別追加部材差は絶対差を相殺する。ゼロ効果境界は質量会計から求められるが、現実の未知部材差が境界のどちら側かはまだ不明である。

寄与条件という観点の価値は、改善を確定できないときでも、改善余地が支持にない場合、計画へ反映されない場合、部材差で消える場合、単に証拠がない場合を分けられる点にある。この分類は対象の限定モデルに関する学術的説明案であり、社会技術的移行の成否を実証するものではない。

RQ0への暫定回答は、計算能力のみではなく、対照より良い出力、その適用可能性、効果の伝達が同時に満たされる必要がある、というものである。RQ1は品質条件を部分的に評価できたが公平な時間・実機資源はHOLDである。RQ2はモデル内の相殺境界と連続DC感度を算定できたが実用完成品と量子への帰属はHOLDである。RQIの三層整理はtrialの解釈提案である。
''')
md('LIMITATIONS.md','''
# 一般化可能性と限界

- 地域：大田区由来の合成需要・固定ODであり、実注文・実交通へ校正された標本ではない。道路受入FAILを保持する。
- 経路：単一車両訪問順・固定割当であり、EVRP全体、途中充電、車群規模最適化ではない。旧時間窓あり系列を現Bへ移さない。
- アルゴリズム：mirror支持、active限定grid、Groverの学習・近似精度・初期状態に依存する。全量子手法や将来ハードウェアの優劣は判定できない。
- 対照：古典初期と同支持DPとglobal exactは役割が異なる。同一計算予算の最新古典最良法比較ではない。exact53は未確定。
- 時間・資源：保存CPU工程とQPU時間を区別し、公平なend-to-end speedup、compiled回路、物理qubitを算定しない。
- 材料：半電池由来の逆算参照、平均電圧・利用率・N/Pの仮定、T08簡略部材、T09完成pack欠測、電力・熱・寿命・安全に依存する。
- 走行：固定速度・平坦・回生なし・補機除外・空荷・観測窓。質量変化に対する速度応答・実車効率は未検証。
- 統計：固定有限cohortの記述であり、36,800計画、45,080感度行、10測定repを独立した実都市標本数としない。
- 文献：一次照合は明示した範囲であり網羅的レビューではない。Papachristos2018の引用意図と旧参考文献全体の精読はHOLD。
- 社会技術：組織・制度・採用行動・費用・受容性・環境LCAの因果効果を測定していない。三層の図は概念的trial提案である。
''')
# Explicit claim ledger: empirical arithmetic and interpretation have separate rows.
claims=[
('CL01','Bは460入力・8設定・10測定rep、36800保存best計画である','PASS','B cohort','EXPERIMENT_INVENTORY.csv;PATH1_QUALITY_COMPARISON.csv','既存成果の再確認','原NPZ460と保存JSON、検算NUMERICAL_CHECKS'),
('CL02','保存best計画は順列・容量・帰還条件を満たす','PASS','B no windows only','NUMERICAL_CHECKS.csv','既存成果の再確認','raw shot成功率・現実配送成功率は主張しない'),
('CL03','厳密参照は407で53未確定である','PASS','B certificate metadata/hash','PATH1_QUALITY_COMPARISON.csv;SOURCE_BASELINE.csv','既存成果の再確認','solver再求解ではない'),
('CL04','mirror5の目的値は全入力で初期解と同じである','PASS','B saved output objective','PATH1_QUALITY_COMPARISON.csv','既存成果の再分析','raw bestの初期解による置換なし'),
('CL05','mirrorの同支持内で初期解を上回る目的値改善余地がない','CONDITIONAL','保存matching orbitと古典DP','PATH1_METHOD_AUDIT.md;B_CLASSICAL_ORBIT_COMPARISON.csv','既存成果の再確認','全順列・量子一般の不能ではない'),
('CL06','activeは460入力の保存3点gridでt=0選択','PASS','限定grid','SOURCE_BASELINE.csv;B_ACTIVE_GRID_SELECTION.csv','既存成果の再確認','全角探索ではない'),
('CL07','Groverは3–5顧客で厳密参照一致、大規模側で平均初期差が正','CONDITIONAL','固定ODと保存CPU simulation','PATH1_QUALITY_COMPARISON.csv','既存成果の再分析','最強古典との優劣・規模単独の因果効果ではない'),
('CL08','量子方式は古典よりend-to-endで速い','HOLD','公平な求解時間','PATH1_RUNTIME_COMPARISON.csv','未解決事項','scope・環境・QPU未記録'),
('CL09','8192shots、p2/p3と保存scope別資源が確認できる','PASS','B protocol and fit records','PATH1_RESOURCE_REQUIREMENTS.md;SOURCE_BASELINE.csv','既存成果の再確認','compiled depth/gatesではない'),
('CL10','実機論理／物理資源を確定できる','HOLD','B hardware','PATH1_RESOURCE_REQUIREMENTS.md','未解決事項','encoding・gate・error model不足'),
('CL11','T08の条件付き簡略質量差は5.448297415kg','PASS','specified T08 arithmetic only','ANALYSIS_RUN.json;PATH2_MODEL_VALIDATION.md','既存成果の再確認','実用packの測定差ではない'),
('CL12','上記mass差は実用完成packの軽量化を証明する','HOLD','engineering transfer','HOLD_REGISTER.md','未解決事項','全電池・部材・安全条件不足'),
('CL13','T09は完成mass NULL183、全面対向1件FAIL','PASS','original T09 records','T09_INDEPENDENT_COMPONENT_CHECKS.csv;SOURCE_BASELINE.csv','既存成果の再確認','failureを消去しない'),
('CL14','T09_ROW_183の全面対向条件を満たす','FAIL','same-stack footprint condition','PATH2_MODEL_VALIDATION.md;C_T09_COMPONENTS_183.csv','既存成果との不一致','元モデル内FAILを保持。修正案は面積/設計再考であり未採用'),
('CL15','T09未知質量差δ=bで相殺する','CONDITIONAL','separate B015/B051 mass bookkeeping','PATH2_BOUNDARY_RESULTS.csv','既存成果の再分析','δの現実値は未測定'),
('CL16','T08の利用率・電圧・追加質量のゼロ境界を算定した','CONDITIONAL','other parameters common','PATH2_BOUNDARY_RESULTS.csv','既存成果の再分析','条件付きモデルの閾値であり実証値ではない'),
('CL17','T08連続49点のDC差を共通古典460速度で計算した','PASS','deterministic arithmetic','PATH2_SENSITIVITY_RESULTS.csv;ANALYSIS_RUN.json','新規の条件付き分析','45080行は独立試料ではない'),
('CL18','終点のDC削減総量比は0.412579/0.413590%','CONDITIONAL','fixed observed trajectory and Controlled-DC','PATH2_SENSITIVITY_SUMMARY.csv','既存成果の再確認','実EV削減・全trip正味DCではない'),
('CL19','0.25%目標にはq約185.705/185.669が必要','CONDITIONAL','u1,V3.5,common components,finite cohort','PATH2_BOUNDARY_RESULTS.csv','新規の条件付き分析','任意説明目標であり必要性能の普遍値ではない'),
('CL20','0.5%目標の交点を今回範囲で算定できる','HOLD','q endpoint interval','PATH2_BOUNDARY_RESULTS.csv','未解決事項','区間内非到達。範囲外で不可能という意味ではない'),
('CL21','指定mass区間でDCのmass傾きが正','CONDITIONAL','920 fixed windows / same physics','PATH2_OPERATION_INTERACTIONS.csv;NUMERICAL_CHECKS.csv','新規の条件付き分析','異なる速度応答・回生・補機へ一般化しない'),
('CL22','量子計算がLP/S200性能改善と実EV削減を達成した','FAIL','causal attribution of existing evidence','PATH2_MATERIAL_BRIDGE_AUDIT.md;LITERATURE_EVIDENCE_MATRIX.csv','新たな解釈の提案','この断定は資料と不一致。量子に潜在価値がないという否定ではない'),
('CL23','量子材料予測→対象実用材料改善の追加価値','HOLD','quantum attribution','PATH2_MATERIAL_BRIDGE_AUDIT.md','未解決事項','対象精度・古典比較・設計採用・実験がない'),
('CL24','三層で条件と未接続を整理できる','CONDITIONAL','conceptual trial synthesis','CROSS_PATH_CONDITIONS_MATRIX.csv;DISCUSSION_TRIAL.md','新たな解釈の提案','実証因果モデル・制度評価ではない'),
('CL25','道路N0/N1の地域妥当性が受入済み','FAIL','existing geographical/dynamic acceptance','HOLD_REGISTER.md;SOURCE_AUTHORITY_AND_CONFLICTS.md','既存成果との不一致','旧FAILを保持、新規道路修正なし'),
('CL26','定時配達率を主RQの評価から外した','PASS','trial editorial scope only','RQ_REDESIGN_TRIAL.md;THESIS_CHANGELOG.md','新たな解釈の提案','旧Aは保存。正式目的の変更は未実施'),
('CL27','Papachristos2018の引用意図を同定できる','HOLD','source manuscript citation','LITERATURE_CLASSIFICATION.csv','未解決事項','候補を自動採用しない')]
tab('CLAIM_EVIDENCE_MATRIX.csv',[dict(claim_id=a,claim=b,status=c,scope=d,evidence=e,change_category=f,basis_and_limit=g) for a,b,c,d,e,f,g in claims])
# Keep original candidate claims visible; paragraphs not covered by key ledger remain unverified.
doc=Document(O/'sources/tmp_RsrchMstrDc_1026_results_integrated.docx');candidates=[]
for i,p in enumerate(doc.paragraphs[:370]):
 if len(p.text)>40 and any(t in p.text for t in ['結果','確認','示す','量子','改善','削減']):candidates.append({'source':'sources/tmp_RsrchMstrDc_1026_results_integrated_TEXT.md','paragraph_index0':i,'text':p.text,'review_scope':'主張をCL01–CL27へ再構成。旧全文章を一括PASSとしない','status':'SOURCE_CANDIDATE_NOT_INDEPENDENTLY_PROMOTED'})
tab('SOURCE_CLAIM_CANDIDATES.csv',candidates)
# Conditions and next steps for all unresolved issues.
holds=[
('H01','T09完成pack質量','HOLD','外装・タブ・foil余白・pack構造183行欠測','軽量化の無条件主張不可','設計別の未測定部材と全電池性能を測定','C'),
('H02','T08/T09同一完成品比較','HOLD','会計境界・活物質率等が異なる','完成pack優劣不可','同容量・同機能・同安全の整合設計','C'),
('H03','B公平なend-to-end速度優位','HOLD','scope不一致・前後処理・統一環境不足','時間優位の結論不可','同入力・同停止条件・同計算予算で全工程計時','C'),
('H04','量子実機回路・物理資源','HOLD','compiled depth/gates/hardware未記録','実用必要資源断定不可','対象回路・gate set・誤り予算・配置仕様','C'),
('H05','厳密最適値53入力','HOLD','R4 21、R5 32で証明不足','gap分母は407に限定','元certificateを精査し必要時の制限pilotとsolver比較','C'),
('H06','対象材料の量子計算への帰属','HOLD','参照はVASP/DFTと電極実験','量子由来性能改善未実証','同物性精度・同資源の量子古典比較と設計採用の記録','C'),
('H07','B経路→速度→DC','HOLD','現在Bの保存走行評価未実施','B品質差を省電力へ変換不可','地域受入解決後に同条件の計画対応付け','C'),
('H08','地域道路N0/N1','FAIL','旧幾何／動的受入FAIL','実地域配送へ一般化不可','独立の道路・動的検証。trialでは既存結果保存','D'),
('H09','T09全面対向1行','FAIL','同一stack footprint必要条件違反','当該設計の成立主張不可','面積・担持・stackを整合する設計提案を別途評価','D'),
('H10','Papachristos2018','HOLD','引用意図が一意でない','当該引用依存の主張を使用しない','研究者が元PDF・管理記録で引用意図を指定','C'),
('H11','実車・電極・電池の外的妥当性','HOLD','半電池移転・空荷・固定速度等','実用効果量未実証','対象全電池・pack・実車との同境界照合','C'),
('H12','Word実機最終組版・大学様式','HOLD','LibreOfficeとWordの差、指定様式未確認','提出原稿とは扱わない','Wordでフォント・ページ・数式・図表、様式を確認','B'),
('H13','旧参考文献全体・全引用の精読','HOLD','今回はL01–L12の限定照合','全文の引用監査完了を主張しない','LITERATURE_EXISTING_BIBLIOGRAPHYを原著に対応','C'),
('H14','H_plan数値と計画採用の運用規程','HOLD','許容時間・転送・採用手続不明','時間適用閾値は式のみ','対象運用の計画締切・処理工程を記録','C'),
('H15','0.5%任意目標の閾値','HOLD','今回q区間に交点なし','範囲外の性能不能を意味しない','追加の範囲拡張は研究者が必要性を判断','C')]
tab('UNRESOLVED_ITEMS.csv',[dict(hold_id=a,item=b,status=c,reason=d,impact=e,next_action=f,adoption_recommendation=g) for a,b,c,d,e,f,g in holds])
md('HOLD_REGISTER.md','# HOLD／FAILの再評価\n\n'+markdown_table(pd.DataFrame([{'ID':a,'事項':b,'判定':c,'理由・対象範囲':d,'結論への影響':e,'必要な次作業':f} for a,b,c,d,e,f,g in holds]))+'\n\nHOLDは推測で解消していない。FAILは該当する主張・設計条件の判定であり旧結果を削除しない。')
md('UNRESOLVED_ITEMS.md','# 未解決事項\n\nHOLD_REGISTER.mdおよびUNRESOLVED_ITEMS.csvに15事項の理由・影響・次作業を記録した。特にH01–H07とH14は研究上の結論の強さを制約する。H08/H09のFAILは保持した。\n\n引用H10/H13とWord表示H12が残るため提出・正式統合は未実施である。これらは本trialの実行記録と条件付き草案の完成を妨げないが、研究全体の完成を意味しない。')
# All exactly 32 requested task IDs with distinct execution and scientific verdicts.
tasks=[
('S1-1','RQ再定義','RQ_REDESIGN_TRIAL.md','完了','CONDITIONAL','正式RQを変更しない'),('S1-2','指標整理','INDICATOR_DEFINITIONS.csv','完了','PASS','旧定時率との不整合を記録'),('S1-3','寄与条件操作化','CROSS_PATH_CONDITIONS_MATRIX.csv','完了','CONDITIONAL','必要・十分・観測・仮定を区別'),('S1-4','境界固定','RESEARCH_BOUNDARY.md','完了','PASS','B時間窓なし／旧Aありを分離'),
('S2-1','A/B/C棚卸し','EXPERIMENT_INVENTORY.csv','完了','PASS','環境欠測はその旨を記録'),('S2-2','主張根拠対応','CLAIM_EVIDENCE_MATRIX.csv','完了','CONDITIONAL','重要主張27、旧候補文は別保存'),('S2-3','HOLD再評価','HOLD_REGISTER.md','完了','HOLD','判定できない15事項の影響・次作業'),('S2-4','追加分析判断','ADDITIONAL_ANALYSIS_DECISIONS.md','完了','PASS','大規模求解見積はデータ不足を明記'),
('S3-1','比較監査','PATH1_METHOD_AUDIT.md','完了','CONDITIONAL','初期状態・終了・支持の差'),('S3-2','品質再分析','PATH1_QUALITY_COMPARISON.csv','完了','CONDITIONAL','B全36800、exact407'),('S3-3','求解時間','PATH1_RUNTIME_COMPARISON.csv','可能範囲完了','HOLD','scope別CPUのみ、公平比較不可'),('S3-4','量子資源','PATH1_RESOURCE_REQUIREMENTS.md','可能範囲完了','HOLD','compiled/hardware欠測'),('S3-5','寄与条件導出','PATH1_CONTRIBUTION_CONDITIONS.md','完了','CONDITIONAL','時間予算は式・数値HOLD'),('S3-6','適用限界','LIMITATIONS.md','完了','CONDITIONAL','問題・対照・backend別'),
('S4-1','材料接続','PATH2_MATERIAL_BRIDGE_AUDIT.md','完了','CONDITIONAL','DFT/量子とA/B/Cを区別'),('S4-2','質量監査','PATH2_MODEL_VALIDATION.md','可能範囲完了','HOLD','T09完成pack未測定'),('S4-3','連続感度','PATH2_SENSITIVITY_RESULTS.csv','完了','CONDITIONAL','49点×460×2Crr、利用率追加'),('S4-4','成立消失境界','PATH2_BOUNDARY_RESULTS.csv','完了','CONDITIONAL','ゼロ境界／任意目標を区別'),('S4-5','走行条件','PATH2_OPERATION_INTERACTIONS.md','完了','CONDITIONAL','固定速度・成分maskとbranch'),('S4-6','量子帰属','PATH2_CONTRIBUTION_CONDITIONS.md','完了','HOLD','対象性能改善の量子帰属未実証'),
('S5-1','三層構造','INTEGRATED_CAUSAL_MODEL_TRIAL.md','完了','CONDITIONAL','概念的trial提案'),('S5-2','条件比較','CROSS_PATH_CONDITIONS_MATRIX.csv','完了','CONDITIONAL','単一改善率へ統合しない'),('S5-3','不成立分類','DISCUSSION_TRIAL.md','完了','CONDITIONAL','能力不足・未適用・消失・データ不足'),('S5-4','一般化限界','LIMITATIONS.md','完了','CONDITIONAL','旧M0との変更候補を記録'),
('S6-1','文献分類','LITERATURE_CLASSIFICATION.csv','完了','CONDITIONAL','重点12確認＋未同定1；旧73段落別台帳'),('S6-2','一次根拠照合','LITERATURE_EVIDENCE_MATRIX.csv','可能範囲完了','HOLD','未同定引用・全引用精読は残る'),('S6-3','研究ギャップ','RESEARCH_GAP.md','完了','CONDITIONAL','新規性の網羅的主張をしない'),
('S7-1','背景目的方法','THESIS_SECTIONS_TRIAL.md','完了','CONDITIONAL','である調・再現条件'),('S7-2','結果節','THESIS_TRIAL.docx','完了','CONDITIONAL','保存結果と追加感度を分離'),('S7-3','考察結論','THESIS_SECTIONS_TRIAL.md','完了','CONDITIONAL','全RQへ暫定回答、未検証明示'),
('S8-1','学術数値監査','FINAL_AUDIT_REPORT.md','完了','CONDITIONAL','独立式照合・根拠追跡、外的妥当性HOLD'),('S8-2','原稿成果物監査','REPRODUCIBILITY_REPORT.md','可能範囲完了','HOLD','パッケージ・PDF照合、Word実機はHOLD')]
tab('TASK_COMPLETION_MATRIX.csv',[dict(task_id=a,performed_work=b,artifact=c,execution_status=d,scientific_status=e,evidence_or_unresolved=f) for a,b,c,d,e,f in tasks]);assert len(tasks)==32
md('EXECUTIVE_SUMMARY.md','''
# 独立統合trialの要約

総合判定はTRIAL COMPLETEである。これは到達可能な分析・本文草案・監査・未解決記録を作成したという判定であり、研究全体の実証完了や正式採用ではない。32小課題の実施状況と科学的判定を分けた。

経路1：現行時間窓なし460入力・8設定・36,800保存計画を原NPZと測定記録から再検算した。mirror5は初期解と同じ目的値で、同支持DPが示す改善余地がない。Groverの小規模参照一致と大規模初期差の悪化は保存条件に限定する。公平な総求解時間、QPU優位、compiled資源はHOLDである。

経路2：T08の簡略質量差5.448297415kgを再確認した。既存端点内49点を460共通速度・2Crrで計算し、終点のDC削減総量比0.412579/0.413590%を再現した。利用率境界0.877094072と追加mass境界5.448297415kg、T09代表の未知mass差境界9.722608121/5.977891152kgを整理した。任意の0.25%目標のq閾値約185.705/185.669を条件付きで算定した。量子由来改善・完成pack・実車効果は未実証である。

統合：技術能力・システムへの適用・運用結果という三層の条件整理をtrial提案とした。支持不足・時間内採用・部材相殺・未接続を区別できることが追加価値である。単一の量子改善率へ統合しない。

定時配達率は主指標から除外した。旧Aの結果と旧原稿を保全した。最新方針とREADME・旧原稿の差を記録し、旧方針の正式記録は上書きしない。Papachristos2018、旧全引用の精読、Word実機・大学様式などをHOLDとする。

採用区分はADOPTION_REVIEW.mdに記載する。実データ再確認はA、条件付き感度と本文・統合考察はB、工学／時間／引用の不足はC、量子一般の優位や量子材料改善の実証という断定はDを推奨する。最終採否は研究者が判断する。
''')
md('ADOPTION_REVIEW.md','''
# 採用判断用レビュー（trial内の推奨、正式採否ではない）

本報告は、本文を生成した同一エージェントが証拠台帳と独立数値式を用いて行った分離監査である。第三者・別エージェントの査読を受けたとは主張しない。

## 追加価値

Bの全保存計画を再検算し、解品質と時間scope・支持制限を結び付けた。Cは既存二端点間の連続49点と利用率49点を共通速度で評価し、任意目標を満たすq閾値を追加した。質量からDCへの正の傾きの成立を解析区間全体で確認した。文献HOLDの時点差、READMEの旧方針、R4=99/100と旧A/現Bの混合リスクを明示した。

## 推奨区分

|対象|推奨|根拠・制約|
|---|---|---|
|B件数・原NPZ目的値・厳密参照欠測・scope別時間の再確認|A 採用候補|算術と出典確認。実運用解釈は別|
|T08/T09部材算術と未知部材NULLの保持|A 採用候補|元仕様内で照合。完成品の主張を加えない|
|RQ再設計と主指標整理|B 条件付き採用候補|11月4日方針に整合。研究者が正式計画・本文の扱いを判断|
|連続感度・相殺境界・任意目標閾値|B 条件付き採用候補|固定容量・簡略会計・共通速度・観測窓・任意性を明記|
|三層因果モデル・統合考察・論文trial|B 条件付き採用候補|概念的提案。未実証リンクと外的妥当性を維持|
|完成pack、実車省電力、公平な総求解時間、回路資源|C 再検討が必要|H01–H07/H11/H14の証拠を要する|
|Papachristos元引用と旧全参考文献の確定|C 再検討が必要|引用意図・原著照合が必要|
|量子優位一般、量子計算が対象材料改善を実現したという断定|D 採用非推奨|既存証拠が支持しない／帰属を誤る|
|道路受入済み・T09全面対向成立という断定|D 採用非推奨|既存FAILと不一致|

## 研究上のリスク

旧目的はサービス水準を重視しており、今回の条件重点案とは説明が異なる。正式採用時には方針・タイトル・背景・結論を一貫して改訂する必要がある。T08の実用移転、T09部材未知、CPUとQPUの混同、固定速度を実車効果と呼ぶこと、文献要旨を実証の証拠へ拡大することが主なリスクである。

## 元原稿との差分

|事項|変更前（元原稿段落index0）|trial変更案|理由・根拠|
|---|---|---|---|
|目的|19:サービス水準とエネルギーへの影響|二経路の寄与条件・制約・未接続の特定|最新依頼、RQ_REDESIGN|
|RQ|23/27:定時率と電力量の併用|RQ0/RQ1/RQ2/RQI|主指標除外と既存回答範囲の対応|
|指標|23:PE定時率を中心に評価|B品質・gap・OD時間・工程時間、C質量・DC・境界|INDICATOR_DEFINITIONS|
|方法|3.8のA政策分析を主節に配置|Aは履歴補足、B/Cを主とし連続感度追加|系列を混合しない|
|結果|5.2 A定時率と5.3の離散参照|B品質・CPU工程、C49点・境界を分ける|PATH1/2 CSV|
|考察|定時率差と材料影響の議論|能力・適用・伝達の三層と不成立を比較|CROSS_PATH matrix|
|結論|旧のサービス水準と電力の問い|各RQへ条件付き回答、量子帰属・実運用HOLD|CLAIM_EVIDENCE_MATRIX|

全差分はtrial提案である。元原稿とその図表・参考文献はsourcesにそのまま保存し、正式な研究記録を編集していない。採用・統合・公開・commit・pushは実施していない。
''')
md('THESIS_CHANGELOG.md','''
# 論文trialの変更履歴

元の統合済みDOCXをsourcesへバイト複製し、本文・表・図を保全した。THESIS_TRIAL.docxはその複製を読み、本文bodyを新規の7章構成に置き換えた独立編集版である。元の付録・表27点・数式・参照をそのまま新本文へ残した差分編集版ではない。元全文はsourcesと抽出テキストに保存し、比較はADOPTION_REVIEWの節対応による。

変更はすべてtrial提案である。研究目的/RQ/指標を寄与条件へ整え、旧定時率Aは補足へ移した。現行Bと旧Aの条件を分け、T08/T09の完成品境界・量子帰属を明示した。保存結果、今回の追加分析、考察を分離した。12重点文献を出典として用い、未同定Papachristosを新しい主張の根拠には用いない。旧引用のHOLDは維持する。

内部数値修正：初回スクリプトは保存値のFraction文字列をfloatへ直接変換できず停止した。Fractionを明示解析して再実行した。次の点検で、同一目的値10repの浮動小数平均に約1e-13秒の擬似差・SDが現れる点を検出し、保存された正確な差を平均し、全値同一時はSD=0とした。元データ・モデルは変更していない。logs/analysis_attempt01.log、analysis_attempt02_pass.json、analysis_final.logに記録する。

DOCXの数式は改変解釈を避けるため読める一行算式として記述し、新しい数式番号(1)–(7)、図1–4、表1–4を用いる。旧数式・相互参照・履歴本文はsource DOCX側で保存した。Word実機での最終組版・大学指定様式はHOLDである。
''')
print('reports written; tasks32, claims27, unresolved15')
