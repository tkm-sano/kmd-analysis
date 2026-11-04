from pathlib import Path
import csv,json,re,shutil,hashlib
from docx import Document
from docx.shared import Inches,Pt,Cm
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.text import WD_LINE_SPACING
from docx.shared import RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
import pandas as pd
O=Path(__file__).resolve().parents[1]
q=pd.read_csv(O/'PATH1_QUALITY_COMPARISON.csv');b=pd.read_csv(O/'PATH2_BOUNDARY_RESULTS.csv');runtime=pd.read_csv(O/'PATH1_RUNTIME_COMPARISON.csv');s=pd.read_csv(O/'PATH2_SENSITIVITY_SUMMARY.csv');lit=pd.read_csv(O/'LITERATURE_CLASSIFICATION.csv')
def mdtable(headers,rows):return '\n'.join(['|'+'|'.join(headers)+'|','|'+'|'.join(['---']*len(headers))+'|']+['|'+'|'.join(str(x).replace('|',' / ').replace('\n',' ') for x in r)+'|' for r in rows])
t1=mdtable(['系列','母集団','主たる出力','本稿での位置付け'],[['A','4顧客78、36政策','旧定時率・採用時刻','履歴・補足。主指標外'],['B','460入力×8設定×10rep','保存経路・OD秒・工程資源','経路1の主分析'],['C T08','古典460保存速度、2Crr','簡略質量・観測窓DC','経路2の主感度'],['C T09','183部材設計、代表2設計','既知部材・未知質量差','完成pack未確定の境界']])
t2=mdtable(['顧客数','設定','平均初期差 s','平均gap %','厳密入力'],[[int(r.n_customers),r.config_id,f'{r.mean_delta_vs_initial_s:.6f}',f'{r.mean_global_gap_percent:.6f}',int(r.exact_inputs)] for r in q[q.config_id.isin(['MEAN_P2','GROVER_P2','GROVER_P3'])].itertuples()])
t3=mdtable(['境界','値','単位','条件'],[['T08追加質量差',f'{5.448297415076922:.9f}','kg','qS、u=1、V=3.5'],['T08利用率',f'{.8770940719841043:.9f}','1','qS固定・共通電圧等'],['T08平均電圧',f'{3.1931556837797896:.9f}','V','qS、u=1、他部材共通'],['T09 B015未知差',f'{9.722608121107784:.9f}','kg','固定担持の代表設計'],['T09 B051未知差',f'{5.977891152148871:.9f}','kg','固定面積の代表設計']])
t4=mdtable(['Crr','説明用目標 %','必要q Ah/kg','判定'],[[r.boundary.replace('T08 ',''),r.input_variable.split('_')[2].replace('pct',''),f'{r.value:.6f}' if pd.notna(r.value) else '範囲内交点なし',r.status] for r in b[b.kind=='ARBITRARY_ILLUSTRATIVE_TARGET'].itertuples()])
text='''# 量子計算がEV配送システムに寄与し得る条件

配送計画と電池材料評価を介した作用経路の分析――修士論文本文trial案

本稿は2026年11月4日の方針に基づく独立した1回のtrialである。正式な研究成果への採用・統合は未実施である。既存成果の再分析、条件付き計算、解釈提案を含む。研究者の採否判断を要し、研究全体の実証完了を意味しない。

## 要旨

本研究は、量子計算の技術的能力が都市内EVラストマイル配送システムへ寄与するための条件を、配送経路計算と電池材料・車両の二経路から検討するものである。対象は大田区由来の単一デポ・固定割当の合成配送問題である。保存された実験結果、原入力、実装、一次文献を照合し、技術能力、システムへの適用、運用上の結果という三層へ整理した。定時配達率は主指標に含めない。

経路1では、時間窓なしの460入力、8設定、各10測定反復に対応する36,800保存計画を検算した。matching支持を用いる5設定は古典初期解と同じ目的値を示し、その支持内最適値から改善余地の制約が確認された。Grover型設定は小規模で厳密参照に一致したが、大規模側では平均目的値が古典初期解より悪化した。保存時間はCPUシミュレーションの工程別記録であり、公平な総求解時間や量子実機での優位は未判定である。

経路2では、既存の条件付き材料入力を簡略セル・パック質量と固定速度の走行時DC電力量へ接続した。比容量の二端点間を49点で計算し、追加部材差、利用率、平均電圧による相殺境界を示した。完成パックの未知部材、実用全電池への移転、量子計算に起因する材料改善は未検証である。以上から、技術能力の改善がシステム成果へ伝達されるには、出力の改善に加えて適用条件と効果の伝達条件が必要であることを、限定したモデルと証拠の範囲で論じる。

## 1　背景と研究目的

### 1.1　社会課題と技術評価

配送は人々の生活と事業活動を支える一方、車両、道路、エネルギー、拠点、計画作成の相互依存を伴う。エネルギー利用の改善を検討する際には、対象となる配送機能と比較条件を明示する必要がある。技術の性能値だけでは、その性能がどの設計・運用に使われるかを説明できないためである。

社会技術システムの視点は、技術、利用実践、制度、インフラの関係へ注意を向ける（Geels, 2002）。社会的課題への対応を論じる政策研究も、個々の研究開発とシステムの変化を区別している（Schot and Steinmueller, 2018）。本研究はこの視点を背景としつつ、社会制度全体をモデル化するのではなく、技術出力が配送計画または電池設計を介して運用に関係する区間を対象とする。

量子計算は萌芽的技術として期待されるが、用途・将来性能・社会的影響に不確実性がある。萌芽性の定義が含む不確実性と曖昧性（Rotolo et al., 2015）を踏まえ、本研究は量子技術の有効性を前提としない。将来の技術性能が実現することと、その性能を仮定した際にシステムの結果が変わることを分け、後者を条件付きモデルで検討する。

### 1.2　研究目的と問い

本研究の目的は、量子計算の技術的能力が配送計画および電池材料評価を通じてEV配送システムへ反映されるための条件と、寄与を妨げる制約・未接続を、保存実験結果と一次文献に基づき特定することである。量子優位や改善量の実証は研究成立の必須要件ではない。

全体の問いRQ0は「量子計算は、どのような技術能力・適用・効果成立条件の下で対象EV配送システムへ寄与し得るか」である。RQ1は「同一配送問題で古典対照を上回る解を許容時間内に計画へ適用するために何が必要か」、RQ2は「材料入力の変化が質量を介して走行時DC電力量へ伝達され、また相殺される条件は何か」である。統合の問いRQIは「二経路の寄与が技術能力の改善だけでは決まらないのはどの接続条件によるか」である。

本稿のRQはtrial提案であり、旧正式研究質問を上書きしていない。定時配達率を主指標から外し、経路1では解品質・最適性ギャップ・OD道路旅行時間・求解工程時間・資源、経路2では材料入力・質量・Controlled-DC・成立消失境界を扱う。必要な需要を同じ条件で扱うという比較上の前提は維持する。

## 2　先行研究と本研究の位置付け

### 2.1　社会技術システムと萌芽的技術の評価

本研究は、技術から社会的成果へ自動的に改善が伝わるという前提を置かない。社会技術的移行に関する研究と、萌芽的技術を将来条件の下で評価する研究を、境界・適用条件・不確実性を明示するための参照とする。Arvidsson et al.（2018）の将来技術評価に関する議論も参照するが、本研究はLCAや社会技術的移行の実証研究ではない。

### 2.2　EV配送と経路計算

Schneider et al.（2014）は時間窓と充電拠点を含むEV配送問題を扱う。本研究の主系列Bは、車両への顧客割当と台数を固定した訪問順の計算であり、途中充電を含めない。したがって、実施した計算問題をEV配送全体の最適化と呼ばない。比較対象の制約・目的関数の差を明示することが必要である。

量子最適化についてはQAOA、制約を扱う交互演算子、Grover型ミキサーに関する原著を参照する（Farhi et al., 2014; Hadfield et al., 2019; Bärtschi and Eidenbenz, 2020）。Palackal et al.（2023）の配送応用は、問題の分割や実行可能解の取得を含む条件が結果を左右する比較例である。本研究の保存方式と同じ実験条件ではないため、結果の数値を直接移植しない。

### 2.3　材料計算と車両への接続

量子材料計算から設計に有用な物性を得る候補経路は、Delgado et al.（2022）を参照する。一方、本研究の材料参照入力の由来であるChen et al.（2020）は古典DFTと電極実験である。Faraji-Niri et al.（2024）の電極データも完成パックを直接検証したものではない。材料計算、電極特性、セル・パック、車両質量を同じ成果として扱わない。

### 2.4　研究ギャップ

本研究の位置付けは、技術能力、システムへの適用、運用上の結果の各層を、二つの作用経路に共通する形式で対応付け、保存データが示す制約と未接続を整理する点にある。文献が少ないという理由や世界初という主張に依存しない。対象・評価指標・分析境界の違いに基づく位置付けである。文献照合は重点12件の限定範囲であり、網羅的な系統的レビューではない。

## 3　方法

### 3.1　対象条件と実験系列

対象は大田区由来の単一デポDEP_006を持つ合成配送問題である。計算問題ごとに車両1台、顧客割当・台数固定、容量216PE、サービス102秒/顧客、計画出発0秒、デポ帰還期限32,400秒とする。途中充電、顧客再割当、車両増加は対象外である。PEは荷物相当量であり、kgへ変換して電力量の積載質量に用いていない。

表1に系列の違いを示す。主系列Bは時間窓なし、旧Aと旧正式小規模量子は顧客時間窓ありである。旧R4=99と現B R4=100も別条件である。旧Aの定時配達率は履歴・補足とし、新しい主指標へ混ぜない。

表1　実験系列と本稿の評価境界（出典：EXPERIMENT_INVENTORY.csv）。

{TABLE1}

### 3.2　証拠の区分と監査方法

保存結果、今回の再分析、追加の条件付き計算、研究者による解釈を区別する。既存の報告書の結論を無条件に採用せず、上流ファイル・版・依存関係を確認した。重要主張はPASS、CONDITIONAL、HOLD、FAILの4区分とし、対象範囲と根拠を対応付けた。PASSは指定範囲での算術・資料整合を含むが、実世界の妥当性へ自動的に拡張しない。

新しい計算は独立したtrial領域で実行した。元NPZ、保存測定、速度、原稿は読み取りのみとし、SHA256とGit状態を開始・終了時に確認する。量子回路の再実行、学習、経路探索、SUMO、実車・電池実験は行わない。

### 3.3　経路1の目的と指標

顧客の訪問順をπ、デポを0、地点間の有向道路旅行時間をτとすると、目的は式(1)である。

T(π) = Σ[k=0..n] τ(π_k, π_(k+1)),  π_0 = π_(n+1) = 0.　(1)

待機とサービス時間は目的に含めない。顧客時間窓なしのBでは、全顧客の一度訪問、総需要216PE以内、T+102n≦32,400秒を独立に確認する。実道路の旅行時間や実配送完了を保証する制約ではない。

厳密参照T*が確認できた入力について最適性ギャップを式(2)で求める。

gap(%) = 100 × (T − T*) / T*.　(2)

保存した有理数表現による最適値一致率、古典初期との差Tsample−Tinitial、実行可能な保存bestの取得状況を併記する。量子方式の最良標本を初期解との小さい方へ置換していない。原NPZから計算した目的値と保存測定を全36,800計画で照合した。

Bは3/4/5/25/100/125顧客、規模ごと78/78/78/78/78/70固有入力である。26親・25需要群、8設定、各10測定repからなる。10repは同じ学習済み状態の測定反復である。入力内平均を取り、その後規模内で入力を等重みに集計した。標準偏差は測定反復の記述であり、独立学習や実都市の不確実性ではない。

### 3.4　アルゴリズム・対照・停止条件

matching支持のmirror5設定は対称位置を組とする部分swapで、支持は2^floor(n/2)の完全経路である。全顧客を保持するが全順列は探索しない。同じ支持の古典chain-DP最適値を、global厳密参照とは別の対照とする。Grover P2/P3は一様順列初期状態と全順列支持、activeは隣接swap p3とt={0,0.5,1}の限定gridである。

層数、目的、初期状態、最適化上限は元PROTOCOLに従う。mirrorの関数評価上限64、Grover68、active3gridは同一予算ではない。最終測定は8,192shotsを10repである。保存fitは3,680件を一意に数え、測定repで10重加算しない。global厳密参照は407入力で、残る53は欠測理由を保持する。厳密solver自体を今回再求解したわけではない。

### 3.5　求解時間と資源

前処理、初期古典解、fit、状態選択、最終検証、測定、後処理、入出力転送を分ける。保存CPU wall/CPUのscopeが異なるため、単純な比を量子の速度向上率としない。active RESULTと他方式FITも別である。計画に許される時間をH_planとした時間条件は式(3)で表す。

T_pre + T_fit + T_measure + T_validate + T_post + T_transfer ≦ H_plan.　(3)

各項の十分な比較実測とH_planの運用値がないため、数値の採用閾値はHOLDとする。pは層数でありcompiled回路深さではない。backendの二サイト演算・MPS bondをnative gate数へ換算しない。実機論理・物理資源と誤り訂正の見積は未確定である。

### 3.6　材料参照と質量会計

T08では、Chen et al.の同試験系列の容量と保持率から旧研究が逆算したqLP=171.875、qS=195.959596 Ah/kgを参照する。初回容量や実用全電池性能と同じではない。利用率uは追加の全電池移転損失を一度だけ表し、保持率・ICEを再乗算しない。

gross energy E_g=20,000Wh、平均全電池電圧V=3.5、正負活物質率0.75/0.98、負極比容量360Ah/kg、N/P=1.1とする。100セルと0.19kg/cellのその他部材、packその他15kg、追加質量δを用いた簡略会計は式(4)である。

m_pack = E_g/(V q u × 0.75) + 1.1 E_g/(V × 360 × 0.98) + 100 × 0.19 + 15 + δ.　(4)

セル質量は両極塗工材を100分割してその他セル部材を加える。gross20kWhを質量、usable18kWhをstockの条件に使い分ける。旧Legacy B0/B1/B2のpack比エネルギー180/220/250Wh/kgは再現用の履歴として保持し、現材料入力と量子効果へ読み替えない。

T09は活物質・塗工材、Al/Cu、separator、liquidの既知成分を記録する一方、外装・タブ・余白・pack構造は未測定である。183設計の既知成分を有理数式で独立に照合した。既知成分へT08の固定部材を重複加算せず、完成パック質量を残差で補わない。

### 3.7　固定速度のControlled-DC

保存速度は1秒間隔で、ds=v_tΔt、慣性は隣接速度二乗差で計算する。W1は転がり、W2は空気、W3は並進、W4は回転の仕事である。回転等価質量61kg、CdA=1.175m²、空気密度1.2041kg/m³、g=9.80665m/s²、効率0.9を固定する。Crrは速度依存式のp=4.5と2.6の係数包絡を用いる。

E_DC = Σ_t max[W1_t + W2_t + W3_t + W4_t, 0] / 0.9.　(5)

式(5)のWはWhへ換算した値である。合計後の正値化であり、成分ごとの正値化ではない。回生なし、平坦、補機範囲外、空荷0kg、運転者55kgとする。T08では非pack走行質量1,043.888888889kgを共通とし、pack質量を置換する。末端1秒は未観測であり、電力量を0としない。

質量依存を各区間のa_t m+b_tとして表し、質量区間の両端で同符号の項と分岐が変わる項を分けた区分線形式を計算した。凍結kernelと920端点で照合し、最初の軌跡は別のscalar和でも検算した。成分分解はbaseline正値maskでの差とbranch補正を用いる。

### 3.8　連続感度と境界

qLPからqSまでを含む等間隔49点、u=1、V=3.5、追加質量0とし、共通古典460速度と2Crrで45,080行を計算した。qS固定でuを容量等価点から1まで変える49点の感度も算定した。この区間は既存参照端点と旧感度入力の内側である。実測された連続材料性能ではない。

既知または簡略会計の質量差をb、未知・追加S−LP差をδとすると、式(6)が成り立つ。

Δm = m_LP − m_S = b − δ.　(6)

δ=bをゼロ効果境界とし、共通走行条件の区間でDCの質量傾きが正かを確認する。効果の任意目標0.1/0.25/0.4/0.5%は、単位と閾値計算を説明するために設定したものであり、研究成功・採用基準ではない。各総量比を式(7)で計算し、区間内の交点を決定論的二分法で求める。範囲外へ外挿しない。

saving(%) = 100 × (ΣE_LP − ΣE_alt) / ΣE_LP.　(7)

### 3.9　統計と再現性の解釈

本稿の数値は固定有限cohortに対する記述である。入力、測定、政策、感度点の依存を保持し、実都市母集団への信頼区間や有意性検定を追加していない。旧群bootstrapの区間は履歴上の補助感度であり、モデルの外的誤差の区間ではない。今回の連続感度は決定論的で乱数seedは非適用である。

全CSVと図表の再生成コード、環境、入力SHA256、Git状態をtrialに保存する。公開cloneだけでは外部保全NPZ・測定・速度が不足するため、公開環境のみでの全量再現性は未達である。

## 4　研究結果

### 4.1　配送計画の解品質：保存結果の再分析

Bの保存計画36,800件は、全顧客の順列、容量、帰還期限について保存モデル内で可行であった。これは8,192shots後のbest計画についての値であり、全raw shotの成功率ではない。厳密参照入力は407件、未確定はR4の21件とR5の32件、計53件であった。

mirror5とactiveの目的値は全460入力で古典初期解と同じであった。mirrorの保存同支持DP最適値も初期目的値と一致した。activeは全460の保存gridでt=0が選択された。これらの観測は全順列や連続角探索の最適性を示さない。

表2は代表設定の入力内平均後の規模別記述である。Grover P2/P3は3〜5顧客で保存厳密参照に一致した。4/5顧客では初期差が平均約−0.160/−1.099秒であり、小規模の一部入力で初期解を改善した。一方25/100/125顧客では平均初期差が正であった。

表2　Bの代表設定の品質（出典：PATH1_QUALITY_COMPARISON.csv。gapは厳密参照のある入力のみ）。

{TABLE2}

![図1　規模別の最適性ギャップ。保存厳密参照のある入力を分母とする。](PATH1_FIGURES/F1_quality.png)

![図2　古典初期解に対するOD秒の差。正は保存目的値の悪化である。](PATH1_FIGURES/F2_initial_delta.png)

測定repのばらつきはPATH1_INPUT_SEED_STATISTICS.csvに保存した。同じ目的値が繰り返される入力のSDを0とし、丸め誤差を測定変動へ読み替えていない。Groverの大規模側には測定間の変動があった。これを学習の再現性や都市間変動の推定とはしない。

### 4.2　保存CPU時間と資源：比較可能な範囲

fitと最終検証を別scopeとして保存した。Grover P3の大規模側の最終検証はfitと異なる規模のCPU時間を要しており、fitのみを求解全体と呼べない。activeの保存時間もgrid等を含むRESULT scopeである。PATH1_RUNTIME_COMPARISON.csvに工程別の件数、平均、中央値、最小、最大を示した。

8192shots/測定rep、p2/p3、保存関数評価数、backend演算等は確認できた。一方、統一した当時環境、全工程時間、compiled gate数・depth・実機qubitは不足した。公平なend-to-end速度優位と実用必要資源の数値判定はHOLDである。保存CPU秒を実機実行想定秒へ変換しなかった。

### 4.3　材料・質量：保存結果の再確認

T08のLP/S200条件の簡略pack質量は96.145654799/90.697357384kgで、差は5.448297415kgであった。対応するセル質量はpackその他15kgを除いて100分割した値である。実測完成packの差ではない。

T09の183設計はすべて完成pack質量が未確定であった。既知成分の合計と各成分の算術は照合できた。全面対向の1行は元の必要面積条件のFAILを維持した。代表B015/B051の既知差は9.722608121/5.977891152kgであり、未知部材差δがこれらに達すると相殺する。

表3　質量会計のゼロ境界（出典：PATH2_BOUNDARY_RESULTS.csv）。

{TABLE3}

### 4.4　連続感度：今回の条件付き追加計算

qの49点について、セル、簡略pack、車両・走行質量、観測窓DCを算定した。qS終点のDC削減総量比はCrr下側0.412579010%、上側0.413590412%であった。個別率の平均はそれぞれ0.409329419%、0.410435042%であり、総量比とは異なる。

![図3　T08参照端点間の連続q感度。固定u・V・部材・共通460速度の条件付き計算である。](PATH2_FIGURES/F3_continuous_q.png)

全920条件で、T08両端点間の質量区間における最小片側DC傾きは正であった。凍結kernelと区分線形式の最大差は2.73×10^−12Wh、最初の軌跡の独立scalar和との最大差は4.55×10^−13Whであった。数値の一致は実車妥当性の確認ではない。

表4の任意目標に対するq閾値を算定した。0.5%は解析区間内で非到達であり、区間外の不能を意味しない。0.25%の値も、同一容量・u=1・V=3.5・同部材・総量比という条件に限定される。

表4　説明用の任意DC目標に対するq閾値（出典：PATH2_BOUNDARY_RESULTS.csv）。

{TABLE4}

![図4　追加・未知部材差による相殺。T08/T09の別設計を示し、完成pack同士の性能比較ではない。](PATH2_FIGURES/F4_cancellation.png)

### 4.5　走行条件と未評価部分

同一速度上のW1・W3差は走行距離や加減速に関係し、W2・W4の直接質量差は0であった。正値maskの変更によるbranch補正を含めてDC差を構成した。再発進や距離との相関は記述値であり、個別条件を独立に操作した因果効果ではない。

Bの現行計画に対する走行DC、対象材料の量子物性計算、実用全電池移転、完成pack性能、実車省電力は未評価である。旧道路N0/N1の受入FAILを保持する。旧Aの政策結果を保存したが、本稿では新たな定時率の結論へ用いない。

## 5　寄与条件の統合考察

### 5.1　技術能力条件

配送計算の品質改善を寄与と定義するなら、明示した古典対照より良い可行解を得る必要がある。改善解が支持に含まれない場合、アルゴリズム内の探索を増やすだけでは目的値改善に届かない。mirrorの結果は、この支持と初期解に関する制約を示している。支持拡張やp増加だけで改善が保証されるわけではない。

材料計算では、設計判断に必要な物性を精度・時間・資源の条件内で求めることが能力条件候補となる。しかし、本T08のq変更はその能力達成を測定したものではない。物性予測の精度と材料性能の改善を区別して論じる必要がある。

### 5.2　適用条件

配送側では、式(3)の時間条件に加え、同じ需要と制約を保ち、計画が採用・実行されることが必要である。両方式が同じ締切内に完成し、同じ品質の計画を採用するなら、計算時間差がそのまま運用時間差へ伝わるとは限らない。

材料側では、半電池参照が実用全電池へ移転し、同容量での軽量化へ設計上配分される必要がある。追加部材、安全・熱・寿命等が変われば、正極由来の差を保持できない可能性がある。計算出力があることと、システムへ実装されることを別条件とする。

### 5.3　効果成立・消失条件

T08の共通V・負極・固定部材の条件では、q_S u_S > q_LP u_LPが正極塗工材の軽量化の必要十分条件である。未知部材が変わるときは式(6)のb−δの符号が質量差を決める。指定した質量区間・共通速度でDC傾きが正であることを合わせれば、モデル内では質量相殺点とDC差ゼロが対応する。

共通固定部材は正極由来の絶対kg差を直接消さないが、全質量・電力量に対する相対効果を希釈する。一方、材料別の追加部材差は絶対差を相殺し得る。この違いを一括して「固定質量で効果が消える」と表現するのは適切ではない。

不成立は、支持内に改善余地がない場合、時間内採用ができない場合、部材差で消失する場合、必要な証拠がない場合に分けられる。HOLDは効果不存在の証拠ではない。今回の負の結果や小さい条件付き効果も、適用条件を特定するための情報である。

### 5.4　二経路の共通構造

両経路の共通構造は、技術能力から出力を得て、出力をシステム設計・運用へ適用し、その後に成果へ伝達するという三層である。解品質の秒数と材料質量・DCの削減率を単一の改善指標へ集約しない。条件候補、保存データで確認した条件、モデル上仮定した条件を分けることで、追加的な証拠が必要な区間を特定できる。

この整理を社会技術システム全体の実証モデルと呼ぶことはできない。制度、組織、採用行動、経済性を観測しておらず、それらへの一般化は今後の検討を要する。旧M0からの変更も、面接後M1の成果ではなくtrial解釈提案である。

## 6　限界と今後の必要作業

対象は大田区由来の合成入力であり、道路受入、実注文、背景交通、実車電力量に対する妥当性が確立していない。単一車両、固定割当、途中充電なしの境界を超える適用は未評価である。規模比較は需要・地理・方式の差を含み、顧客数単独の因果効果ではない。

経路1では古典初期と同支持DPとglobal厳密参照の役割が異なる。最強古典との同予算比較、統一環境・総時間、実機回路資源、厳密参照53入力が不足している。これらを保存CPUの一部工程から補うことはできない。

経路2では半電池参照、利用率・平均電圧・N/P、簡略部材、T09の未測定部材、固定速度、回生なし・補機範囲外・空荷・末端未観測に依存する。実用全電池・完成pack・車両で同じ差が生じることは未実証である。量子計算から対象材料設計への追加価値も未接続である。

今後必要な作業は、主張に対応する証拠の不足に限定して判断する。公平な時間比較には同条件の全工程測定、完成packには部材と工学性能の整合データ、量子帰属には対象物性の古典対照と設計採用の証拠が必要である。大規模求解や新規SUMOを、本稿の条件整理を終えるためだけに追加しない。

引用についてはPapachristos（2018）の元引用意図と旧参考文献全体の精読が未完了である。本trial本文はその未同定引用に依存しない。本文草案の出典は末尾の重点12文献へ対応させたが、提出前の大学指定様式、Microsoft Wordでの最終表示を含む最終編集が必要である。

## 7　結論

RQ0に対し、量子計算が対象EV配送システムへ寄与するための条件候補は、技術的に有用な出力、システムへの適用可能性、効果の伝達という三層に区分できる。保存データにより評価できたのは、その一部の品質制約と質量・DCの条件付き関係である。

RQ1に対し、同一問題で対照より良い可行解を得るためには、改善解を含む支持とその取得が必要である。今回のmatching支持では初期目的値を上回る余地が確認できず、Groverでは規模・方式に依存した結果が得られた。時間内採用の条件は定式化できたが、公平な総時間と実機資源は未確定である。

RQ2に対し、材料入力の差は、利用率、平均電圧、部材の質量配分を通じて変化する。指定モデル内の相殺境界、連続DC感度、説明用目標の閾値を定量化できた。一方、未知部材差の実値、実用全電池・完成pack・実EV、量子由来の性能改善は未検証である。

RQIに対し、二経路はいずれも適用過程と伝達条件によって技術出力の寄与が制約される。学術的貢献の候補は、量子優位を前提とせず、保存数値・モデル仮定・未接続を分離し、支持制限、採用時間、部材相殺を共通の条件分析へ対応付けた点にある。これは限定した証拠に基づくtrial提案であり、正式な研究成果への採用は研究者の判断に委ねる。

## 参考文献（本trial本文の重点確認範囲）

{REFERENCES}

## 付録A　主張・根拠と再現手順

主要主張27件はCLAIM_EVIDENCE_MATRIX.csv、全32小課題の実施状況はTASK_COMPLETION_MATRIX.csv、未解決15事項はHOLD_REGISTER.md、図表とCSVの対応はFIGURE_TABLE_INDEX.mdである。環境・乱数非適用・処理時間はANALYSIS_RUN.json、入力場所とSHA256はSOURCE_BASELINE.csv、実行コードはscripts/analyze.pyである。外部保全データが必要であり、公開cloneだけでの全再現性は主張しない。

本稿の図1〜4と表1〜4はtrial内の独立した番号である。元原稿の番号・数式・参考文献はsourcesの複製へ保全している。元原稿との差分はTHESIS_CHANGELOG.mdとADOPTION_REVIEW.mdに記録する。
'''
refs=[]
for r in lit[lit.status=='PASS'].itertuples():refs.append(f'{r.author} ({r.year}). {r.title}. {r.primary_url}')
text=text.replace('{TABLE1}',t1).replace('{TABLE2}',t2).replace('{TABLE3}',t3).replace('{TABLE4}',t4).replace('{REFERENCES}','\n\n'.join(refs))
(O/'THESIS_SECTIONS_TRIAL.md').write_text(text)
# Copy the selected original first, edit ONLY the trial copy.
source=O/'sources/tmp_RsrchMstrDc_1026_results_integrated.docx';target=O/'THESIS_TRIAL.docx';shutil.copyfile(source,target);d=Document(target)
body=d._element.body
for el in list(body):
 if el.tag!=qn('w:sectPr'):body.remove(el)
for sec in d.sections:
 sec.page_width=Cm(21);sec.page_height=Cm(29.7);sec.top_margin=Cm(2.2);sec.bottom_margin=Cm(2.2);sec.left_margin=Cm(2.3);sec.right_margin=Cm(2.3)
 for part in [sec.header,sec.footer]:
  for x in list(part._element):part._element.remove(x)
 sec.header.add_paragraph('KMD修士研究・独立trial／正式採用未定')
 foot=sec.footer.add_paragraph();foot.alignment=2;field=OxmlElement('w:fldSimple');field.set(qn('w:instr'),'PAGE');foot._p.append(field)
for name in ['Normal','Body Text','Heading 1','Heading 2','Heading 3','Caption','Title']:
 
 if name not in d.styles:d.styles.add_style(name,WD_STYLE_TYPE.PARAGRAPH)
 st=d.styles[name];st.font.name='Droid Sans Fallback';st.font.size=Pt(10.5)
 st._element.get_or_add_rPr().rFonts.set(qn('w:eastAsia'),'Droid Sans Fallback')
 st.paragraph_format.line_spacing=1.35;st.paragraph_format.space_after=Pt(6)
for name,sz in [('Heading 1',16),('Heading 2',13),('Heading 3',11.5),('Title',20)]:
 d.styles[name].font.size=Pt(sz);d.styles[name].paragraph_format.keep_with_next=True
 d.styles[name].font.bold=True
# All original package relationships remain in this copy; new body has standalone numbering.
lines=text.splitlines();i=0
while i<len(lines):
 line=lines[i]
 if not line.strip():i+=1;continue
 if line.startswith('|'):
  rows=[]
  while i<len(lines) and lines[i].startswith('|'):
   cells=[x.strip() for x in lines[i].strip('|').split('|')]
   if not all(re.fullmatch(r':?-+:?',c) for c in cells):rows.append(cells)
   i+=1
  table=d.add_table(rows=1,cols=len(rows[0]));table.style='Table'
  borders=OxmlElement('w:tblBorders')
  for side in ['top','left','bottom','right','insideH','insideV']:
   edge=OxmlElement('w:'+side);edge.set(qn('w:val'),'single');edge.set(qn('w:sz'),'4');edge.set(qn('w:color'),'B8B8B8');borders.append(edge)
  table._tbl.tblPr.append(borders)
  for j,v in enumerate(rows[0]):table.rows[0].cells[j].text=v
  for row in rows[1:]:
   cells=table.add_row().cells
   for j,v in enumerate(row):cells[j].text=v
  for ri,row in enumerate(table.rows):
   row._tr.get_or_add_trPr().append(OxmlElement('w:cantSplit'))
   if ri==0:row._tr.get_or_add_trPr().append(OxmlElement('w:tblHeader'))
   for cell in row.cells:
    for p in cell.paragraphs:
     p.paragraph_format.space_after=Pt(3);p.paragraph_format.line_spacing=1.1
     for r in p.runs:r.font.size=Pt(8.5);r.bold=(ri==0)
  continue
 if line.startswith('!['):
  match=re.match(r'!\[(.*)\]\((.*)\)',line);cap,path=match.groups();d.add_picture(str(O/path),width=Cm(15.8));d.add_paragraph(cap,style='Caption')
 elif line.startswith('# '):d.add_paragraph(line[2:],style='Title')
 elif line.startswith('### '):d.add_paragraph(line[4:],style='Heading 2')
 elif line.startswith('## '):d.add_paragraph(line[3:],style='Heading 1')
 else:d.add_paragraph(line,style='Body Text')
 i+=1
d.core_properties.title='量子計算がEV配送システムに寄与し得る条件（独立trial）';d.core_properties.subject='条件付き分析・正式採用未定';d.core_properties.comments='Source manuscript preserved in sources; independent trial only.'
# Normalize direct spacing: source duplicate style spacing + fallback metrics caused overlap in first render.
allp=list(d.paragraphs)+[p for t in d.tables for row in t.rows for c in row.cells for p in c.paragraphs]
for p in allp:
 fmt=p.paragraph_format;fmt.line_spacing=Pt(17);fmt.line_spacing_rule=WD_LINE_SPACING.AT_LEAST
 fmt.space_before=Pt(0);fmt.space_after=Pt(7);fmt.keep_together=False;fmt.keep_with_next=False;fmt.page_break_before=False
 snap=OxmlElement('w:snapToGrid');snap.set(qn('w:val'),'0');p._p.get_or_add_pPr().append(snap)
 for rr in p.runs:
  rr.font.size=Pt(10.5);rr.font.name='Droid Sans Fallback';rr.font.color.rgb=RGBColor(0,0,0)
  rr._element.get_or_add_rPr().rFonts.set(qn('w:eastAsia'),'Droid Sans Fallback')
 if p.style.name in ['Heading 1','Heading 2','Title']:
  fmt.keep_with_next=True;fmt.space_before=Pt(12)
  for rr in p.runs:rr.font.bold=True
 if p.style.name=='Heading 1':fmt.page_break_before=True
for t in d.tables:
 for row in t.rows:
  for c in row.cells:
   for p in c.paragraphs:
    p.paragraph_format.line_spacing=Pt(12);p.paragraph_format.line_spacing_rule=WD_LINE_SPACING.AT_LEAST;p.paragraph_format.space_after=Pt(3)
    for rr in p.runs:rr.font.size=Pt(8.5)
d.save(target)
(O/'FIGURE_TABLE_INDEX.md').write_text('''# 図表・数式対応

|番号|内容|元データ／計算|画像／本文|
|---|---|---|---|
|図1|B規模別gap|PATH1_QUALITY_COMPARISON.csv；MEAN/GROVER/ACTIVE|PATH1_FIGURES/F1_quality.png/pdf|
|図2|B初期差|同CSV；MEAN/GROVER|PATH1_FIGURES/F2_initial_delta.png/pdf|
|図3|連続qと総量DC率|PATH2_SENSITIVITY_SUMMARY.csv；u1/V3.5|PATH2_FIGURES/F3_continuous_q.png/pdf|
|図4|未知・追加mass相殺|PATH2_BOUNDARY_RESULTS.csv；T08/B015/B051|PATH2_FIGURES/F4_cancellation.png/pdf|
|表1|系列・母集団|EXPERIMENT_INVENTORY.csv|THESIS_SECTIONS 3.1|
|表2|代表方式品質|PATH1_QUALITY_COMPARISON.csv；18行|THESIS_SECTIONS 4.1|
|表3|質量ゼロ境界|PATH2_BOUNDARY_RESULTS.csv；先頭5行|THESIS_SECTIONS 4.3|
|表4|任意目標q|PATH2_BOUNDARY_RESULTS.csv；末尾8行|THESIS_SECTIONS 4.4|
|式1–7|目的・gap・時間条件・mass・DC・相殺・総量比|方法3.3–3.8／scripts/analyze.py|独立trial内の番号|

図1の厳密参照分母は78/78/78/78/57/38、図2の全入力分母は78/78/78/78/78/70。図3は共通460速度の総量比。図4は異なる部材設計を分けた相殺式であり完成pack性能差の横断比較ではない。旧原稿の図表・数式番号はsource DOCXで保全した。
''')
(O/'THESIS_BUILD.json').write_text(json.dumps({'source_path':str(source),'source_sha256':hashlib.file_digest(source.open('rb'),'sha256').hexdigest(),'output':str(target),'paragraphs':len(d.paragraphs),'tables':len(d.tables),'inline_shapes':len(d.inline_shapes),'markdown_characters':len(text),'equation_numbers':7,'references':12,'method':'copy original; replace body with independent trial sections; preserve original bytes in sources','visual_status':'PENDING_RENDER'},ensure_ascii=False,indent=2))
print((O/'THESIS_BUILD.json').read_text())
