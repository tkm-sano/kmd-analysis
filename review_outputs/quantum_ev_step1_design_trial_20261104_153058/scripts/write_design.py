from pathlib import Path
import csv,json,textwrap
O=Path(__file__).resolve().parents[1];R=O.parents[1]
P=R/'review_outputs/no_sumo_full_analysis_20261102/run01';T=R/'review_outputs/quantum_ev_conditions_full_trial_20261104_125659';U=Path('/home/takuma/kmd-analysis-pre-clean-20261102-112222/untracked');S=U/'review_outputs/staged_qaoa_validation_20261102';T8=U/'review_outputs/material_ev_stage2_20261026/run02';T9=U/'review_outputs/t09_open_data_model_20261029/run01';BR=U/'review_outputs/t08_t09_conditional_bridge_20261030/run01'
def md(n,s): (O/n).write_text(textwrap.dedent(s).strip()+'\n')
def table(n,rows):
 with (O/n).open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
md('SOURCE_MAP.md',f'''
# 根拠の参照記号

全パスは存在を検査した入力。ハッシュと版はSOURCE_PROVENANCE.csv、保存先変更はevidence/PATH_RELOCATION_MAP.csv。相対表記P/T等は以下の絶対パスを基準とする。

|記号|実在する場所|主な用途|
|---|---|---|
|R|{R}|現作業ツリー。HEADはevidence/START.json|
|P|{P}|11月2日全件監査。run_b.py/run_c.py/statistics_tables.py、B/C全件CSV|
|T|{T}|11月4日統合trial。RQ_REDESIGN_TRIAL.md、analyze.py、原稿THESIS_TRIAL.docx|
|S|{S}|B実行原本。mirror_family/grover_depth/active_adjacent_p3のPROTOCOL.json、SOURCE_SNAPSHOT、RUNS|
|T8|{T8}|T08元SCENARIOS.json、T08.json、MATERIAL_ENERGY.csv、SOURCE_SNAPSHOT|
|T9|{T9}|T09 model.py、analyze.py、RUN_CONFIG.json、PARAMETER_SOURCES.csv、PACK_20KWH_SENSITIVITY.csv|
|BR|{BR}|T09_MASS_BOUNDARIES.csv、MASS_COMPONENT_BRIDGE.csv、DC_MASS_RESPONSE.csv、integrate.py|

権威順位：今回ユーザーが確定した方針 > 方針記録run03/01_POLICY_AND_SCOPE.txt > 元データ・実行コードの事実 > 既存trialの解釈。正式採用状況は変更しない。旧正式方針の文面を今回の方針へ自動昇格しない。

インターネット上の最新版や論文一次資料の再調査は今回のローカル監査には含めない。材料の報告値は保存シナリオ内の記録として扱い、掲載論文を今回再検証したという意味ではない。
''')
md('RQ_INDICATOR_ALIGNMENT.md','''
# RQと指標の対応（Step 1 trial確定仕様）

根拠はT/RQ_REDESIGN_TRIAL.md（既存trial案）と今回の研究者指定方針。READMEや正式原稿の旧問いを上書きしたものではない。RQ0/RQ1/RQ2/RQIの採用済み正式原本は今回確認できず、名称・文言の正式採用はHOLD。ただし以下の評価対応は本trial内で固定し、再選択を求めない。

|RQ|問う内容・経路|評価指標|系列|回答可能な範囲|不足証拠・判定|
|---|---|---|---|---|---|
|RQ0|量子技術がどの技術能力・適用・効果成立条件でEV配送へ寄与し得るか。両経路の上位問い|RQ1のΔJと時間条件、RQ2のΔMとΔEの成立・消失条件。単一合成点数を作らない|B、C、T08/T09と保存文献整理|固定入力・保存CPU工程・モデル内の条件を列挙できる|実運用・量子材料改善の因果接続HOLD、全体CONDITIONAL|
|RQ1|同一配送問題で古典近似より良い解を、計画作成の許容時間内に得る条件|主ΔJ=JC−JQ。補助相対率・取得率・可行率・gap・一致率・ばらつき。τtotal≤Hplan|B時間窓なし460入力×8設定×10測定rep。旧Aは歴史的補足のみ|同一費用表の解品質・初期差・厳密407・探索支持の制約|古典近似との現行予算統制、総時間、Hplan、compiled資源HOLD|
|RQ2|材料入力→モデル電池質量→車両質量→走行DCの伝達と相殺条件|ΔM=b−δ、ΔE=ELP−ES、100ΔE/ELP。q/u/V/未知部材のゼロ効果境界|C旧保存軌跡、T08主/T09補完|同一軌跡・同一物理仮定下の条件付き感度と構造依存|実材料の量子由来改善、完成パック・実車妥当性HOLD|
|RQI|技術能力だけで両経路の寄与が決まらない接続条件は何か|経路別の必要条件・モデル内十分条件・未接続台帳。効果量を合算しない|RQ1/RQ2の横断整理|符号化/探索支持/計算工程/部材会計/運行仮定の比較|社会制度の因果効果は未測定、解釈CONDITIONAL|

社会技術システムの一事例としてEV配送を扱う。実道路改善と量子材料改善は結果の主張に含めず、考察後段の未実証接続へ置く。定時配達率は主指標から除外し、旧Aの履歴は維持する。
''')
md('POLICY_CONSISTENCY_AUDIT.md','''
# 方針整合性監査

総合CONDITIONAL：新しい評価仕様は研究者方針に整合するが、既存正式文書・原稿に旧目的が残る。本作業は一切書き換えない。

検出根拠はevidence/POLICY_OCCURRENCES.csv（実パス、行、見出し、原文抜粋）。DOCXは本文・表内を含むXML段落番号pNをevidence/*TEXT.txtに保存した。単語の存在だけを違反とせず、その記述の役割を判別する。

|箇所|旧方針の残存とtrial修正案|判定|
|---|---|---|
|R/README.md 冒頭・研究目的・3経路と二つの成果|表題に定時配達率、目的に需要充足と電力量の両立、旧3経路と面接中心が残る。将来採用時は二経路の寄与条件と本trial RQ対応へ置換提案|現方針との整合FAIL、原本保全PASS|
|R/docs/research/RESEARCH_DESIGN_SUMMARY.md §1/§2/§5/§7|旧RQ/H1〜H3・面接工程・成果構成に定時配達率。現行の研究工程と同一視しない。履歴版を保持して採用後の版更新候補|CONDITIONAL|
|R/docs/research/EXPERT_INTERVIEW_PROTOCOL.md、回答票、分析ガイド|目的・指標・方法の旧面接記録。主研究方法として再採用しない。旧版・未実施状態を明示する候補|CONDITIONAL|
|R/tmp_RsrchMstrDc_1026_results_integrated.docx 序論・問い・方法・結果・考察および付録|序論で定時配達率をサービス水準とする記述が存在。現行A/B/Cの第5章と旧節の付録保存を区別する。目的/RQ/方法/結果見出し/考察主張を本trialに対応させる編集候補を記録。旧A数値や付録を削除しない|CONDITIONAL、未統合|
|R/tmp_RsrchMstrDc_1026_revised.docx / revisions/v07_results_integrated.docx|別候補として抽出・hash保存。mtime順だけで正式最新版を決めない|正式採用版HOLD|
|T/THESIS_TRIAL.docx、T/THESIS_SECTIONS_TRIAL.md|寄与条件中心の独立原稿案。定時率の除外や限界への言及は許容。最新の独立trialであり正式原稿ではない|PASS（位置付け）|
|P/stage0.py、P/FROZEN_PROTOCOL.json、P/statistics_tables.py|Aの主指標PE定時率と旧符号JQ−Jinitialが凍結されている。Pを改変せずStep2で別仕様として再出力|PASS（履歴維持）、流用時CONDITIONAL|
|T/PATH2_BOUNDARY_RESULTS.csv|0.1/0.25/0.4/0.5%はARBITRARY_ILLUSTRATIVE_TARGET。研究の成否判定に用いず、ゼロ境界を主とする|PASS（区別が必要）|

最新原稿の扱い：11月3日の統合記録に対応するルートresults_integratedを正式側の作業候補、11月4日のT/THESIS_TRIALを最新の独立案として両方確認した。版はevidence/MANUSCRIPT_VERSIONS.jsonとSOURCE_PROVENANCE.csvで識別。正式採用を本監査では決めない。

元データにon_time列が残ること、限界で定時配達率を説明することは方針違反ではない。未実証接続を実証結果として記載すること、CPU時間をQPU時間へ読み替えること、任意削減率を成功基準にすることはFAIL。
''')
md('PATH1_COMPARISON_BASELINES.md','''
# 経路1：比較対象

監査元はP/B_PLAN_REFERENCES_36800.csv、B_CLASSICAL_INITIAL_BASELINES.csv、B_AUXILIARY_CLASSICAL_IMPROVEMENTS.csv、B_EXACT_REFERENCE_COVERAGE.csv、S各PROTOCOL.jsonとSOURCE_SNAPSHOT。独立算術検査はevidence/NUMERICAL_CHECKS.csv。保存表の件数をそのまま引用せず460元NPZ・測定JSONへ照合した。

|規模|顧客数|入力数|厳密参照あり|未証明|古典初期解|古典近似|
|---|---:|---:|---:|---:|---:|---|
|R0|3|78|78|0|78|2法×78|
|R1|4|78|78|0|78|2法×78|
|R2|5|78|78|0|78|2法×78|
|R3|25|78|78|0|78|2法×78|
|R4|100|78|57|21|78|2法×78|
|R5|125|70|38|32|70|2法×70|
|計|—|460|407|53|460|920行|

時間窓なし・単一車両・全顧客デポ発着。目的Jは有向OD旅行時間総和（秒）、サービス時間は目的へ加えない。制約は全顧客の順列、需要合計≤216 PE、J+102n≤32,400秒。32,400秒は帰庫制約であり計算予算ではない。旧凍結Aの時間窓/99顧客やCの旧460軌跡とは別母集団。

8設定はmirror5（MEAN_P2、CVAR10_P2、CVAR01_P2、COHERENT2_P2、COHERENT4_P2）、GROVER_P2、GROVER_P3、ACTIVE_ADJACENT_P3_GRID。各460入力で10測定rep、36,800保存計画、3,680 fit。各repは8,192 shotsからのraw sampled-bestであり、初期解とのminを採用しない。

mirror：対称位置のpartial-SWAP、p2、支持2^floor(n/2)、奇数中央固定。COHERENTは初期状態2/4、他は1。MEANとCVaR(α=.10/.01)は学習目的が異なるが最終解品質は同じOD秒で評価する。Grover：全n!支持、一様順列初期状態、p2/p3、65,536学習cost pool。active：隣接parity SWAP p3、t={0,.5,1}の限定grid、初期経路からの局所支持。支持・初期状態・探索予算・近似精度が異なるため、群間差をmixerだけの因果効果としない。

|対照|役割と採用仕様|利用可能性・制約|
|---|---|---|
|古典近似|主対照JCはITERATED_GREEDY_ADJACENT_SWAPを事前指定。DEPHASED_RANDOM_SWAPは第二の近似対照として別々に表示。2法の結果を見て有利な方を選ばない|全規模460入力ずつ。元比較は旧swap実験へのCPU合わせであり現行staged8への予算合わせではない。入力hashと目的値は共通、解品質比較は条件付き、時間公平性HOLD|
|古典初期解|Jinitial。全460の補助対象。初期解が強いことと主近似対照で勝てることを区別|元RESULTで初期経路・評価・構築時間保存。近似改善処理を含む完成対照と同一視しない|
|全問題厳密最適値|J*。共通gap・一致率の参照、実用近似の代替にしない|407のみ。53は最適性未証明、HOLD。詳細はPATH1_REFERENCE_COVERAGE.csv|
|同じmirror支持のchain-DP最適値|探索支持の診断。全順列J*とは別。古典に対する量子優位の証拠にはしない|mirror5の同支持比較。初期目的とorbit最適値が一致する保存結果を確認する対象|

初期解の生成は元unified_no_windowsの保存RESULTSを上流とし、旧whole_rosterのRESULTへ転記されている。古典近似は同じ初期経路を基にした局所探索・脱位相ランダムswap（S/SOURCE_SNAPSHOTおよびcpu_matched_classical_swapsの凍結コード）。厳密値を初期解やQAOAの学習に漏らさず、評価参照に限る。

主比較は同一input SHA・目的・制約・サービス条件をjoin時に必須検査する。現行8設定のCPU予算統制がない既存JC比較は「保存条件での品質比較」と明記し、総時間/速度優位を付けない。Step2の新規統制比較で公平性を補う。
''')
md('PATH1_METRIC_SPECIFICATION.md','''
# 経路1：指標仕様

根拠：P/run_b.pyのFraction計算、S各SOURCE_SNAPSHOTのinteger_travel/validateおよびmeasure。目的は最小化。i=input SHAで識別する問題、a=アルゴリズム設定、r=0..9の測定反復。JCは指定古典近似ごとに保持する。初期解との差には必ずinitialと付記する。

|指標|式・単位|分母・集計|欠測・適用範囲|
|---|---|---|---|
|主ΔJ|JC,i−JQ,iar [s]|同一入力・制約での対応差。input内10rep平均→規模内等重み|JCまたはJQ欠測/非可行は差NULL、理由・対象数を併記。B全460が対象、現行予算統制は別HOLD|
|相対改善率|100(JC−JQ)/JC [%]|各入力のJCが分母、個別比の平均を主。比の総和とは別|JC≤0はNULL。JC不在時Jinitialで代用しない|
|補助初期差|ΔJinitial=Jinitial−JQ [s]|同一入力・rep|既存delta_objective_vs_initial_sはJQ−Jinitialなので符号反転。主ΔJへの改名は禁止|
|改善解取得率|sum_r I(acquired & feasible & ΔJ>0)/Nscheduled|設定ごと入力内10rep、その平均 [%]。初期差ならinitialを明示|未取得/非可行は成功0、実行記録自体欠測は未知として上下限[成功/N,(成功+未知)/N]と既知数。QC差NULLを失敗と決めない|
|可行計画取得率|sum I(acquired & feasible)/Nscheduled [%]|保存計画単位（B各設定4,600rep）→入力平均|全保存best36,800可行を確認。全shotsの可行率とは異なる。欠測実行は未知上下限|
|raw-shot可行率|1−invalid/8192 [%]|測定repの全raw shots|invalid count未保存はNULL。selected-bestの可行率100%で埋めない。保存されたactive等のみ|
|最適性gap|100(J−J*)/J* [%]|JQとJCの両方に共通参照J*。各入力内平均→厳密取得入力内平均|J*未証明53件はNULL。J*≤0はNULL。407分母と各規模内分母を明示、全460への外挿禁止|
|最適解一致率|sum I(J=J*)/Nexact-valid [%]|目的値一致。経路文字列一致とは別|参照あり407。未取得は失敗、実行未知は区間、参照なしは対象外。多重最適解を許容|
|試行間ばらつき|sample SD=sqrt(sum(Jr−mean J)^2/(m−1)) [s]、median、IQR=Q.75−Q.25 [s]|同一input×設定×fitの測定repのみ。quantile線形補間。m≥2でSD|m<2はSD NULL。fit間・学習seed間・入力間のばらつきと区別。各nを保存|

数値判定は保存小数をDecimal→共通整数scaleまたはFractionで読み、厳密に再計算する。元NPZはfloat64だがDecimal(str(x))の保存十進数を目的関数の定義値とする実装であり、そこでの比較許容幅εJ=0秒とする。ΔJ>0改善、=0同等、<0悪化。既存CSV float表示だけで一致判定しない。元分数・経路がないJCは同じ入力から厳密再構成できるまで一致判定HOLD。既存古典目的分数は利用可、経路再検証可能性は別記する。

float64の整合性検査に使う絶対1e−7秒（元run_b.py）やsample候補抽出1e−8秒（各measure）、MPSエネルギー差1e−7秒は、目的値が同等とする科学的閾値ではない。精度検査と効果境界を混同しない。近接値はexact deltaも併記し、必要なら表示精度感度として別表にするが、任意の1秒改善を成功定義にしない。

独立性：36,800行は独立観測ではない。10repは同一fit、8設定は同一入力、入力は26親・25需要groupに依存。CへこのID/分母を転用しない。Bは省電力最適化でも定時率実験でもない。
''')
md('PATH1_RESOURCE_SCOPE.md','''
# 経路1：資源の評価範囲

根拠：S各PROTOCOL.json、SOURCE_SNAPSHOT、P/B_RESOURCES_PER_FIT.csv、B_SAVED_RESOURCES_LONG.csv。実験環境S/ENVIRONMENT.jsonはPython3.11.15、NumPy2.2.5、SciPy1.15.3、Qiskit2.1.2/Aer0.17.2、Linux/x86_64・hostname hayate、worker内1thread、GPU/QPU実行false。記録は実験群単位であり、全fitのCPU機種・負荷・実行時刻が統一記録されているわけではない。

|要因分類|確認できること|採用しない推測・HOLD|
|---|---|---|
|問題符号化|旧A位置符号化はn²二値（3/4顧客で9/16）。B mirrorはfloor(n/2)二値方向、支持2^floor(n/2)。Groverはn!の全順列支持。activeは局所labelネットワーク|支持の情報量と実装論理量子ビット数は異なる。B全8設定に旧n²を当てはめない|
|アルゴリズム|mirror p2のcost phase/partial SWAP、Grover p2/p3のcost phase/projector mixer、active p3の隣接parity SWAP。8192shots/測定rep×10、3680fit|layer数pはcompiled depthではない。COBYLAのmaxiterは関数呼出制限、実反復数ではない|
|計算アーキテクチャ|mirror binary MPS bond≤256/cutoff1e−13（精度検査1e−14）、active label MPS rank64、Grover subset DP(n≤25)/certified MC(n>25)|two_site_gates、QR_moves、DP/MC samples等はbackend処理回数。nativeゲート数へ換算しない|
|ハードウェア|CPUの理想化/数値誤差制御シミュレーション。保存hardware_qubits/compiled_gate_count/compiled_depthは未記録|native gate set・接続・noise・誤り訂正・物理量子ビット数・QPU秒はHOLD|

mirrorの二値方向はR0..R5で1/2/2/12/50/62。これを完成実装の論理qubit数とは呼ばない。元旧Grover構築には2n²−2という論理回路記述もあるが、現行staged p2/p3の補助qubit・状態準備・projector・展開回路まで同じ資源で実装された証拠ではないため現行必要量へ移植しない。

学習：mirror≤64 unique評価（basis9点またはcoherent12点＋2 COBYLA starts×24）、Grover≤68（2starts×32＋初期点、最終beta解析式）、active3grid（t0は解析的初期点、t.5/1を数値評価）。trace長はunique評価数、optimizer反復実数は全fit未保存。CVAR学習のみ1024shots/評価、Grover学習65,536 cost poolはQPU shotsではない。主系列は一学習fit当たり10測定反復。代表点の3学習seed再試行は全460の独立10学習とは異なる。

層・量子ビット・ゲート・shots・反復の依存は問題規模、支持、学習目的、精度、コンパイル先で変わる。現行保存値から一意の全学習回路shots総数、compiled資源、物理qubitを算定しない。Step2ではコードからの論理回路資源と実行backend工程の双方を分離して追加記録する候補とする。
''')
md('PATH1_TIME_CONDITION_SPEC.md','''
# 求解時間条件

計画作成の起点を「入力が揃い計画作成を開始する時点」、終点を「可行性が確認され運行側へ計画が渡る時点」とする。τtotal≤Hplan。Hplanは利用場面の計画締切から根拠付きで定義する必要があり、現資料にその数値根拠を確認できないためHOLD、数値を設定しない。

τtotalは前処理＋古典初期化/近似処理＋パラメータ最適化＋必要な回路評価/測定＋最終検証＋後処理＋転送/待機のelapsed critical path。optimizerに含まれるシミュレーションを再加算しない。並列処理がある場合はCPU秒の合計で総elapsedを代用せず、共通開始終了のwallを主とする。キャッシュ生成/初期学習を含むcold条件と既学習/キャッシュ利用のwarm条件を別に固定し、同じ条件で比較する。

Bのfit wall/CPUは保存工程の実測である。mirrorには最適化後の精度再検査と状態保存、Grover fitには再利用学習pool読込、active RESULTには2モードの測定と検証まで含まれる。3群を同じ求解時間列として順位づけしない。GroverのFINAL_VALIDATIONは別のwallで、fitには含まれない。構成工程の境界・欠測数はPATH1_RUNTIME_SCOPE_INVENTORY.csvとevidence/RUNTIME_CODE_LOCATORS.txt。

古典初期構築時間は近似手法全体ではなく、古典近似actual_CPU_secondsも旧swap対照に合わせたCPU予算である。現行8設定との公平な総時間比較はHOLD。CPU時間をQPU時間へ換算しない。GPU/QPU/データ転送時間の未計測を0秒としない。

32,400秒はデポ帰庫制約（J+102n≤32,400）の値。Hplanへ代入しない。計算予算を変えた品質曲線をStep2で計測する場合、秒数の候補はpilotの計算資源見積として事前固定し、運用上の許容時間とは呼ばない。Hplan不明でも品質と工程記述は進められるが、運用採用可否の判定は保留する。
''')
md('PATH2_MODEL_ROLE_SPECIFICATION.md','''
# T08/T09の役割と会計境界

T08を主、T09をモデル構造依存性の補完とする。根拠：T8/SCENARIOS.json、T08.json、SOURCE_SNAPSHOT/src/kmd_quantitative/material_ev/stage2/battery.py、T9/model.py・analyze.py・RUN_CONFIG.json・PACK_20KWH_SENSITIVITY.csv、BR/integrate.pyと部材境界表。

T08では総cell容量Q=Egross/V [Ah]、正極活物質mp=Q/(q u)、正極乾燥塗工材Mp=mp/fp、負極活物質mn=NP·Q/qn、負極塗工材Mn=mn/fn。Mpack=Mp+Mn+Ncell·mother+Mpack,other+Madditional。cell質量=(Mp+Mn)/Ncell+mother。100s1pは設計仮定で、sum cell Ahとpack terminal Ahを混同しない。

gross=20,000 Whは質量設計、usable=18,000 Whは運転stock。qLP=171.875、qS=195.959596 Ah/kg、u=1、V=3.5 V、NP=1.1、qn=360 Ah/kg、fp=.75、fn=.98、100cells×.19kg=19kg、pack other15kg、additional0。0.19kgは両極塗工材以外のcell固定部材の包括項であり、内訳を実測した値ではない。15kgも仮定である。additionalは他に入っていない材料固有追加部材のみ。

qLPは121/.704、qSは194/.99の保持率基準からの逆算proxy（保存丸め値を用いる）。半電池の初回実測比容量やgraphite full-cell性能とは区別。保持率・ICEを追加uと重複適用しない。温度、保持率の基準、Sの質量正規化、活性化履歴、実電圧、power/thermal/life/safety/formation/Li inventoryは未確認。条件付き伝達を計算できても実材料の適格性はHOLD。

T08出力LP96.14565479871602kg、S90.6973573836391kgは簡略モデル計算値。車両質量は元車両から旧電池質量を除いた非pack質量に置換packを加え、走行質量に運転者55kgを加える。保存Cでは非pack走行部分1043.888888888889kgが共通。車体自重にpackを二重加算しない。

T09は部材ごとに幾何を伝播する。face area=active mass/active loading、coating volume=solid volume/(1−porosity)、thickness=coating volume/face area。両面foil面積はface area/2（margin/端部未測定）、Al密度2699・Cu8960 kg/m³。separator面積=max(正負face area)、乾燥separator質量=面積×面密度。電解液は両極coating空隙＋separator空隙＋extra volumeへwettable/saturationと密度を適用する。保存モデルでは正極混合固体密度4458、負極2200、液密度1300kg/m³、separator厚25μm・porosity.41、wettable=saturation=1。密度の材料間transferは仮定として残す。

既知subtotalは正負塗工材＋Al＋Cu＋乾燥separator＋liquid。活物質とcoatingを二重加算しない。未知はcasing/tabs/foil margins/pack structureなど。complete_pack_mass_kgは全183行NULL。T08固定19+15kgをT09 subtotalへ足して完成packを推定しない。T09_ROW_183は全面対向の条件FAILを保持し、物理的に成立した候補として用いない。

共通は20kWh/18kWh、3.5V、LP/S proxy、N/Pと負極基礎値。異なるのは活物質率・loading・area policy・porosity・部材密度transfer・部材固定/幾何連動の扱い。正確な共通条件は行ごとに辞書と照合する。T08/T09絶対質量を完成パック同士として直接比較しない。T09はT08の実証的validationではなく、同じ入力変化でもモデル構造でbが変わることを示す補完モデル。

成立境界はPATH2_BOUNDARY_DEFINITION_TABLE.csv、B015/B051はevidence/T09_BOUNDARY_PAIR_LINKAGE.csvで元行に接続する。q/u/V連続分析や49点は決定論的な探索座標で、49独立実験ではない。全軌跡の正DC質量感度の保証は、指定質量区間とCrr条件内に限る。
''')
md('CONTROLLED_DC_SCOPE_AUDIT.md','''
# Controlled-DC適用範囲

根拠：R/01_research_design/methodology/CONTROLLED_MASS_TO_DC_MODEL_FREEZE.json、R/src/kmd_quantitative/energy/frozen_sources/run_full_controlled_dc.py:68–83（公開alias controlled_dc.pyでhash保護）、P/run_c.py、C_TRAJECTORY_READBACK.csv、T8/MATERIAL_ENERGY.csv、各保存trajectory manifest。

Cの古典460速度入力はmatched_classical_trajectories_20261007/MATCHED_CLASSICAL_CANONICAL_TRAJECTORIESの保存CSV.gz。道路交通シミュレーション由来のモデル速度であり実車センサ計測ではない。別にR0/R1量子経路の参照があり、C全readbackは重複を除く465軌跡。古典460だけを主要固定軌跡cohortとし、R0/R1のmethod参照を新しい独立軌跡として水増ししない。Bの新460問題とjoinして配送経路改善のDC効果を推定しない。

区間jはdt=1s、右端速度vj、ds=vj dt、Δv²=vj²−vj−1²。

|項|機械仕事 [J]|質量置換|
|---|---|---|
|W1|m g Crr(v,p) ds|走行質量mを置換|
|W2|.5 ρ CdA v² ds|同じ軌跡・空力仮定では不変|
|W3|.5 m Δv²|走行質量mを置換|
|W4|.5×61 Δv²|回転等価質量61kg固定|

E_DC=Σmax(W1+W2+W3+W4,0)/(3600η) [Wh]、η=.90。成分個別を正値化して足す式ではない。回生なし、平坦路、補機・旋回損失除外、積載0kg、運転者55kg。g9.80665、ρ1.2041、CdA1.175。Crr=.005+(.01+.0095(v_kmh/100)²)/p、lower p4.5bar・upper p2.6bar。Crr2条件は確率的な95%区間ではない。

同一trajectory SHA・観測区間・CrrでLP/Sのpack質量のみを置換する。車両構成や経路選択は共通。正値maskがmassで変わるため、成分寄与はbaseline正値maskでのW1〜W4差＋branch correctionの恒等式で扱う。W2/W4が同値でもmask変化の補正を省かない。

約0.413%は100Σ(ELP−ES)/ΣELP。今回の端点再集計はevidence/C_ENDPOINT_RATIO_READBACK.csv。個別削減率の平均は約0.4093/0.4104%で別の推定対象。いずれもモデル計算値で、測定電力量や量子由来材料改善効果ではない。Bの量子解品質差に乗じない。

末端1秒等の未観測tailは未補完、未知電力量を0としない。C_TRAJECTORY_READBACK.csvのterminal_gap_sとmanifestを保持する。保存道路の地域的受入/実運用妥当性FAIL/HOLDも維持。同一軌跡質量感度のverificationは実道路/実車validationを意味しない。
''')
md('PATH1_STATISTICAL_ANALYSIS_PLAN.md','''
# Step 2：経路1統計仕様

実施状態：既存の記述統計・cluster感度は存在する。T/PATH1_INPUT_SEED_STATISTICS.csvは3680行、input×設定ごと10測定repのn/平均/sample SD(ddof1)/min/max。T/scripts/analyze.pyで定数列SDを0とする実装を確認し、今回は元36,800行から再集計して照合した。P/B_INPUT_SEED_AGGREGATES.csvは初期差、gap、一致率、可行率をinput内平均した別表。P/statistics_tables.pyはinput→規模内等重み、25需要group bootstrap10,000回seed20261102のpercentile95%を補助感度として実行。P/CLUSTER_SENSITIVITY_INTERVALS.csv等は実在する。現行古典近似JCとの差を主にした表や、全指標の中央値/IQRは未完了。既存値の符号JQ−JinitialをΔJと誤認しない。

観測構造：group_id（25需要群）→parent_id（26親、同一groupに複数親あり）→物理input（460、規模と条件の派生）→設定8（対応あり）→fit1→measurement rep10。repには独立PCG64 streamがあるが学習条件は同じ。設定・規模を独立な無作為標本とみなさず、groupの独立性も確率標本によって立証されていない。

主推定対象は「保存された有限入力cohortについて、設定aと事前指定JCの、10測定反復にわたる平均品質差を各入力同じ重みで平均した値」。規模s別θsa=(1/Ns)Σi∈s[(1/10)Σr(JC,i−JQ,iar)]。全体は460入力等重みを補助として示し、6規模等重みの値と混同しない。JC2法は別々に出し、主はgreedy adjacent。学習予算非統制という限定を表題に付す。

実行順序（Step 2、今回は未実行）：

1. provenance/hashを固定し、(input SHA,設定,rep)PK、460×8×10、初期/近似/厳密join一対一を検査。古典近似元分数を確認し、可行性・対応が未確認の対照は差をHOLD。
2. metric仕様に沿いexact FractionでΔJを生成。JQ/Jinitial/JC/J*、exact有無、fit ID、group/parent、欠測理由、測定seed entropyを保持。
3. 各input×設定でmean/median/SD/min/max/Q25/Q75/IQR、改善/可行/最適一致を算定。SDはddof1、quantileは線形補間。mean SDとinput間SDは別列とする。
4. 規模×設定×対照ごとにinput平均差の平均・中央値・入力間SD/IQR、改善確率のinput平均と「10rep中1回以上改善したinput率」を区別して出力。全分布と全8設定を表示し有利な設定だけ選ばない。
5. gap/一致率はexact407（規模78/78/78/78/57/38）に限定。exact有無の初期目的/規模/観測特徴を比較する欠測監査を出す。53の値は代入しない。complete-caseのgapを全460へ一般化しない。
6. 設定間の比較は同じinputにおける差。異なる設定のrep番号を共通乱数によるpaired seedと自動認定しない。input内rep平均の対応で比較する。
7. fit時間は一fit一行、resource scope別の分布として示す。10rep行へ複写されたfit時間を10倍数えない。

不確実性区間：有限cohortの記述自体に標本抽出CIを強制しない。補助として二種類だけ事前宣言する。(a)固定input/fitでの測定乱数感度：input内で10repを復元抽出、設定間streamは独立に再標本化し、10,000回seed20261104、percentile95%。全8192shotsを独立最終解として数えない。10repでは尾の精度が限られると注記。(b)仮想的に同様の需要group母集団を想定したcluster感度：25 groupを25個復元抽出、同groupの全parent/input/設定/repを一緒に保持、input内平均後θを再計算、同じ再標本化重みを全対応contrastに使う。10,000回seed20261102で既存との再現可能性を保持。group交換可能性と群間独立を仮定した仮説的感度であり実配送母集団の校正済みCIではない。群が欠ける規模やexact subsetでは有効cluster数とundefined回数を報告。rep-onlyとgroup区間を無説明に合算しない。

学習乱数の区間は全入力の複数学習がないためHOLD。中央値・SD・IQRを8設定混合で一つに潰さない。検定/p値は必須とせず、量子優位の有意性や改善量を研究の合否にしない。分布・境界・負/ゼロ結果を同じ仕様で報告する。

予定出力：INPUT_CONFIG_METRICS、PAIRED_CLASSICAL_APPROX_DIFFERENCES、SCALE_CONFIG_DISTRIBUTIONS、REFERENCE_MISSINGNESS、RUNTIME_BY_SCOPE、OPTIONAL_MEASUREMENT_SENSITIVITY、OPTIONAL_GROUP_SENSITIVITY。いずれも新Step2 trialに保存しP/Tを上書きしない。
''')
md('PATH2_UNCERTAINTY_ANALYSIS_PLAN.md','''
# Step 2：経路2の感度・不確実性

主対象は決定論的条件付き伝達。T08主、T09構造補完、Controlled-DC固定軌跡。モデル内で入力を動かした49点は49独立実験ではない。未知部材に確率分布を与えず、境界δ=bとその両側を決定論的に評価する。

|区別|推定/表示対象|Step2仕様|
|---|---|---|
|軌跡間分布|固定パラメータ下の460軌跡におけるΔE、個別率|trajectory SHA単位でLP/Sと2Crrを対応保持。規模別mean/median/SD/IQR/min/max、Σ差/Σ基準と平均個別率を併記。R0/R1 method参照は別表|
|パラメータ感度|q、u、V、loading、porosity等による決定論的曲面|保存範囲内の連続感度と零境界。既存q49点とu49点、各固定条件を再利用。二変数u×V等は新計算候補、外挿をしない|
|未知部材境界|ΔM=b−δの成立/消失/逆転|T08 additionalとT09未知部材差の内訳を固定。δ=b−1kg,b,b+1kg等は境界を可視化するdiagnostic（成功率目標ではない）。B015/B051を混ぜない|
|構造的不確実性|T08固定部材とT09面積連動部材の違い|共通Egross/V/u/q/NP/qneg/fractions等を一致させ、会計境界の揃う成分差だけ比較。完成パック差や実証validationとしない|
|統計的推定不確実性|同様の需要群へ一般化する仮想感度、あるいは実測入力の誤差|主解析は有限cohort記述。希望する場合のみ25group bootstrap、全軌跡のLP/S/Crr/parameter gridを一緒に再標本化。実測誤差分布の証拠がないq/u/δにはCIを付けない|

既存実施：P/C_T08_PAIRED_DIFFERENCES.csv、C_CONDITIONAL_MASS_DC_SUMMARY.csv、CLUSTER_SENSITIVITY_INTERVALS.csv、T/PATH2_SENSITIVITY_RESULTS.csv・SUMMARY.csv、UTILIZATION_CONTINUOUS.csv、BOUNDARY_RESULTS.csv、OPERATION_INTERACTIONS.csvが存在する。Tのq感度は460×2Crr×49=45,080行。これらの行数は独立標本数ではなく評価格子×対応入力の数。

Step2ではhash/PKとpair key(trajectory SHA,Crr,scenario)を検証し、端点・identical controlのΔ=0を確認。質量差→DC符号の成立は保存mass区間内の正値化branchを含む感度で評価する。ΔM=0なら同一軌跡・同一全条件でΔE=0、ΔM>0だけから全ての運行条件で厳密ΔE>0とは外挿しない。既存正傾き確認は保存区間・Crr条件内の結果。

走行条件別は距離/停止再発進/速度/加速指標を保存速度から算出し、規模/parent/groupと併記。共通軌跡の条件差として分布を記述し、単相関から運転条件の因果効果を断定しない。Crr2値を同じtrajectoryの反復測定として独立化しない。未観測tail、回生/補機/勾配、未知BOM、密度transfer、材料の実現性、道路受入を別々のHOLDとして残す。

任意0.25%等は既存例示の出典としてのみ保存し、新しい成功基準・必要性能へ置き換えない。統計的有意差を経路2成立の要件にしない。
''')
md('STEP1_DECISION_RECORD.md','''
# 決定記録

位置付け：独立Step1 trial。研究者が確定した方針を変えず、正式採用・原稿統合を実施しない。

既定方針を保持：二経路／定時配達率を主指標から除外／経路1は解品質と計算時間／経路2は材料からDCへの条件付き伝達／T08主・T09補完／ゼロ効果境界／任意削減率を成功基準にしない／実道路と量子材料改善を実証しない／未接続は考察後段／EV配送は社会技術システムの一事例。

今回trial内で固定した評価仕様：

- ΔJ=古典近似JC−JQ。主JCをgreedy adjacent、random swapを別対照、初期解を補助、J*を共通参照に分離。既存初期差は符号反転して名称も区別。
- 保存十進数由来Fractionの目的比較はεJ=0、float再計算の1e−7sは整合性検査。solver/シミュレータ精度と同等判定を混ぜない。
- B現460×8×10は測定rep。R4=100、厳密407/未証明53。A旧時間窓・C旧軌跡と混合しない。
- 時間は工程別scope。τtotal≤Hplan、Hplan数値HOLD、帰庫32,400秒を代用しない。QPU速度/compiled/物理qubitはHOLD。
- T08は簡略質量の条件付き主モデル、T09は既知幾何部材と未知部材の構造感度。完成パック比較は行わない。
- ΔM=b−δのbとδをモデル別に定義。q/u/V・追加部材のゼロ境界、ΔEの総和比と個別率平均を区別。
- 有限cohort対応記述を主、測定乱数・需要groupの補助感度を分離。学習seedの反復が不足する範囲はHOLD。

採用未決定の事項：正式RQ原本の文面、正式原稿の版選定、現行8設定の公平なCPU予算、実運用Hplan、未証明53の求解追加、完成BOM、実車・材料接続。これらはHOLDのままでもStep1の作業完了を妨げない。
''')
rows=[]
for task,status,outputs,hold in [('1-1','CONDITIONAL','RQ_INDICATOR_ALIGNMENT.md;POLICY_CONSISTENCY_AUDIT.md','正式RQ/原稿への採用未実施'),('1-2','CONDITIONAL','PATH1_COMPARISON_BASELINES.md;PATH1_METRIC_SPECIFICATION.md;PATH1_REFERENCE_COVERAGE.csv','現行8設定の時間予算統制;厳密53'),('1-3','CONDITIONAL','PATH1_RUNTIME_SCOPE_INVENTORY.csv;PATH1_RESOURCE_SCOPE.md;PATH1_TIME_CONDITION_SPEC.md','工程未分離;Hplan;compiled/QPU'),('1-4','CONDITIONAL','PATH2_MODEL_ROLE_SPECIFICATION.md;PATH2_INPUT_PARAMETER_DICTIONARY.csv;PATH2_BOUNDARY_DEFINITION_TABLE.csv;CONTROLLED_DC_SCOPE_AUDIT.md','T09完成pack;材料/実車/道路妥当性'),('1-5','PASS','PATH1_STATISTICAL_ANALYSIS_PLAN.md;PATH2_UNCERTAINTY_ANALYSIS_PLAN.md;STEP2_ADDITIONAL_EXPERIMENT_CANDIDATES.csv','Step2未実行;学習seed不足')]:rows.append({'task':task,'work_status':'COMPLETE','scientific_status':status,'deliverables':outputs,'remaining_hold':hold})
table('STEP1_COMPLETION_MATRIX.csv',rows)
# Candidates with explicit pilot gates instead of unsupported whole-cohort seed counts.
candidates=[
 dict(priority=1,id='E1',candidate='探索支持とアルゴリズムを分離する統制比較',question='RQ1:支持・初期状態・探索予算と量子状態操作の効果を分離できるか',insufficiency='mirror/Grover/activeで支持・初期状態・予算が同時に異なる;古典近似CPU合わせは旧swap実験',inputs='元B NPZ460/初期経路/凍結コード/hash;共通支持を明示できる小規模と既存代表点',controls='同一input/目的/制約/初期状態/支持;最適化評価数・shots・時間をそれぞれ別軸で統制;同支持chainDP診断',metrics='DeltaJ,relative improvement,acquisition,feasibility,gap where exact;time by scope',rep_seed_basis='pilotは既存R3/R4/R5代表各3入力＋R0/R1/R2の固定先頭入力;測定10rep×8192は既存再現基準;学習3seedは探索的分散診断に限定。全量回数はpilot後、目標MC誤差と資源上限を事前固定',resources='CPU MPS/DP;大規模Grover MCはpilot資源見積後に段階判定;QPU不要',conclusion_impact='支持制限由来のゼロ改善と手法由来の差を分離;改善なしも有効な条件結果',gate='Step2で事前プロトコル・input選択・予算・精度gate固定後に実行'),
 dict(priority=2,id='E3',candidate='古典/量子求解時間の再計測',question='RQ1:共通工程と計算予算で品質とelapsed時間を比較できるか',insufficiency='fit scopeが群間で異なる;初期構築と近似完成対照が別;転送/後処理欠測',inputs='E1共通入力/コード/実行環境台帳;タイマ付き隔離コピー',controls='同一CPU/affinity/threads/負荷条件;cold/warm別;キャッシュ再利用費用;end-to-endと内訳の非重複;実行順を交互化',metrics='tau_total wall,process CPU,peak RSS,DeltaJ,time-quality curves',rep_seed_basis='各固定入力・方式でpilot3回の実行時間を計測しCVとtimer分解能を確認;初回coldとwarmを別記。追加回数はpilot精度基準を事前宣言して決定。測定seedはE1と区別',resources='CPU;最初は小規模・既存代表点のみ;全量資源未確定',conclusion_impact='CPU工程比較を可能にする;Hplan根拠がなければ運用採用判定はなおHOLD',gate='E1と同時設計可;Hplan数値を勝手に設定しない'),
 dict(priority=3,id='E2',candidate='未証明53入力の厳密参照改善',question='RQ1:大規模gapと最適一致率の参照欠測を減らせるか',insufficiency='R4 21/R5 32は証明未成立;欠測を最適値で補えない',inputs='PATH1_REFERENCE_COVERAGEの53証明/NPZ/保存witness/lower bound/solver hash',controls='同一有向OD・全顧客・制約;証明とincumbentを区別;数値bound-witness整合・独立証明検査;strict Fraction',metrics='proved optimal count,gap only certified,wall/CPU,RSS,termination',rep_seed_basis='決定論的証明求解はseed反復不要。まずtermination種別ごとの固定1件を診断、証明不整合の原因を確認。solverseedを使う場合1固定値と記録、性能分散実験とはしない',resources='CPU exact solver/RAM;53件一括投入せずpilotで秒/メモリ上限を固定',conclusion_impact='gap coverage拡大;DeltaJは厳密値なしでも定義できるため最優先ではない',gate='bound-witness不一致を解決してから追加求解;証明なし値は引き続きNULL'),
 dict(priority=4,id='E4',candidate='T08/T09共通条件の追加感度',question='RQ2:質量・DC境界が固定部材/幾何仮定へどう依存するか',insufficiency='既存B015/B051は特定のarea/loading条件;絶対質量比較は会計境界不一致',inputs='SCENARIOS/RUN_CONFIG/183行/部材辞書/保存460軌跡',controls='Egross/V/q/u/NP/qneg/fractionsを揃える;幾何policyは別軸;既知部材境界を一致;未知はdelta軸',metrics='component delta,b-delta,u/V zero boundaries,DeltaE,total ratio and mean individual ratio',rep_seed_basis='決定論的gridなのでseed反復不要。既存49点範囲を基本とし境界付近を適応分割、収束許容幅をコード精度から事前固定。点数を標本数としない',resources='軽量CPU質量算術/保存軌跡kernel;新規SUMO不要',conclusion_impact='モデル構造に頑健な条件と依存する条件を区別;実証validationへは昇格しない',gate='T09_ROW_183の物理FAILを分離;完成packは求めない'),
 dict(priority=5,id='E5',candidate='保存軌跡の走行条件別分析',question='RQ2/RQI:同一質量差のDC効果が軌跡特徴でどう変わるか',insufficiency='既存相関は距離・再発進の依存とparent/scale交絡を分離しない',inputs='旧C460trajectory SHA/速度/parent/group/2Crr/LP-S対応',controls='同一trajectory内mass差/Crr対応;走行観測窓共通;Bへjoin禁止;分類閾値は結果を見る前に固定',metrics='DeltaE,individual ratio,total ratio,W1/W3/branch;distance/restarts/speed bins',rep_seed_basis='全保存460で有限cohort記述;乱数seed不要;補助group感度のみ10000resample seed20261102;2Crrや49点を独立nとしない',resources='軽量CPU readback;SUMO/車両実験不要',conclusion_impact='効果伝達の条件差を説明;運転操作の因果効果や地域一般性は主張不可',gate='既存OPERATION_INTERACTIONS再利用優先;新規軌跡生成しない')]
table('STEP2_ADDITIONAL_EXPERIMENT_CANDIDATES.csv',candidates)
md('HOLD_REGISTER.md','''
# HOLD台帳

|ID|未解決証拠|影響・解除条件|Step2の進行|
|---|---|---|---|
|H01|正式RQ0/1/2/I原本と正式採用原稿版|研究者の採用・版選定までtrial表現を維持|trial統計設計は進められる|
|H02|現行8設定と古典近似の予算・支持統制|E1/E3の共通入力/工程/予算記録|既存品質記述は条件付き可|
|H03|厳密最適値53未証明|証明JSON termination別の原因修正＋独立検証|非gap指標は全460可、gap407限定|
|H04|総計画時間/Hplan根拠|共通計測と運用起点/締切の証拠|時間優位・運用可否は断定不可|
|H05|compiled/実機/物理資源|回路/コンパイラ/接続/noise/誤り訂正の明示|保存CPU資源記述可|
|H06|全入力の複数学習seed|事前固定した学習反復追加|10測定repを学習分散に代用しない|
|H07|raw-shot invalid countの一部未保存|保存samplesからの再構成/新記録|best plan可行率のみ全件可|
|H08|T08 proxy→実full-cell、V、形成、密度、寿命/安全|独立した実材料・セルの証拠|モデル感度のみ可|
|H09|T09未知部材・完成pack|BOM等の実測/設計根拠|b−delta境界のみ、残差補完不可|
|H10|量子計算による実材料性能改善|材料計算から実材料へ接続する独立証拠|考察後段の未接続|
|H11|B経路→実走行/DC・地域道路妥当性|受入済みnetwork/軌跡/運用比較の証拠|BとCを別に扱う|
|H12|保存trajectory末端未観測と回生/補機/勾配等|当該計測/別モデルの正当化|観測窓・凍結境界内のみ|

保持する既存FAIL：道路N0/N1の地域受入、T09_ROW_183全面対向条件、現方針を旧README/原稿へそのまま適用した際の不整合。FAILを削除せず、今回の限定モデル算術のPASSと別に管理する。
''')
md('STEP2_HANDOFF.md','''
# Step 2引継ぎ仕様（未実行）

このファイルは開始可能な具体仕様であり実行指示の自動発火ではない。今回の実行範囲はStep1まで。

開始時に新しい一意のStep2 trialを作り、SOURCE_PROVENANCE.csvとevidence/START.jsonの版を再検証する。元参照の旧絶対パスはevidence/PATH_RELOCATION_MAP.csvから実在ファイルを解決しhash一致を必須とする。外部preservationが利用できない環境では元NPZ/測定/コードの取得までHOLD、CSVだけで再現完了としない。

経路1の準備：PATH1_REFERENCE_COVERAGE.csvの460行にinput/parent/group/scale/n、近似2法、初期、厳密証明をjoinする。主JC=ITERATED_GREEDY_ADJACENT_SWAP、第二対照=DEPHASED_RANDOM_SWAP。元古典近似分数はB_AUXILIARY_CLASSICAL_IMPROVEMENTS/上流MATCHED_COMPARISONにあり、元rawのinputと同じ目的・制約・初期化を確認する。予算非統制の限定を維持し、時間比較を付けない。measurement rep=10の3680fit階層を固定し、品質はraw sampled-best、初期とのminで置換しない。

PATH1_STATISTICAL_ANALYSIS_PLAN.mdの手順1〜7とPATH1_METRIC_SPECIFICATION.mdを実装する。分布・中央値/IQR・二対照対応差・exact欠測層を追加し、旧初期差と主ΔJを別列にする。数式テストは異なる目的/誤join/未知値のゼロ補完を検出する最小fixtureと、元算術の標本照合で行う。既存集計を再現したことと新JC統計を完了したことを分けて記録する。

経路2の準備：T08 scenario、T09 row/pair、trajectory SHAを固定。PATH2_INPUT_PARAMETER_DICTIONARY.csvは値/単位/根拠を保存している。境界はPATH2_BOUNDARY_DEFINITION_TABLE.csv、PAIR_LINKAGEでbとdeltaを確認。T08主の49点・u感度とCrr対応を再利用し、PATH2_UNCERTAINTY_ANALYSIS_PLAN.mdの分布/パラメータ/未知BOM/統計感度を別表にする。C古典460とB新460の同数を対応の証拠にしない。

追加実験はSTEP2_ADDITIONAL_EXPERIMENT_CANDIDATES.csvの優先1(E1支持統制)、2(E3時間)、3(E2厳密)、4(E4共通感度)、5(E5軌跡条件)。軽量な既存再集計はこの順位を待たず実施できる。新規重計算はpilot→資源/精度/回数の事前固定→段階実行とし、全量投入を先に約束しない。pilotの3seed/3回は探索的診断で、妥当な最終標本数が確定したという意味ではない。

実験前に固定する項目：対象inputリスト・hash、目的/制約、古典方式、支持/初期状態、学習評価数とshots、学習/測定seedの独立stream、cold/warm工程境界、CPU affinity/threadsとメモリ上限、数値精度gate、停止条件、欠測・failを記録するschema。改善を採否gateにしない。Hplanや実QPU資源の未確認値は作らない。

進行条件：本Step1設計を利用するという研究者の採用判断は未実施。Step2を別途実施する際は出力範囲と新規計算の段階を明示する。H01〜H12を全解除する必要はないが、各出力の主張範囲に関わるHOLDを保持する。新規CPU統制比較なしでも条件付き品質統計は開始可能。Hplanなしでは運用時間合格、53未証明では全460gap、未知BOMでは完成pack効果、実機なしではQPU優位を判定しない。
''')
md('README.md','''
# KMD修士研究 Step 1 評価設計・既存結果確定 trial

目的：量子技術がEV配送へ寄与する条件を検討するため、保存実験・実装・既存統計・原稿を照合し、Step2の評価仕様を具体化する。独立trialであり正式採用・統合は未実施。元データ・コード・既存trial・原稿を変更しない。commit/push/公開なし、新規QAOA/SUMO/厳密求解なし、Step2の統計計算・追加実験を開始していない。

読取元はSOURCE_MAP.mdとSOURCE_PROVENANCE.csv。現行Bの元NPZ/測定JSON/証明、旧C保存速度、T08/T09モデル、11月2日全件監査、11月4日統合trial、正式側DOCX候補と独立THESIS_TRIALを区別した。上流の一部はリポジトリ外のpreservationに実在するため、このtrialだけを他環境へ移しても全再検証できない。

|課題|成果物|
|---|---|
|1-1|RQ_INDICATOR_ALIGNMENT.md / POLICY_CONSISTENCY_AUDIT.md|
|1-2|PATH1_COMPARISON_BASELINES.md / PATH1_METRIC_SPECIFICATION.md / PATH1_REFERENCE_COVERAGE.csv|
|1-3|PATH1_RUNTIME_SCOPE_INVENTORY.csv / PATH1_RESOURCE_SCOPE.md / PATH1_TIME_CONDITION_SPEC.md|
|1-4|PATH2_MODEL_ROLE_SPECIFICATION.md / PATH2_INPUT_PARAMETER_DICTIONARY.csv / PATH2_BOUNDARY_DEFINITION_TABLE.csv / CONTROLLED_DC_SCOPE_AUDIT.md|
|1-5|PATH1_STATISTICAL_ANALYSIS_PLAN.md / PATH2_UNCERTAINTY_ANALYSIS_PLAN.md / STEP2_ADDITIONAL_EXPERIMENT_CANDIDATES.csv|
|横断|STEP1_DECISION_RECORD.md / STEP1_COMPLETION_MATRIX.csv / STEP2_HANDOFF.md / STEP1_FINAL_AUDIT.md / HOLD_REGISTER.md|
|根拠・保全|SOURCE_MAP.md / SOURCE_PROVENANCE.csv / evidence/ / OUTPUT_SHA256_MANIFEST.csv|
|監査コード|scripts/audit_sources.py / scripts/supplement_audit.py / scripts/write_design.py / scripts/finalize.py|

まずSTEP1_FINAL_AUDIT.mdで判定と限界、STEP2_HANDOFF.mdで次工程、各仕様書で定義を確認する。evidence/NUMERICAL_CHECKS.csvとSUPPLEMENT_CHECKS.csvは今回独立に検査した範囲であり、既存trialの検査件数を今回実行した数として引用しない。

再検証は監査スクリプトを新しいtrialへコピーして使い、元trialを再実行で上書きしない。scripts内の出力先は__file__から決まるため、コピー先の一意ディレクトリでのみ実行する。write_design.pyは本Step1の編集内容を出力する専用スクリプトであり、将来の新事実を自動反映するものではない。
''')
print('design documents written',O)
