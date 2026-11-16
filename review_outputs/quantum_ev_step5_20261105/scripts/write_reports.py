from pathlib import Path
import pandas as pd,numpy as np,json,hashlib,datetime
O=Path(__file__).resolve().parents[1];R=O.parents[1];D=O/'data'
S1=R/'review_outputs/quantum_ev_step1_design_trial_20261104_153058';S2=R/'review_outputs/quantum_ev_step2_analysis_trial_20261104_155535';S3=R/'review_outputs/quantum_ev_step3_synthesis_trial_20261104_174309';S4=R/'review_outputs/quantum_ev_step4_thesis_integration_trial_20261104_184043';A4=R/'review_outputs/quantum_ev_step4_evidence_decisions_20261104_183654';P=R/'review_outputs/no_sumo_full_analysis_20261102/run01'
s=json.loads((D/'SUMMARY.json').read_text());ds=pd.read_csv(D/'GAP_DESCRIPTIVE_STATISTICS.csv');ins=pd.read_csv(D/'INPUT_UNIT_STATISTICS.csv');d=pd.read_csv(D/'B_PLAN_GAPS_36800.csv');ic=pd.read_csv(D/'INPUT_CONFIG_MEANS_3680.csv');ip=pd.read_csv(D/'INPUT_MEANS_460.csv');cnt=pd.read_csv(D/'IMPROVED_EQUAL_WORSENED.csv');op=pd.read_csv(D/'OPERATIONAL_SUMMARY.csv')
def write(n,t):(O/n).write_text(t.strip()+'\n')
def md(frame):
 def cell(x):
  if isinstance(x,(float,np.floating)):return f'{x:.6f}'
  return str(x).replace('|','／').replace('\n',' ')
 return '\n'.join(['| '+' | '.join(map(str,frame.columns))+' |','| '+' | '.join(['---']*len(frame.columns))+' |']+['| '+' | '.join(cell(x) for x in row)+' |' for row in frame.itertuples(index=False,name=None)])
def fmt(v):return f'{v:,.3f}'
configs=sorted(d.config_id.unique());x=ins[ins.level.eq('input_mean_by_config')];co=x.pivot(index='config_id',columns='metric',values='mean').reset_index();co['入力数']=460;co=co.rename(columns={'delta_s':'平均符号付き差 秒','abs_delta_s':'平均絶対差 秒','relative_gap_percent':'平均相対差 %'})
allstats=ds[ds.level.eq('all_plans')][['metric','n','mean','median','sd','min','max','q1','q3','p05','p95']];instats=ins[ins.level.eq('input_mean_all')][['metric','n','mean','median','sd','min','max','q1','q3','p05','p95']]
write('STEP5_BASELINE_AND_PRESERVATION.md',f'''# Step 5 基準と保全

作業日：2026年11月5日（Asia/Tokyo）。作業ディレクトリは `{O}` である。元実験を再実行せず、保存データの読取・再集計・独立原稿作成を実施した。

## 開始状態

HEADは `{(O/'evidence/GIT_HEAD_START.txt').read_text().strip()}` である。開始時はmainがorigin/mainより7commit先行し、多数の既存未追跡成果物が存在した。未追跡ファイルを今回の生成物と誤認しない。Git状態の全行と既存tracked差分は `evidence/GIT_STATUS_START.txt` と `evidence/GIT_DIFF_START.patch` に保存した。commit/pushは実施しない。

`evidence/REPOSITORY_FILE_INVENTORY.csv` に既存研究ディレクトリのパス・容量・mtime_nsを記録した。`.conda`等の環境や`.git`を全件hashする監査ではない。`evidence/BASELINE_SHA256.csv` は既存review成果物、研究設計、コード、ルート原稿等を開始時にhashした台帳である。03_dataの大きなrawデータ群は一覧を保全し、実際に用いる入力は別途SHA256で固定した。外部保全ディレクトリのNPZ、候補MEASUREMENTS、greedy RESULT、protocolは読取前の `evidence/ANALYSIS_INPUT_SHA256.csv` で固定した。終了時照合結果は `evidence/PRESERVATION_RESULT.json` に保存する。

## 原稿の基準選定

基準は `{S4/'THESIS_STEP4_INTEGRATED_TRIAL.docx'}` および同名PDFである。採用根拠は同ディレクトリの `SOURCE_THESIS_AUTHORITY.md`、`FINAL_AUDIT_REPORT.md`、`STEP5_HANDOFF.md`、`THESIS_PRESERVED_CONTENT_AUDIT.csv` にある。Step3後の科学的採用判断を反映し、11月3日内容基準版の86OMML・27表・19画像を本文/保全付録に保持した、114頁の来歴確認済み統合版である。ファイルのmtimeや名前の新しさだけから選んでいない。後日のポスターevidence内コピーを独立の論文改訂版とは扱わない。研究者が承認した最終提出版であることを示す決裁記録は未確認であり、今回の改訂入力としての選定である。

元内容保全基準 `{R/'tmp_RsrchMstrDc_1026_results_integrated.docx'}` の既存記録hashは `53a3abac8d8e62db6442f92d850eb2f3bb58e876606a84f61f6fe3de1763f99f` である。Step5の実hashは開始台帳に記録した。新原稿 `THESIS_STEP5_REVISED.docx` を作成し、基準原稿を上書きしない。

## 科学的判断の優先順位

今回の明示指示、`{A4/'STEP4_EVIDENCE_DECISIONS.md'}` と `CLAIM_EVIDENCE_MATRIX.csv`、補正後Step3、Step2/1・原実験の順で解釈を照合する。Step4の35判断（PASS9、CONDITIONAL18、HOLD5、NOT CLAIMED3）を変更しない。Step4統合台帳の31採用推奨とは件数/目的の異なる台帳である。

## 確認した資料群

|資料|入口・役割|
|---|---|
|Step1|`{S1}`：主対照・時間/統計/材料範囲の仕様|
|Step2|`{S2}`：73,600対照行のうち主対照36,800、支持460、QAOA診断、時間、材料感度|
|Step3|`{S3}`：414/46/41、Chen訂正、二経路の採用整理|
|Step3別統合|`review_outputs/quantum_ev_thesis_step3_integration_20261104_173959`：文献と旧全文trial。全文代替にしない|
|Step4科学判断|`{A4}`：Chen実用入力HOLD・主/参考の分離|
|Step4全文|`{S4}`：DOCX/PDF・全文・文献・保全対応|
|B保存計画|`{P/'B_PLAN_REFERENCES_36800.csv'}`：ルート/入力/seed/source hash|
|原実行|外部保全 `staged_qaoa_validation_20261102` と `cpu_matched_classical_swaps_r0_r5_20261101`：CPU模擬/古典の分離|
|材料/DC|T07/T08/T09の来歴はStep2 SOURCE_MAP/Step4科学台帳。凍結DCは `01_research_design/methodology/CONTROLLED_MASS_TO_DC_MODEL_FREEZE.json`|

SHA256の全文はCSVを正本とし、最終時点で照合する。既存HOLD・道路受入FAIL・T09_ROW183対向FAILを削除しない。
''')
write('STEP5_OBJECTIVE_GAP_ANALYSIS.md',f'''# B系列の解品質差の定量評価

## 比較と定義

460入力×8設定×10測定反復＝36,800保存bestを全件評価した。R0/R1/R2/R3/R4/R5は3/4/5/25/100/125顧客、78/78/78/78/78/70入力である。設定は `{', '.join(configs)}` である。入力ごとに設定8・rep0〜9の完全対応があり、3,680fitである。主解析の入力hash、旅行時間行列、顧客集合、容量216PE、サービス102秒、帰庫上限32,400秒を照合した。全保存候補とgreedyは可行である。全shotの可行率とは異なる。

候補は量子アルゴリズムの**古典CPUシミュレーションによる出力**である。実機量子計算で作られた計画ではない。mirror5は2層のmatching支持（2^floor(n/2)）、Grover p2/p3は全順列支持の模擬評価（subset DP/MC等）、activeは隣接swap p3のMPSとt={{0,.5,1}}gridである。8,192shotsの10測定は同一学習済みfitに条件付く。学習seed10回でも、8種類の古典ヒューリスティクスでもない。個別のseed entropyは `data/B_PLAN_GAPS_36800.csv` と元52列CSVに保持した。rep番号が同じでも入力/設定別entropyが異なるため、seed別集計 `by_measurement_rep` は測定反復番号の層別である。

greedyは `ITERATED_GREEDY_ADJACENT_SWAP` である。有向隣接swapの最良改善降下を行い、局所最適ではincumbentを乱数の2〜min(12,2n)swapで摂動し再降下する。初期解をbestに保持し、旧swap-QAOAの入力別CPU秒をsoft capに用いる。seedは2026110200+scale×10000+index+1000000、入力ごとに1seedである。古典初期解、脱位相random対照、全問題最適値とは別の対照である。古典の計算予算は現行8設定に対応せず、候補のraw sampled-bestと初期解保持ありの古典bestには出力規則差もある。この比較は保存条件下の品質記述であり、公平な総性能・量子帰属を識別する試験ではない。第二対照73,600行のうちrandomの36,800行は主比較に重ねて数えない。

J=Σ有向OD旅行時間（デポ帰還を含む、秒）、ΔJ=J_candidate−J_greedy、絶対差=|ΔJ|、相対差=100ΔJ/J_greedyとした。正は悪化、負は改善である。Step1〜4のΔJ_old=J_greedy−J_candidateから符号を反転した。保存分数を用いて全36,800行の旧差との厳密な逆符号を検証した。分母0は未定義とするが、対象のgreedyは全て正である。

## 全計画の記述統計

{md(allstats)}

SDはddof=1、四分位数と5/95百分位は線形補間である。全計画の平均符号付き差は **+{s['mean_delta_s']:.6f}秒**、平均絶対差は **{s['mean_absolute_delta_s']:.6f}秒**、平均相対差は **+{s['mean_relative_gap_percent']:.6f}%** である。全計画中央値は0秒・0%である。全差が非負のため符号付き平均と平均絶対差が今回だけ一致し、定義は区別する。greedy平均{ s['greedy_mean_s']:.6f}秒、候補平均{s['candidate_mean_s']:.6f}秒である。平均Jから計算した比は{s['ratio_of_means_percent']:.6f}%であり、個別相対差の平均22.243524%と異なる。比の違いはJ_greedyによる重み付けの違いである。

## 460入力を等重みにした分布

各入力の80出力を平均してから460入力の分布を算出した。

{md(instats)}

完全均衡設計のため全計画平均と入力等重み平均は一致するが、中央値とSDは一致しない。入力平均の典型値は中央値+7.473770秒・+0.634226%、入力間SD622.305258秒・31.345204ポイントである。全計画SD1,459.379051秒をこのSDと混同しない。25需要group・26親と規模間の派生関係が残り、460入力も独立無作為標本とはみなさない。今回は固定集合の記述統計に限定し、p値・母集団CI・新規bootstrap推論は行わない。

## 設定差

{md(co)}

6設定（mirror5とactive）は同じ初期解を保存しているため、同一の平均+1.040464秒・+0.065503%となった。Grover p2は+1,766.046542秒・+88.887051%、p3は+1,762.035546秒・+88.668125%である。全体平均は8設定を等重みに混合した記述であり、単一の「量子手法」の代表効果量ではない。二つのGrover設定が全正差総和の大部分を占める。設定・規模・予算・初期状態・支持・backendの同時差を、設定一因子の因果効果へ帰属しない。

Grover p2は3〜5顧客で0秒・0%、25顧客で+575.109082秒・+37.601662%、100顧客で+4,470.044218秒・+224.484514%、125顧客で+5,983.706453秒・+292.076023%である。R5の入力間SDは1,314.364537秒、中央値5,674.647848秒である。相対差の分母は主greedyであり、最適参照を分母とする旧292.1311%等のglobal gapとは別である。

## 少数入力への感度

入力80出力平均の範囲は0〜2,315.123775秒である。最大1入力の差総和への寄与は{s['max_input_contribution_percent']:.6f}%、上位5入力は{s['top5_input_contribution_percent']:.6f}%、上位23入力（5%）は{s['top23_input_contribution_percent']:.6f}%である。上位23入力除外でも平均差は{s['mean_without_top23_inputs_s']:.6f}秒である。1入力ずつ除外した平均の範囲は{s['leave_one_out_mean_min_s']:.6f}〜{s['leave_one_out_mean_max_s']:.6f}秒であり、単一入力だけで全体平均の方向が生じた結果ではない。大規模層とGrover設定への集中は明確であり、平均だけから典型入力を表現しない。診断値は `INPUT_INFLUENCE.csv`、設定内の全10repは元データに保持する。

## 改善・同等・悪化（補助指標）

{md(cnt[cnt.level.eq('all_plans')][['classification','count','percent','denominator']])}

## 出力と再現

`data/GAP_DESCRIPTIVE_STATISTICS.csv` は全計画・入力別・設定別・測定rep別・入力×設定別・規模×設定別の全指標統計である。`data/INPUT_UNIT_STATISTICS.csv` は入力平均の統計、`INPUT_CONFIG_MEANS_3680.csv` は10repの平均、`IMPROVED_EQUAL_WORSENED.csv` は全階層の件数/割合である。`scripts/analyze.py` は元NPZと元測定JSONおよび古典RESULTの経路を読み、分数の有向辺和・可行性・hash・入力対応を全件照合する。主要値はSUMMARY.jsonから追跡できる。

図4-1=F1_paired_objectives、図4-2=F2_gap_distributions、図4-3=F3_setting_input_boxes、図4-4=F4_input_gapsを作成した。散布/分布は36,800保存計画の記述、箱ひげは設定ごと460入力の10rep平均、入力比較は各80出力平均である。分布2種を1図に統合した。PNG300dpiとPDFを保存し、対象/単位/集計単位/比較対象を図とキャプションへ記載した。
''')
write('STEP5_OPERATIONAL_IMPACT.md',f'''# 解品質差と配送運用成果

## 保存条件と対象の限定

B入力NPZの全460件でready=0、due=32,400秒、顧客service=102秒、デポservice=0を確認した。容量は216PE、対象需要合計は `B_INPUT_CONDITIONS_460.csv` に保存した。顧客固有の配送時間窓は除かれており、時計時刻としての配送開始・契約期限・実出発余裕・取得から出発までの実測記録は存在しない。t0=0は保存モデルの時間原点であり、午前0時や実際の出発時刻とは同定しない。旧Aの保存定時率は入力・採用政策が異なるためBの効果へ転用しない。

## 確認可能な対応計算

同一入力・同一開始原点・待ち0・全顧客1回・共通サービス時間の下では、帰庫時刻R=J+102nであり、R_candidate−R_greedy=ΔJとなる。全36,800対応で確認した。帰庫差の平均は+441.790609秒である。配送完了を「最終顧客のサービス完了」とする場合は L=R−最終顧客→デポの旅行時間であり、差はΔJ−最終帰路差である。帰庫と配送完了を同義にしない。全顧客の完了順序もルートから再構成し、入力別平均と顧客別の局所最小/最大差を保存した。

{md(op[['config_id','n','mean_return_difference_s','mean_last_delivery_difference_s','min_last_delivery_difference_s','max_last_delivery_difference_s','min_candidate_slack_s']])}

最終顧客完了差が負の保存計画は180件である。これは移動総和が悪化しても最終帰路と順序の差により最終顧客が早く終わる場合があることを示す。各顧客時刻差はその顧客までのprefix経路に依存し、総移動差から一律に割り当てられない。平均顧客完了差は各入力内で顧客等重み後に計画/入力等重みであり、全配送件数重みの平均ではない。

## 期限までの余裕と定時率

共通帰庫上限に対する候補の余裕は最小{s['min_return_slack_s']:.6f}秒、最大{s['max_return_slack_s']:.6f}秒、greedyは最小{s['min_greedy_slack_s']:.6f}秒、最大{s['max_greedy_slack_s']:.6f}秒である。保存条件の全計画は帰庫上限内にあり、共通上限内の顧客完了割合も両側100%で差0ポイントである。これは**顧客時間窓を除いたモデルの上限遵守**であり、実測の契約定時配達率ではない。全てに大きな余裕があるため、対象Bに期限ぎりぎりの運用効果は観測されていない。実配送定時率は `contractual_on_time_rate=NULL` とし、0%や100%で代入しない。

## 時間差が成果に反映される条件

顧客jのgreedy完了をC_gj、期限をD_j、余裕をs_gj=D_j−C_gj、候補のprefix完了差をδC_jとすると、greedyが期限内で候補が遅れる条件はδC_j>s_gjである。帰庫ではδR=ΔJ、余裕s_g=32,400−R_gなのでΔJ>s_gで上限違反となる。これは条件式であり、新しい配送期限/開始条件を設定した再実験ではない。小さい正差でも余裕がさらに小さい場合は閾値を跨ぎ、両側が閾値内なら二値成果は変わらない。対象Bは後者に当たる。

計算・取得時間を出発前へ加える場合、固定時計の下で時刻差にδτ（両方式の出発遅延差）を加える必要がある。開始後の経路時間にCPU fit秒をそのまま追加しない。前処理/転送/検証を含むτ_totalとH_plan、実出発時刻は未同定であり、CPU scopeのみでは運用採用を確定できない。

## 採用政策との関係

保存候補はraw sampled-best、古典bestは初期解保持ありである。保存条件を変えず、参考として min(J_candidate,J_initial) と min(J_candidate,J_greedy) の目的値を算術で分けた。後者を仮に採用規則とすれば、候補全件がgreedy以上のため採用後J差は0秒である。これは新しい実運用でのfallback採用を観測した結果ではない。前者は古典初期と主greedyの差が残り、主greedyfallbackと同一ではない。実採用・実道路への接続はHOLDを維持する。

根拠は `data/B_PLAN_GAPS_36800.csv`、`B_INPUT_CONDITIONS_460.csv`、`OPERATIONAL_SUMMARY.csv`、元Bのinput/route/source hash、原protocolである。完了時刻差と帰庫差の相違はStep5で追加した定量整理である。
''')
conditions=[
['A 改善解の存在','mirror支持460でJ*_S=J_initial、J_greedy≤J_initialを照合','指定mirrorの2^floor(n/2)支持では改善候補がない（CONDITIONAL）','全順列や別mixerへの一般化は不可。activeは3点grid全t0であり全active支持の最小証明ではない'],
['B 改善解の取得','Bの差分布、診断3入力の9,312fit/93,120測定','支持内存在と有限予算での取得を区別。診断は主greedyが既に最適','Grover大規模の悪化原因は角度・予算・初期・測定等に分解し切れない'],
['C 時間的成立','CPU工程記録9,603、固定例Q34.643ms/脱位相35.014ms','CPUでの限定scope測定。greedy12.142msは1出力、Qは10測定','全工程τ_total・H_plan・QPU総性能HOLD'],
['D 計画採用','全36,800保存best可行、容量/帰庫条件をNPZ再検算','モデル上の可行性は確認。greedyfallbackなら採用後差0の条件式','現実の採用イベント・出発遅延・道路受入未検証'],
['E 成果への反映','帰庫差=ΔJ、最後の顧客差=ΔJ−帰路差、余裕最小7435.748秒','保存Bの共通上限遵守差0ポイント。実定時率には置換しない','契約期限と実行交通・顧客別時刻の運用検証HOLD']]
pd.DataFrame(conditions,columns=['condition','evidence','scope_and_judgment','unresolved']).to_csv(D/'PATHWAY1_CONDITIONS.csv',index=False)
write('STEP5_PATHWAY1_CONDITIONS.md',f'''# 経路1の成立条件

必要な接続をA〜Eに分ける。いずれかの段階だけをもって量子技術の運用寄与としない。ΔJの符号は候補−greedyである。

{md(pd.DataFrame(conditions,columns=['条件','証拠','適用範囲と判断','未検証事項']))}

## 支持不存在と取得失敗の区別

`{S2/'PATH1_SUPPORT_AUDIT.csv'}` はmatching-chain独立DPにより460入力全てで支持内最良値=初期値を示す。`data/B_PLAN_GAPS_36800.csv` の初期値/主対照対応から J_greedy≤J_initial が成立するので、この特定支持内ではJ_candidate<J_greedyを満たす解がない。測定shotsや同じ支持内の学習を増やしても不存在を補うことはできない。これは支持の制約に関する結論である。activeのt0選択を、その広い全到達空間での不可能性証明へ置換しない。

Grover全順列支持のAは全問題の最適参照と主greedyを比較して、支持最小がgreedyより小さい入力でのみ成立を確認できる。監査後414参照は再列挙234、保存DP78、独立有理LP61、保存MIP等値のみ41であり、外部証明未了41を区別する。残る46はJ*未証明である。Bの差と可行性は460全件で利用できるが、46のglobal gapを推定補完しない。参照の有無と「改善解が存在しない」を同義にしない。

診断R1_020のfull/基底/graphでは最適取得p1=58/97、p2=78/97、条件付きWilson95%は49.8〜69.0%、71.4〜87.1%である。初期状態等の条件を伴う取得能力の結果である。greedyは診断入力で最適のため、最適取得確率の差をgreedy超えと解釈しない。旧10測定を97独立学習と混ぜない。

## 単一原因への帰属を避ける

mirrorはAの不成立を指定支持で確認できる。一方Groverの大規模悪化は、全支持であることだけでは角度最適化・有限shots・初期状態・各backendの精度/予算・出力規則を統制したことにならず、単一原因を確定できない。旧greedyと8設定の予算・初期解保持の差も残る。CPU模擬結果からQPU優劣、量子優位性、量子一般の不可能性を主張しない。

根拠はStep2 `PATH1_PAIRED_COMPARISONS.csv`、`PATH1_SUPPORT_AUDIT.csv`、`EXACT_REFERENCE_STATUS.csv`、`QAOA_CONTROLLED_EXPERIMENT_REPORT.md`、`PATH1_RUNTIME_PROTOCOL.md` とStep4 P1-01〜14である。
''')
# Quantify the reference conditions A separately (exact-status classes retained).
refs=pd.read_csv(S2/'EXACT_REFERENCE_STATUS.csv',keep_default_na=False);pair=pd.read_csv(S2/'PATH1_PAIRED_COMPARISONS.csv',keep_default_na=False,low_memory=False);pair=pair[pair.primary_comparison].drop_duplicates('problem_id');from fractions import Fraction as F
ar=[]
for x in pair.to_dict('records'):
 ex=x['exact_fraction'];eq='UNPROVED_JSTAR' if not ex else ('REFERENCE_BETTER_IN_FULL_SUPPORT' if F(ex)<F(x['JC_fraction']) else 'GREEDY_EQUALS_REFERENCE')
 ar.append(dict(problem_id=x['problem_id'],reference_class=x['reference_evidence_class'],A_full_support_status=eq,reference_status=x['reference_status']))
pd.DataFrame(ar).to_csv(D/'FULL_SUPPORT_EXISTENCE_BY_INPUT.csv',index=False)
write('STEP5_PATHWAY2_EVIDENCE.md',f'''# 経路2の科学的採用結果

## 主分析の会計

gross設計電力量をE_g、平均電圧をV、正極容量をq、追加利用率をu、正負極活物質割合をf_p/f_n、負極容量をq_n、N/Pをrとする。正極活物質m_p=E_g/(Vqu)、正極乾燥塗工材m_p/f_p、負極乾燥塗工材E_g r/(V q_n f_n)を合計し、明示したその他部材を加える。活物質を乾燥塗工材へ二重加算しない。

T08主式は M=E_g/V[1/(q u f_p)+r/(q_n f_n)]+F+D+δ である。Dを別記した場合はFとの重複を除き、元T08が未知設計部材を個別に同定した意味ではない。∂M/∂q=−E_g/(Vf_puq²)、∂M/∂u=−E_g/(Vf_pqu²)、∂M/∂V=−E_g/V²[1/(quf_p)+r/(q_n f_n)]である。固定部材の局所感度は1である。正の定義域、他変数固定、同じ会計が条件であり、容量/電圧/寿命/安全が現実に独立調整できるという証拠ではない。全偏微分は `data/PATH2_ANALYTICAL_SENSITIVITY.csv` に保持した。

同一電圧・負極・活物質割合・部材を固定し基準利用率1なら、q_s u_s>q_refで正極質量が減少する。より一般には利用率、電圧、負極、面積依存部材を含む式へ戻す。同じ会計内の削減bと、その会計外のscenario側追加差δについて削減ΔM=M_ref−M_s=b−δとなる。δ<bで削減、δ=bで消失、δ>bで逆転する。恒等式単体を学術的な新発見とはしない。

## T07/T08/T09の役割

T07/T08の数値受入や検算PASSは材料入力の実用適格性PASSと異なる。Step4 M-01〜03とP2各判定を優先する。T07を実材料検証の根拠として昇格しない。T08は解析感度の主モデル、T09は面積・箔・膜・孔隙/液量と未知BOMの構造依存を示す補完である。fixed_loadingとfixed_areaは設計方針が異なり、面積連動部材への伝達も異なる。T08のF=34kgをT09既知subtotalへ重ねて足さない。casing/tabs/foilmargin/packstructure等の未知はNULLのままにする。完成セル/パック成立には全電池容量・電圧・利用率・BOMと設計採用の根拠が必要である。

パック質量差を車両質量差へ1対1に伝えるのは、その他車体、補強、搭載方式、荷重、運転者等を固定しパックだけを交換するモデル条件である。実製品で必要となる別部材変化を0と断定しない。

## 材料非依存Controlled-DC

凍結式は各区間の転がり・空力・並進加減速・回転等価質量仕事の和を区間ごとに正値化し、η=.9でDCへ換算する。E_DC(m)=Σmax(a_t m+c_t,0)/η である。平坦、回生なし、補機/旋回損失除外、積載0、運転者55kg、回転等価61kgのモデルである。区間ごとのa_tは減速で負にもなり得るため、物理の直観だけで単調性を仮定しない。max(affine,0)の和は凸区分線形であり、下端右微分が正なら同じ区間で傾きが正である。

保存460軌跡×2Crr、走行質量1000〜1250kgでは、下端1000kgの右微分は以下である（Wh/kg、軌跡間SD）。

{md(pd.read_csv(D/'DC_MASS_KERNEL_SUMMARY.csv'))}

同じ軌跡・物理条件で比較質量が両方ともこの区間内なら、ΔM=M_ref−M_sとΔE=E_ref−E_sの符号が一致する。これは固定モデル内の応答であり、実車電力量の推定値ではない。距離、速度、正の加減速が異なるため感度は軌跡ごとに変わり、単一の材料削減率には集約できない。2Crrは同じ460軌跡を共有し920独立走行試験ではない。

## Chen依存値は参考のままである

Chen et al. (2020), Nature Communications 11, 3411, DOI: [10.1038/s41467-020-17126-3](https://doi.org/10.1038/s41467-020-17126-3) の報告容量/保持率と逆算は確認されているが、逆算qの分母cycle/activationと実用full-cell入力適格性はHOLDである。171.875/195.959596Ah/kgからのT08具体質量差、利用率/電圧の具体境界、約0.413%のDC差、T09具体差、49点/81点/162条件を、代表的な実材料効果として採用しない。既存論文の参考節5.5を保持する場合も入力未適格の参考条件と明記する。要旨/結論の主効果量から除く。

量子による物性計算→合成→電極→full-cell→完成pack→実車への接続、安全・寿命・熱・機械制約、未知BOM、実道路受入は未検証である。T09_ROW183対向FAILと道路受入FAILは既存判定として維持し、今回の軽量検算PASSで上書きしない。

根拠：Step4科学台帳M/P2、Step4 `data/DC_MASS_KERNEL_INDEPENDENT.csv`、凍結DC、Step2 SOURCE_MAPのT8/T9/BR、Step3 `scripts/dc_independent.py`。材料入力を追加した実験は行っていない。
''')
comparison=[
['上流能力','量子回路アルゴリズムのCPU模擬を実行','量子材料計算・材料合成は未実行'],
['中間成果','保存bestのJ差を同一入力greedyと対応','q/u/V→活物質/既知部材→走行質量の条件式'],
['主効果量','平均+441.790609秒/+22.243524%、入力中央値+7.473770秒','1000kg下端DC質量感度2.368077/2.431780Wh/kg（平均）'],
['運用への伝達','prefix時刻・帰庫・期限余裕・採用・総取得時間に依存','同じ部材会計・車両換装・固定軌跡・物理に依存'],
['消失条件','同等解、greedyfallback、期限閾値を跨がない','追加差δ=b、質量依存のない評価条件、別部材相殺'],
['悪化/逆転','候補がgreedyより長い、遅延が余裕を超える','δ>b、利用率/電圧/設計差が容量改善を相殺'],
['検証済み範囲','指定支持の不存在、保存差、モデル時刻算術','モデル偏微分、既知会計、460軌跡の質量応答'],
['仮定依存','同じ出発・サービス、静的OD、採用条件式','正の定義域、非重複会計、1000〜1250kg凍結物理'],
['未検証','QPU、総時間、契約定時率、実採用/実交通','実用q、full-cell/BOM、量子→実材料、実車DC'],
['証拠と成熟度','具体アルゴリズムの計算出力はあるがQPU実用性未評価','下流のモデルのみ。上流の技術達成を前提化できない']]
pd.DataFrame(comparison,columns=['axis','path1','path2']).to_csv(D/'CROSS_PATH_COMPARISON.csv',index=False)
write('STEP5_INTEGRATED_DISCUSSION.md',f'''# 二経路の統合考察

{md(pd.DataFrame(comparison,columns=['比較軸','経路1','経路2']))}

平均+441.791秒と中央値0秒の併存は、平均的な悪化がすべての出力に一様に生じたのではなく、設定と入力層へ集中したことを意味する。入力平均中央値は7.474秒であり、集計単位を変えると典型値も変わる。従って技術名だけでシステムへの効果を一つの改善率として記述することはできない。旧8設定は予算と出力規則が揃っておらず、これは計算条件を固定した観察的な比較である。

経路1で支持内の改善解不存在を確認できることと、全支持で有限予算による取得が難しいことは異なる。mirrorの不存在は指定入力・指定支持に対する強い構造的証拠である。一方、Grover大規模の差の機構は、角度学習、初期状態、shots、backend/精度、計算予算の複数候補を残す。最適取得率の向上、greedy超え、計算時間適合、実運用の採用は別段階である。

同じJ差でも、帰庫時刻は総移動差をそのまま受けるが、顧客完了時刻はprefixと最終帰路に依存する。さらに全候補の帰庫余裕が7,435.748秒以上ある今回のモデルでは二値の上限遵守に差が現れない。これは品質差が無意味なことを示すものではなく、選んだ成果指標に変換する閾値が作用していないことを示す。計画締切H_planを帰庫上限へ代入すれば取得段階と実行段階が混同される。

経路2では容量差だけからパック差を確定できず、電圧/利用率と非活物質部材が質量変換を変える。未知部材を0にすれば見掛けの完成品効果が生じるため、NULL保持が科学的範囲の一部となる。ΔM=b−δは収支恒等式であるが、どの部材がbに入り、どの走行条件でDCへ符号が伝わるかは別途モデルを検査する必要がある。下端感度が正であることの検算は、その限定範囲での符号伝達を支える。

二経路を統合した研究上の知見は、技術能力の存在だけでは対象システムの寄与の方向も大きさも同定できず、主対照/支持・取得・採用/余裕、または部材会計/質量・走行応答という具体的な接続を確定する必要があるという、対象事例に限定した知見である。この知見の根拠は共通矢印の類似だけではなく、保存差の全分布、支持460の証明、非同義な時刻差、採用判断に沿うDC応答を併置した点にある。

経路1は実行済みCPU模擬アルゴリズムに対する比較であり、経路2は未実現の材料能力を上流に置いた下流モデルである。証拠の性質と成熟度が異なる。秒とWhを合算せず、同じ「量子効果率」を作らない。社会技術的移行、経済性、組織/制度/受容、排出削減の実証には及ばない。これらは先行研究での問題設定と比較できるが、今回の二経路から一般法則を導くことはできない。
''')
# Existing bibliography and explicit comparison scopes; inherited metadata preserved with added primary check notes.
refs=pd.read_csv(S4/'LITERATURE_EVIDENCE_MATRIX.csv',keep_default_na=False)
rows=[]
primary={
'OR03':('https://arxiv.org/abs/1709.03489','v2公開要旨・書誌','可行部分空間mixerは既知。本研究は指定mirror460の不存在と主対照差を追加'),
'OR02':('https://arxiv.org/abs/2006.00354','v2公開要旨・書誌','全可行重ね合わせと状態準備は既知。全支持での取得成功と実用優位を同一視しない'),
'OR36':('https://arxiv.org/abs/2304.09629','v2公開要旨・書誌','CVRP分解/TSPの解品質評価は先行例。本研究は全保存分布・入力依存・支持証明が対象'),
'OR37':('https://arxiv.org/abs/2204.11890','v2公開要旨・書誌','電池物性の耐故障量子計算/資源。実材料/実車効果の証拠ではない'),
'L14':('https://web.cecs.pdx.edu/~maf/publications.html','著者大学サイト書誌＋既存原著要旨','経路/速度/電力/費用接続の先行例。統合構造自体の新規性を主張しない'),
'OR28':('https://doi.org/10.1038/s41467-020-17126-3','Step4保存原著Fig5g/方法。Step5 web再取得はエラー','材料報告と逆算/実用採用を分離。科学的HOLD維持')}
for x in refs.to_dict('records'):
 if x['reference_id'] in primary:
  url,scope,rel=primary[x['reference_id']];rows.append(dict(reference_id=x['reference_id'],authors=x['authors'],year=x['year'],title=x['title'],DOI=x['DOI'],URL=url,checked_scope=scope,comparison=rel,status='LIMITED_PRIMARY_CHECK' if x['reference_id']!='OR28' else 'SAVED_PRIMARY_AND_MATERIAL_HOLD'))
rows.append(dict(reference_id='S5-L01',authors='Aaron Brooker; Jeffrey Gonder; Lijuan Wang; Eric Wood; Sean Lopp; Laurie Ramroth',year=2015,title='FASTSim: A Model to Estimate Vehicle Efficiency, Cost and Performance',DOI='10.4271/2015-01-0973',URL='https://www.nrel.gov/docs/fy15osti/63623.pdf',checked_scope='研究所公開原著p1要旨/モデル概略・書誌',comparison='走行cycle/物理モデルによる車両評価は既知。凍結DCの限定算術検証はFASTSim/実車validationと別',status='LIMITED_PRIMARY_CHECK'))
pd.DataFrame(rows).to_csv(O/'evidence/LITERATURE_COMPARISON.csv',index=False)
write('STEP5_ACADEMIC_CONTRIBUTIONS.md',f'''# 学術的貢献と新規性の範囲

## 実証的貢献

実際に検証したのは、指定B系列の保存候補/古典greedyの同一入力対応と、符号付き差平均+441.790609秒、平均相対差+22.243524%、中央値・百分位・入力/設定別の分布である。平均/絶対差/百分率/平均J比の非同義性を実データで区別した。入力平均中央値7.473770秒と設定別平均、影響診断は、改善件数だけでは見えない悪化の局在を示す。新たなQPU効果の実証ではない。

460のmirror支持で改善候補不存在を確認した既存証拠を、有限予算での取得失敗と分けて採用した。固定ODでは帰庫差=ΔJであるが最終顧客完了差は異なり、対象共通上限内では遵守差0ポイントとなることを再集計した。実契約定時率の改善を実証したものではない。

経路2の主実証範囲は保存軌跡を用いたモデル内検算である。記号的感度、会計境界、1000〜1250kg/460軌跡での材料非依存DC応答を採用する。材料性能・完成packの効果としては主張しない。

## 方法的貢献

主対照、支持内最小、最適参照、取得確率、時間scope、計画採用、運用時刻を同一の成功指標へ混ぜず、追跡可能なファイル/式/判断へ対応させた事例評価に特徴がある。全36,800件を保持しつつ460入力とその親/group依存を明示した。材料側は入力来歴、数値整合、実用適格性、モデル帰結、実車validationを独立に審査した。一般的な統計手法や因果媒介概念自体を新規発明したとはいえない。

## 先行研究との比較

{md(pd.DataFrame(rows)[['reference_id','authors','year','title','DOI','URL','checked_scope','comparison']])}

Hadfield et al.の可行部分空間、Bärtschi/Eidenbenzの状態準備、Palackal et al.の量子配送問題における可行性・解品質評価は先行している。本研究の追加部分は指定cohortの主greedy差分布と支持証拠の対応である。[Hadfield原著](https://arxiv.org/abs/1709.03489)、[Grover mixer原著](https://arxiv.org/abs/2006.00354)、[Palackal原著](https://arxiv.org/abs/2304.09629)。

Davis/Figliozziの経路・電力・費用接続とFASTSimのcycle/物理モデルは既存である。したがって「性能と運用を結んだ最初の研究」としない。本研究の凍結DCは補機・回生等を除くため、FASTSimの実車比較検証を本研究へ継承しない。[著者公開一覧](https://web.cecs.pdx.edu/~maf/publications.html)、[Brooker原著](https://www.nrel.gov/docs/fy15osti/63623.pdf)。

Delgado et al.は量子による電池物性評価の計算・資源を扱う。本研究はその上流計算を実行せず、材料側から質量/DCへ伝わる条件を分離する。[Delgado原著](https://arxiv.org/abs/2204.11890)。Chenの原著はStep4保存一次資料の該当実験のみを使用し、再取得失敗で採用判断を上書きしない。

## 理論的示唆と限界

対象事例では、上流技術の能力から成果の符号・大きさを直結して同定できず、比較基準と中間変換・採用条件が必要となる。これは社会技術システム評価への限定した解釈であり、一般理論の検証ではない。δ=bは会計恒等式、閾値内なら二値成果が変わらないことは閾値定義の帰結であり、それだけを新規性としない。

調査は既存Step4台帳20項目と関連一次資料の限定確認であり、網羅的systematic reviewではない。公開要旨/書誌の確認を全文精読完了と表現しない。「初めて」「世界初」「先例がない」は使用しない。旧Papachristos引用原意図と一部保存書誌/全文はHOLDであり、現行主張の支えには用いない。材料HOLDや実車/QPU未検証のままで、一般的量子優位を新規性に置くことはできない。
''')
# Compact source map for major numerical statements.
claimrows=[
['S5-P1-01','平均差+441.790609秒、相対+22.243524%','data/SUMMARY.json;data/B_PLAN_GAPS_36800.csv',str(P/'B_PLAN_REFERENCES_36800.csv')+';'+str(S2/'PATH1_PAIRED_COMPARISONS.csv'),'candidate fraction−greedy fraction、100Δ/Jg、全件平均','PASS_FIXED_COHORT','要旨/3.8/4.2/7'],
['S5-P1-02','計画中央値0、入力中央値7.473770秒','data/GAP_DESCRIPTIVE_STATISTICS.csv;data/INPUT_UNIT_STATISTICS.csv','同上','入力80出力平均→460入力のmedian、ddof1','PASS_DESCRIPTIVE','4.2/6.1'],
['S5-P1-03','設定差/規模差','data/INPUT_UNIT_STATISTICS.csv;data/INPUT_CONFIG_MEANS_3680.csv','同上','入力×設定10rep平均→入力等重み','CONDITIONAL_UNMATCHED_BUDGET','4.3'],
['S5-P1-04','入力影響診断','data/INPUT_INFLUENCE.csv;data/SUMMARY.json','同上','正差総和の上位寄与/leave-one-input-out','PASS_FIXED_COHORT','4.4'],
['S5-OP-01','帰庫差/最終顧客差/余裕','data/B_PLAN_GAPS_36800.csv;data/B_INPUT_CONDITIONS_460.csv','ANALYSIS_INPUT_SHA256のNPZとgreedy RESULT','R=J+102n、L=R−最終帰路','CONDITIONAL_STATIC_OD','4.5'],
['S5-OP-02','共通上限内100%両側/契約率NULL','data/OPERATIONAL_SUMMARY.csv','同上','全顧客prefix完了≤32400。契約率は未同定','CONDITIONAL_NOT_REAL_OTD','4.5/6.3/7'],
['S5-P1-A','mirror460支持内候補不存在','data/PATHWAY1_CONDITIONS.csv',str(S2/'PATH1_SUPPORT_AUDIT.csv'),'J*_S=Jinitial≥Jgreedy','CONDITIONAL_SPECIFIED_SUPPORT','4.6/6.2'],
['S5-P2-01','記号的感度/b−δ','data/PATH2_ANALYTICAL_SENSITIVITY.csv',str(A4/'CLAIM_EVIDENCE_MATRIX.csv'),'正の定義域で偏微分、非重複部材会計','CONDITIONAL_MODEL','5/6.4'],
['S5-P2-02','DC質量感度2.368077/2.431780Wh/kg','data/DC_MASS_KERNEL_SUMMARY.csv;data/DC_MASS_KERNEL_INDEPENDENT.csv',str(S4/'data/DC_MASS_KERNEL_INDEPENDENT.csv'),'1000kg右微分、軌跡間mean/SD','CONDITIONAL_FROZEN_MODEL','要旨/5.3/7'],
['S5-H01','Chen実用材料HOLD','evidence/STEP4_EVIDENCE_DECISIONS.md',str(A4/'MATERIAL_INPUT_PROVENANCE_AUDIT.md'),'原報告/逆算/用途適格性を分離','HOLD_MAINTAINED','5.5/6.4/7'],
['S5-I01','二経路の条件・証拠非対称性','data/CROSS_PATH_COMPARISON.csv','本研究の各経路証拠と文献台帳','秒とWhを統合せず媒介を比較','CONDITIONAL_CASE_INTERPRETATION','6/7']]
pd.DataFrame(claimrows,columns=['claim_id','claim','step5_evidence','original_source','calculation','judgment','thesis_location']).to_csv(O/'evidence/CLAIM_EVIDENCE_MAP.csv',index=False)
# Seed mapping includes exact entropy and original PCG64 state. No claim of ten global seeds.
seed=pd.read_csv(P/'B_PLAN_REFERENCES_36800.csv',keep_default_na=False,low_memory=False)[['problem_id','config_id','fit_id','measurement_rep','measurement_seed_entropy','PCG64_seed_state4','seed_rule_source_sha256','shots']];seed.to_csv(D/'SEED_MAPPING_36800.csv',index=False)
print('reports and claim map written')
