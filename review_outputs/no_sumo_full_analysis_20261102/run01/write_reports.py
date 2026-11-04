"""Render final study tables with explicit conditional/untested boundaries."""
from common import *
def doc(n,s):(O/n).write_text(s.strip()+'\n')
def main():
 a=js(O/'A_FULL_RUN.json');b=js(O/'B_FULL_RUN.json');c=js(O/'C_FULL_RUN.json');s=js(O/'STATISTICS_RUN.json');v=js(O/'VERIFY_FULL_RUN.json');sv=js(O/'STATISTICS_VERIFICATION.json');gate=js(O/'BATCH_GATE.json');base=js(O/'STAGE0_RUN.json');supp=js(O/'SUPPLEMENT_RUN.json');asum=rows(O/'A_SUMMARY_BY_CONDITION.csv');bsum=rows(O/'B_SUMMARY_BY_SCALE_AND_METHOD.csv');csum=rows(O/'C_CONDITIONAL_MASS_DC_SUMMARY.csv');policy=rows(O/'A_POLICY_DECISIONS_2808.csv');mech=rows(O/'A_MECHANISM_COMPARISON.csv');bp=rows(O/'B_PLAN_REFERENCES_36800.csv');fits=rows(O/'B_RESOURCES_PER_FIT.csv');ci=rows(O/'CLUSTER_SENSITIVITY_INTERVALS.csv');rawa=rows(O/'A_PAIRED_PER_PROBLEM.csv');t9=rows(O/'C_T09_COMPONENTS_183.csv');masses=rows(O/'C_COMPONENT_MASS_BRIDGE.csv')
 def ref(p):
  p=use(p);return f'`{p}` — SHA256 `{SRC[str(p)]["sha256"]}`'
 # 00 remains the pre-result document written by stage0; do not rewrite it.
 doc('01_INPUT_AND_IMPLEMENTATION_AUDIT.md',f'''
# 入力・実装監査

事前固定 `FROZEN_PROTOCOL.json` と旧4レビューを継承。旧成果{base['prior_artifacts_pinned']}ファイルをmanifest SHAで照合した。既存OD、計画、政策、seed、FREEZEの変更なし。今回の依頼による全件算術実行は、旧タスク固有の全件禁止表記を歴史記録として保持したうえで実行した。

## 元データと生成経路

|対象|実入力・実装|出力・行数|
|---|---|---|
|A|旧78NPZ、古典/QAOA原JSON、D10/D11 operations_2808。新run_a.py|政策2,808、古典対照2,808、成功64の機構4arm9,216、task59,328|
|B|現行R0…R5 460NPZ、3family raw JSON・8設定、SeedSequence対応台帳。新run_b.py|36,800参照、3680 fit資源、407/53の460参照台帳|
|C T08|SCENARIOS、MATERIAL_ENERGY、旧trajectory manifestsとgzip速度。凍結evaluate|4,464全行、744 dataset/method軌跡参照、465固有速度ファイル|
|C T09|PACK_20KWH_SENSITIVITY、T09_MASS_BOUNDARIES|183行、完成mass NULL183、対向FAIL1|
|C bridge|DC_MASS_RESPONSE、固定旧460速度|25,760全行、1200/1400kgの既存感度probe|

主要起点：

- {ref(U/'review_outputs/cpx01_d11_validation_20261017/operations_2808.csv')}
- {ref(P1/'B_PLAN_REFERENCES.csv')}
- {ref(S/'mirror_family/MANIFEST.json')}
- {ref(R/'01_research_design/methodology/CONTROLLED_MASS_TO_DC_MODEL_FREEZE.json')}
- {ref(T8/'SCENARIOS.json')}
- {ref(T9/'PACK_20KWH_SENSITIVITY.csv')}
- {ref(BR/'DC_MASS_RESPONSE.csv')}

`SOURCE_AND_OUTPUT_HASHES.csv` は実パス・role・SHA・所在を保存。外部Uの未追跡コピーとB/Lの保全資料は公開Git収録扱いにしない。`INPUT_LEDGER.csv` と `PARENT_GROUP_MAPPING.csv` は78/460物理入力と26親→25元需要groupを保持。原入力を再生成していない。

## 指標・単位・欠測

Aは秒、需要PE、率fraction、差ppを別列。完了期限due_start+102、デポdue32400を独立に扱う。Bのobjective_fractionは原有理数、OD_time_sはNPZ脚和。両者のserialization照合許容1e-7秒を、最適値一致の許容には使わない。最適値一致は原有理数で厳密比較する。距離はOD mでnative走行距離ではない。

Bの厳密参照407、未確定53は前回と一致。53入力×8×10=4,240参照はgap/最適一致nullで保持する。全460で評価する取得・初期解差等と分母を分けた。hardware qubit・compiled depth/gates、未保存CPU/RSSは推定で埋めずreasonを付す。原CSVのgap未保存と参照値不存在も区別する。

Cはkg・Wh・%と原設計条件単位を保持。主材料比較のgross20kWh／usable18kWh、T08とT09会計差、Crr両境界、unknown BOMを継承。Cのinput_sha256は速度hashまたは材料CSVのhash、集計行は入力ledger／元結果表hashである。`input_sha_scope` を見て物理入力SHAと区別する。

全CSVの実row数、列、NULL、PKは `DATA_SCHEMA_AUDIT.json`。task PKはscope/condition/problem/arm/task、Bはproblem/config/measurement_rep。親・rep・条件を独立問題として増やさない。保存結果・モデル派生・実世界未検証を別状態で記録する。

## 独立実装

primary AはDecimal逐次、独立AはFraction max-plus。primary Bはraw有理数＋NPZ脚和、独立Bはfsumの別手順と参照分母。primary Cは元の凍結kernelを呼び出し、独立Cはmass線形係数を使った別vector式と部材Fraction式。primary関数を検証コードからimportしていない。主出力14CSVは全件再実行してbyte SHA一致を確認した。
''')
 batchrows=[]
 for name in ['A','B','C']:
  rr=js(O/(name+'_BATCH_RUN.json'));mm=rr['metrics'];batchrows.append(f"|{name}|{rr.get('policy_rows',rr.get('references',rr.get('T08_rows')))}|{mm['wall_s']:.6f}|{mm['max_RSS_bytes']:,}|{rr['failures']}|{gate['projection'][name]['linear_row_projection_s']:.3f}|")
 doc('02_BATCH_AND_RESOURCE_VALIDATION.md',f'''
# 少数batch・資源の受入

少数batchの独立検算 **{gate['batch_independent_checks']:,}項目、不一致0**。これを確認してから全件に展開した。入力・出力SHAは `BATCH_ARTIFACT_HASHES.json`、科学コードSHAは `BATCH_GATE.json`、試行元は各 `*_BATCH_SOURCES.json`。原入力は変更なし。

Aは同順・異順・未取得切替・正出発遅延・早着待機を含む4政策、成功例の機構arm12、計80task。期限等号／超過は元実入力に基づく2境界fixtureで、D10全件母集団へ混ぜていない。BはR0…R5と参照欠測を含む7入力560参照（exactあり5／なし2）。Cは4固有速度、T08 48行、T09 5行（FAIL含む）、bridge224行を再計算。

|系列|主row数（他のrow単位は上記）|batch wall秒|最大RSS bytes|計算失敗|全件wallの事前線形見積秒|
|---|---:|---:|---:|---:|---:|
{chr(10).join(batchrows)}

事前合計見積{gate['projected_total_wall_s']:.3f}秒、RSS screen{gate['screen_RSS_bytes']:,}bytesは、wall1,800秒・process4GiBの上限内。row比例のI/O込み概算で、全件実測ではない。モデル改善は受入基準に使わない。Cの既存FAILは計算失敗と別で保持する。

主全件実測はA {a['metrics']['wall_s']:.3f}秒／{a['metrics']['max_RSS_bytes']:,}bytes、B {b['metrics']['wall_s']:.3f}秒／{b['metrics']['max_RSS_bytes']:,}bytes、C {c['metrics']['wall_s']:.3f}秒／{c['metrics']['max_RSS_bytes']:,}bytes。並行実行を含むprocess別wallで、合計を全作業の経過時間としない。CPUはprocess累積、wallはmain内timer、RSSはprocess peak。科学solverの保存CPU時間とは別である。

全件A/B/Cの独立照合{v['checks']:,}項目、統計照合{sv['checks']:,}項目、主出力14CSVの再実行hash一致。原道路受入や実車性能のPASSではなく、固定モデル算術のPASSである。
''')
 at='\n'.join(f"|{x['condition_id']}|{x['L_s']}|{x['T_Q_s']}|{x['B_s']}|{x['quantum_adopted']}|{x['positive_departure_inputs']}|{float(x['PE_on_time_percent']):.1f}|{float(x['delta_mean_completion_s']):.6f}|{float(x['delta_return_s']):.6f}|" for x in asum)
 routepairs=[x for x in rawa if x['series_id']=='A_MECHANISM' and x['effect']=='ROUTE_QC_CC'];departpairs=[x for x in rawa if x['series_id']=='A_MECHANISM' and x['effect']=='DEPARTURE_CQ_CC'];early=sum(x['availability_feasible']=='False' for x in mech);doc('03_SERIES_A_FULL_RESULTS.md',f'''
# A：固定OD全件結果

判定：算術PASS、解釈CONDITIONAL。78×36=2,808政策、対応する古典のみ2,808、取得成功64×36×4=9,216機構armを保存。**全36条件で、政策・古典対照・4armのPE加重／件数定時率は100%、差0pp**。未完了・判定不能0、帰庫期限超過0。これらは固定ODと中断なしサービスのモデル結果である。

## A2：全78の政策結果

QAOA取得64／未取得14（失敗率17.948718%）、26親・25需要群。未取得を除かず古典切替に含めた。全判断で量子採用1,344（47.863248%）、古典切替1,464（52.136752%）。取得失敗に対応する判断504と、取得済みで期限に間に合わない判断960を区別する。FAILURE_KNOWN294／DEADLINE_NO_AVAILABLE_QUANTUM1170という切替理由は、取得状態とは別のイベント分類である。

取得済みかつT_Q≤L−Bで量子採用する21条件では64/78をQ採用、残る15条件では0。出発0秒1,872判断、120秒192、600秒468、720秒276。正遅延936判断。訪問順が古典と異なる政策入力105。定時率は同じでも、政策対照との配送先平均完了時刻差は個別問題で−962.280893〜+540秒、帰庫差−117.525696〜+39.167567秒となる。

|条件|L秒|T_Q秒|B秒|Q採用数|正遅延数|PE定時%|問題平均完了差秒|問題平均帰庫差秒|
|---|---:|---:|---:|---:|---:|---:|---:|---:|
{at}

平均差は政策Q優先−古典のみで、正は遅い。全36条件を独立標本として平均した因果効果とは呼ばない。task別arrival、wait、start、complete、due_start、D03 deadline、PE、statusと帰庫を保存した。`A_DELIVERY_COMPLETION_BY_STOP.csv` の59,328行は政策／対照／機構すべてを含み、政策のみなら11,232行である。

## A1：成功64の機構比較

64中59は古典と同順、5は異順。QC−CCはrouteだけ、CQ−CCはdepartureだけ、QQ−CCは組合せ、QQ−QC−CQ+CCは交互作用として別表に保存した。同順・同出発では一致する。

route変更による平均完了差は問題別−962.280893〜+5.858631秒、帰庫差−117.525696〜+39.167567秒。departureのみでは平均完了差0〜540秒、帰庫差は全件0。組合せの完了差は−962.280893〜+540秒。今回の保存条件では平均完了／帰庫の交互作用は0であった。4条件の定時率差はいずれも0pp。

機構armのうち{early:,}行は、指定した出発までに仮想取得＋dispatchを満たせない。これはQ routeを強制する反事実的機構比較であり、実際に採用・実行できた政策結果ではない。`availability_feasible` と `departure_before_plan_available` を分けて保存し、政策表に混ぜていない。

## 影響消失条件

サービスはs=max(arrival,ready)、complete=s+102。出発遅延は早着待機で一部または全部吸収され、終了まで伝達した場合だけ完了差となる。全政策の最小deadline余裕は **{s['A_min_slack_s']:.6f}秒**。保存route集合の最初の期限超過が起きる出発境界の最小値は **{s['A_first_late_boundary_min_s']:.6f}秒**で、実政策の最大出発720秒より大きい。期限を広げたり変更した結果ではない。

同じOD・routeでは出発を遅らせても完了が早まらないこと、サービス102秒が一度だけ加わることを検査した。定時率0ppは有限モデル母集団で確認した値であって、量子と古典の一般的同等性、実地域の遅延吸収、実荷物引渡しの実証ではない。動的交通、信号、停車失敗、Aの走行DCは未評価。
''')
 bt='\n'.join(f"|{x['config_id']}|{float(x['mean_delta_objective_s']):.6f}|{float(x['mean_global_gap_percent']):.6f}|{float(x['optimal_match_percent']):.6f}|{float(x['improve_percent']):.6f}|{float(x['mean_fit_wall_s']):.6f}|" for x in bsum if x['scale']=='ALL')
 bg='\n'.join(f"|{x['scale']}|{x['config_id']}|{float(x['mean_delta_objective_s']):.6f}|{float(x['mean_global_gap_percent']):.6f}|{x['exact_reference_inputs']}|" for x in bsum if x['scale']!='ALL' and x['config_id'] in ['MEAN_P2','GROVER_P2','GROVER_P3'])
 doc('04_SERIES_B_FULL_RESULTS.md',f'''
# B：全36,800計画参照の結果

R0…R5は78/78/78/78/78/70物理入力、3/4/5/25/100/125配送先。460入力・26親・25需要群、8設定・10測定repを保持。全36,800参照で保存best計画を取得、route permutation・容量216PE・固定OD帰庫32400秒の実行可能性を確認した。**取得／実行可能100%は8,192shot後の保存best計画について**で、raw各shotの成功率や実配送成功率ではない。

## 全入力の初期解差と407参照のgap

各問題で10repを平均し、460入力を等重みにした全規模pooled記述は下表。主は規模別表であり、尺度混合のpooledは補助である。δ=sampled-best−古典初期、正は悪化。raw bestをmin(initial,sampled)で置換していない。

|設定|平均δ秒（460）|平均global gap%（407）|最適一致%（407）|初期改善%（460）|平均保存scope wall秒|
|---|---:|---:|---:|---:|---:|
{bt}

mirror5設定とactive設定は初期解と全参照で目的値が同じで、改善・悪化とも0。mirrorでは保存された同一matching orbitの古典chain-DP最小値と初期目的値が全入力で一致していた。従って、その支持内で初期解を目的値として上回る改善余地がない。global最適値とorbit最適値を混同しない。activeは保存3点gridでselected_t=0が460/460。これはその限定grid選択の結果であり、一般のQAOAが改善不能という証明ではない。

Grover P2/P3は初期解に対する改善参照の問題内平均率1.521739%だが、大規模側の悪化が大きい。全入力平均δは+1,765.006078／+1,760.995082秒で、実配送・電力量の悪化を示す値ではない。

|規模|代表設定|平均δ秒|平均global gap%|厳密参照入力数|
|---|---|---:|---:|---:|
{bg}

R0〜R2ではGroverが全入力で最適参照と一致し、R1/R2の一部初期解を改善。R3〜R5では最適一致0、正の平均δとなった。mirrorとGroverでは支持、初期状態、学習・検証方式が違うため、同じCPU予算・回路実装での優劣とは呼ばない。

## 参照欠測・比較対象

global厳密参照は407入力、R4の21／R5の32は未確定。global gap・最適一致の潜在分母は407×8×10=32,560参照。4,240参照はnull＋EXACT_REFERENCE_HOLDを保持。参照値は保存証明メタデータと入力に結び、数値を推測していない。証明solverを再実行していない範囲も明記する。

古典比較は(1)固定初期解、(2)同じmirror支持の保存exact DP、(3)旧CPU-matched古典改善920行、(4)global厳密参照を分離した。旧CPU-matchedは同じNPZ hashを確認したが、現在の8設定との予算一致は未確認の補助比較。古典の改善結果を現在の実測fit予算に再対応したとは主張しない。

現在Bの460全体を小さい部分問題へ分割した結果として扱っていない。mirrorの2^floor(n/2)支持は全配送先を残した制限であり、Groverのn!支持、active局所swapと区別する。旧別系列の部分問題実験やR4=99を混ぜていない。

## 計算時間・資源

`B_RESOURCES_PER_FIT.csv` は3,680fitを1回ずつ保存し、10rep分を重複加算しない。`B_SAVED_RESOURCES_LONG.csv` は{supp['saved_resource_fields']:,}個の元JSON fieldとpointer、scopeを保持。FIT、selected state、final validationのCPU/wall、RSS、backend演算・bond等を分ける。

fitだけの平均wallをend-to-end求解時間とは呼ばない。activeの保存wallはgrid・保存測定等のRESULT scopeで、mirror/GroverのFITと同じ範囲ではない。例としてGrover P3の最終検証wall平均はR3約168.745秒、R4約193.651秒、R5約226.554秒で、fitの約1秒と別工程である。CPU上のDP／MC／MPS処理時間で、仮想取得時間・QPU時間ではない。保存されない工程の時間を加算で補完しない。

shots8,192/測定rep、論理p2/p3、optimizer trace数と実optimizer反復数、backend two-site演算とcompiled native gate数を分離。hardware qubit数、compiled depth/gates、統一された全fit実行環境はHOLD。current分析環境のversionは既存量子実験の環境と区別して記録した。

Bの顧客定時率、地域SUMO完了、速度、DCは計算していない。元edge回復2,323／旧cache同一性HOLD2／partial2,662を保持しつつ、回復を必要としないOD指標の主母集団を減らさなかった。
''')
 crows='\n'.join(f"|{x['rolling_case']}|{float(x['mass_saving_kg']):.12f}|{float(x['saving_sum_Wh']):.9f}|{float(x['weighted_saving_percent']):.12f}|{float(x['individual_mean_percent']):.12f}|" for x in csum if x['series_id']=='C_T08' and x['dataset']=='CLASSICAL' and x['scenario_id']=='COND_S200_REF' and x['scale']=='ALL')
 equal='\n'.join(f"|{x['design_policy']}|{x['rolling_case']}|{x['reference_running_mass_kg']}|{float(x['mass_saving_kg']):.9f}|{float(x['weighted_saving_percent']):.9f}|" for x in csum if x['series_id']=='C_BRIDGE' and x['probe_id']=='equal_unknowns')
 doc('05_SERIES_C_CONDITIONAL_RESULTS.md',f'''
# C：材料・質量・固定速度DCの全件結果

算術PASS、科学解釈CONDITIONAL。T08全4,464行（CLASSICAL2,760、R0補助936、R1補助768）、T09全183行、bridge全25,760行を保持。元MATERIAL_ENERGYの744 dataset/method軌跡参照は465固有速度に集約できた。主感度の旧古典460軌跡と、Bの現行460入力を同一視しない。新しいSUMO・材料値・車両条件は追加していない。

## T08

凍結参照qはLP171.875、S200195.959596 Ah/kg（保持率からの逆算参照を丸めた既存値）、利用率1、平均電圧3.5V、gross20,000Wh、usable18,000Wh、負極360Ah/kg、正活物質率0.75、負0.98、N/P1.1。100cell×0.19kg、pack他15kgを含む簡略会計。比容量を量子計算で得た値とはしない。

LP mass96.145654799kg、S200 90.697357384kg、差 **5.448297415kg**。保存速度・共通非pack massでDCを再計算し、下表が個別元行から再現された。初期stock18kWh、補機境界外、回生なし、平坦、61kg回転等価mass、合計後正値化を変更していない。

|Crr|質量削減kg|DC削減総和Wh（460）|総量加重削減%|個別率平均%|
|---|---:|---:|---:|---:|
{crows}

同一LP controlの差は全行0。機械成分はW1転がり／W2空気／W3並進／W4回転のsigned値を保存し、成分別正値化へ変更しない。末端未観測区間はunknownで0Wh補完していない。旧N0の地域妥当性FAILを保持し、実EV・実配送での0.412579%削減とは呼ばない。

## T09とunknown mass

183行すべて完成pack massはNULL（HOLD）、全面対向1行はFAILを保持。既知部材は正負塗工材、Al/Cu、separator、liquid。全183行の各成分を独立Fraction式で照合した。case/tabs/foil margin/pack structure等は未実測で、残差で埋めない。T08の固定部材をT09へ再加算しない。

代表pair B015固定担持の既知LP−S差 **9.722608121kg**、B051固定面積の差 **5.977891152kg**。完成pack同士の差ではなく、全設計で一定の普遍的差でもない。設計全条件と部材差はC_T09_COMPONENTS_183、C_COMPONENT_MASS_BRIDGEに保存した。

b=既知LP−S、δ=未知S−LPとして、正味削減はb−δ。δ<bで軽量、δ=bで相殺、δ>bで逆転。未測定のδを0と確定していない。既存equal_unknownsは感度条件の一つである。

## bridge・走行条件

既存reference走行massは1,200／1,400kgのprobeで、T09完成pack massやB共通massではない。旧460速度×2設計×7δprobe×2Crr×2mass=25,760行を再計算。既存条件範囲ではmass/DC符号が一致し、saving11,040、相殺3,680、逆転11,040行。これらは独立試料数ではない。

|設計（δ=0感度）|Crr|参照走行kg|既知削減kg|総量加重DC削減%|
|---|---|---:|---:|---:|
{equal}

これはunknownが等しい場合の条件付き値で、T08より完成pack性能が高いという比較ではない。Crr・参照mass・scale別336strataの保存距離／再発進とDC差の記述を `C_DRIVING_CONDITION_SENSITIVITY.csv` に保存。相関を独立した走行条件の因果効果や回帰による校正とは呼ばない。

凍結kernelで20,260固有(trajectory,mass,Crr)を評価。独立のmass線形式との最大差は **{v['max_C_independent_DC_error_Wh']:.3g}Wh**。質量の単純比例はbranch切替があるため一般化せず、既存probeで検証した条件付き関係として報告する。

量子材料解析→材料改善は未実証。文献のVASP/DFTと量子計算機を区別する。完成pack・実車・寿命／安全・対象車校正の接続はHOLDのままである。
''')
 chosen=[x for x in ci if x['series_id']=='A_POLICY' and x['condition_id'] in ['D10-01','D10-04'] and x['metric'] in ['delta_mean_completion_s','delta_return_s']]
 cit='\n'.join(f"|{x['condition_id']}|{x['metric']}|{float(x['point']):.6f}|[{float(x['lower95']):.6f}, {float(x['upper95']):.6f}]|" for x in chosen)
 doc('06_PAIRED_STATISTICS_AND_SENSITIVITY.md',f'''
# 対応統計・不確実性

主解析単位は物理入力で、A78／成功機構64、B460、C主軌跡460。26親と25元需要groupを確認した。測定rep、36政策、材料設計・Crr・δprobeは独立物理入力へ水増ししない。

`PAIRED_COMPARISONS.csv` {s['paired_rows']:,}行はmetricごとの解析用long形式。`PARENT_PAIRED_SUMMARIES.csv` {s['parent_summary_rows']:,}行は親別の対応差、母数、有効数を保持。Bは10測定repを各input/configで先に平均して3,680行へ縮約し、seed SD／min／maxは別指標として残した。fit反復・学習不確実性を測定seed差と混同しない。

## 主指標と分母

Aはpolicyごとのpooled PE率、件数率を副、機構は64内の対応差。B主は規模別の入力等重みsampled−initial秒、全規模pooledは補助。gap/最適一致は407のみに限定。C主は設計・圧力を固定したWh差と総量加重削減率、個別率平均を別欄にする。C全反復を1つの量子効果にまとめない。

## 区間は補助感度

有限固定cohortの記述値を主結果とし、25需要groupを丸ごと10,000回、PCG64 seed20261102で再標本化したpercentile95%区間を **{s['bootstrap_contrasts']:,}事前定義contrast** に保存した。親・規模・政策・測定repの依存をgroupごと保持し、PE分母も再計算。source groupを無作為抽出した現実母集団である証拠はないため、実地域・モデル誤差のCIとは解釈しない。

|条件|指標|点差秒|需要group補助区間|
|---|---|---:|---|
{cit}

全A定時率差は0ppで補助区間も[0,0]。これはモデル上の余裕と有限集団の結果で、同等性検定の代替ではない。小さい差・区間内0・同等を区別する。Crr幅は物理モデルenvelopeで、統計CIではない。

**検定0、p値0件**。有意差が出るまで条件・repを変更せず、全36政策／全8設定を提示した。primary／補助／旧古典資料を区別し、最良条件だけを論文に選ばない。`CLUSTER_SENSITIVITY_INTERVALS.csv` は有効cluster数と未定義resample数を保持する。

独立コードで全{sv['bootstrap_contrasts_recalculated']:,}区間を再計算し一致。反復数10,000×1,176は実配送の標本数ではない。53 exact欠測は率の分母へ入れず、原参照行は削除しない。Cの183NULLと1FAILも除外によって見えなくしない。

OD倍率や新しい期限・mass・合成速度は主分析へ追加していない。今回の不確実性区間は、時間不変OD・理想サービス、材料入力・unknown BOM、N0妥当性等の構造誤差を包含しない。これらは条件・限界として別記する。
''')
 doc('07_CAUSAL_PATH_RESULTS_AND_LIMITATIONS.md','''
# 因果経路の定量結果と限界

## 経路1

保存CPU計算でAのQAOA取得64/78を観測し、固定政策へ接続した。量子採用1,344/2,808、古典切替1,464/2,808、正出発遅延936。全政策のモデル定時率は100%で古典との差0pp。routeだけの変更や出発変更は完了時刻を動かすが、待機・期限余裕によって定時率へ伝達しなかった。これは技術的変更が成果へ現れない条件の定量例である。

Bでは8設定・460入力で計画指標を検証し、制限支持／gridで初期解を維持する6設定、smallでは改善するがlargeではraw目的値が悪化するGrover系を区別した。保存CPU時間はbackend・精度・fit/validationで変わる。QPU取得時間や量子優位を実証していない。

計画→固定OD時刻・率はCONDITIONAL。計画→地域速度→走行DC、実荷物引渡し、地域道路妥当性は未検証／不適合のまま。旧軌跡をBへ転用せず、B定時率・B DCは一件も計算していない。

## 経路2

既存材料参照値・会計条件からT08 mass差5.448297415kg、固定旧速度下の下側Crr総量加重DC差0.412579010%を再現した。T09既知差9.722608121／5.977891152kgはunknown質量差δによって相殺・逆転する。既存25,760probeで符号伝達を確認した。

文献の材料試験値はOBSERVED_PUBLISHED、参照比容量逆算はDERIVED、電極／pack会計・固定速度DCはCONDITIONAL。量子計算機による当該材料の改善はUNTESTED。T09完成pack183HOLD・対向1FAIL、道路N0/N1のINVALIDを保持する。

## 主張可能な範囲

- 固定された数理問題での計画品質と取得、仮想運用政策の採否・出発・理想OD配送成果の媒介。
- 同じ保存速度・非pack条件で、指定された質量変更が凍結Controlled-DCへ伝達する範囲とunknown BOMの成立境界。
- 改善0・悪化・消失を含む全件結果と再現手順。

主張できないのは、地域EV配送の実績改善、QPU実行時間／量子優位、現行Bの省電力、完成pack／実車の改善、量子材料解析が性能向上を引き起こした実証である。A/B/Cを加算した総合量子効果量も作成しない。

## 論文へ反映する内容

方法はA_FIXED_OD_NO_SUMO_V1、D03/D10/D11、raw B sampled-best、407/53分母、26親/25group、Cの2会計と固定速度条件を具体的に記す。結果はA定時率0ppと時刻差、B規模別改善／悪化、C既知・未知mass境界を別表にする。考察は待機吸収・期限余裕・支持制限・材料未知部材を説明し、結論は条件付き機構へ限定する。

追加情報が必要なのは実世界の主張を行う場合の独立旅行時間・対象車校正・荷物kg・full-cell/pack BOM・実QPU材料解析等である。現行の条件付き修士研究をまとめるために、地域SUMO修復や新しい量子学習を必須条件へ戻す必要はない。今回は研究docs・論文を編集していない。
''')
 times=[]
 for lab in ['STAGE0','A_BATCH','B_BATCH','C_BATCH','VERIFY_BATCH','A_FULL','B_FULL','C_FULL','VERIFY_FULL','A_REPLAY','B_REPLAY','C_REPLAY','STATISTICS','SUPPLEMENT']:
  m=js(O/(lab+'_RUN.json'))['metrics'];times.append(f"|{lab}|{m['wall_s']:.6f}|{m['CPU_s']:.6f}|{m['max_RSS_bytes']:,}|")
 doc('08_REPRODUCIBILITY_AND_FINAL_REVIEW.md',f'''
# 再現性と最終レビュー

算術・追跡性PASS、モデル解釈CONDITIONAL。独立全件検算{v['checks']:,}項目、統計・interval・再実行検算{sv['checks']:,}項目に不一致0。独立C DC最大差{v['max_C_independent_DC_error_Wh']:.3g}Wh。主出力14CSVは再実行でbyte hash一致 (`REPLAY_OUTPUT_HASH_CHECK.csv`)。

## 状態を分離

|対象|判定|
|---|---|
|A/D11判断・時刻・分母とモデル再実行|PASS算術／CONDITIONAL理想OD|
|B全計画・407参照のgap・保存CPU資源|PASS算術／CONDITIONAL支持・CPU比較|
|B exact53、compiled資源、統一旧実行環境|HOLD・NULL保持|
|C T08/T09既知部材と固定速度DC|PASS算術／CONDITIONAL工学適用|
|T09完成pack183|HOLD|
|T09全面対向1|FAILを保持|
|道路N0/N1地域受入|FAILを保持|
|B計画→DC、量子解析→材料改善|UNTESTED|

## コマンド

既存環境 `.conda/bin/python -B`、現在versionは `ANALYSIS_ENVIRONMENT.json`。実コードSHA、入力SHA、出力SHAは `SOURCE_AND_OUTPUT_HASHES.csv` と `ARTIFACT_MANIFEST.json`。`OUTPUT_SCHEMAS_FROZEN.json` は事前契約、`DATA_SCHEMA_AUDIT.json` は実際の全CSV構造・PK検査。

```bash
.conda/bin/python -B review_outputs/no_sumo_full_analysis_20261102/run01/stage0.py
.conda/bin/python -B review_outputs/no_sumo_full_analysis_20261102/run01/run_a.py --batch
.conda/bin/python -B review_outputs/no_sumo_full_analysis_20261102/run01/run_b.py --batch
.conda/bin/python -B review_outputs/no_sumo_full_analysis_20261102/run01/run_c.py --batch
.conda/bin/python -B review_outputs/no_sumo_full_analysis_20261102/run01/verify_independent.py --batch
.conda/bin/python -B review_outputs/no_sumo_full_analysis_20261102/run01/batch_gate.py
.conda/bin/python -B review_outputs/no_sumo_full_analysis_20261102/run01/run_a.py
.conda/bin/python -B review_outputs/no_sumo_full_analysis_20261102/run01/run_b.py
.conda/bin/python -B review_outputs/no_sumo_full_analysis_20261102/run01/run_c.py
.conda/bin/python -B review_outputs/no_sumo_full_analysis_20261102/run01/verify_independent.py
.conda/bin/python -B review_outputs/no_sumo_full_analysis_20261102/run01/run_a.py --replay
.conda/bin/python -B review_outputs/no_sumo_full_analysis_20261102/run01/run_b.py --replay
.conda/bin/python -B review_outputs/no_sumo_full_analysis_20261102/run01/run_c.py --replay
.conda/bin/python -B review_outputs/no_sumo_full_analysis_20261102/run01/statistics_tables.py
.conda/bin/python -B review_outputs/no_sumo_full_analysis_20261102/run01/resource_and_sensitivity.py
.conda/bin/python -B review_outputs/no_sumo_full_analysis_20261102/run01/verify_statistics.py
.conda/bin/python -B review_outputs/no_sumo_full_analysis_20261102/run01/write_reports.py
.conda/bin/python -B review_outputs/no_sumo_full_analysis_20261102/run01/final_review.py
```

再実行はレビュー一式を新領域へ複製して行う。コードOは自ファイルの親を使用し、旧科学runnerは起動しない。入力R/U/B/Lの保全パスが必要で、公開Gitだけでの全再現性を達成したとは言えない。原文献から全入力を再生成したわけでもなく、現実配送・電池・車両妥当性は未達。

## 資源実測

|process|wall秒|CPU秒（累積）|最大RSS bytes|
|---|---:|---:|---:|
{chr(10).join(times)}

測定はprocessごと。wallはmain内、CPUはimport等も含むprocess累積で、thread実行等によって単純比較できない。上表は今回の既存データ分析費用で、保存量子計算の元実験コストとは別。primaryチェックログは100,000行で上限を設けた場合があるが、検査ループは全行を処理し、不一致なら直ちに失敗する。独立検証は全{v['checks']:,}照合を数え、件数・PK・分母と再実行を別途検査した。

## 保全・修正・残作業

`FINAL_REVIEW.json`、`INPUT_HASH_FINAL.csv`、`GIT_DIFF_FINAL.patch`、`GIT_STATUS_FINAL.txt` に最終保全を記録する。書込みは新レビュー領域のみ。元の道路・OD・計画・FREEZE・docs・DOCXを変更していない。確認範囲は台帳記載ファイルであり、未読バックアップの全内容を監査したという主張ではない。

統計検証の初回は変数名metricが関数を隠し、数値照合後の資源記録で停止した。元データ不一致は0。修正前コード／ログ、diffをrevisionsへ保存し、修正後に全統計検証を再実行してPASSを確認。集計CSVの追跡用metadataを追加し、物理入力SHAと集計元table hashのscopeを明記して再検証した。科学的評価条件は変更していない。

論文転記前には表の符号・分母・単位・scopeを確認する。文章・図表の編集、モデル仮定の章間整合、引用／付録、外部保全データの配布範囲が残作業。今回の全件分析と検証はここで停止し、新規地域実験や論文編集を自動開始しない。
''')
 matrix=rows(P4/'CAUSAL_PATH_EVIDENCE_MATRIX.csv');result_map={'P1-01':('A_RAW_COMPUTATION_RESOURCES_78.csv;B_PLAN_REFERENCES_36800.csv','A acquired64/78;B saved best plans36800;CPU simulation observations'),'P1-02':('B_SUMMARY_BY_SCALE_AND_METHOD.csv','6 settings equal initial objective;Grover worsens mean large-scale raw objective;exact407'),'P1-03':('A_POLICY_DECISIONS_2808.csv','Quantum1344;classical1464;positive departures936'),'P1-04':('A_DELIVERY_COMPLETION_BY_STOP.csv','Fixed-OD modeled completion and waiting, not native arrival/handover'),'P1-05':('A_SUMMARY_BY_CONDITION.csv','All36 policies PE/count100%;difference0pp'),'P1-06':('PRIOR_ARTIFACTS_PINNED.csv','Network INVALID retained;no new diagnostic or native run'),'P1-07':('B_PLAN_REFERENCES_36800.csv','B_DC_UNTESTED_NOT_CALCULATED'),'P2-01':('PRIOR_PROTOCOL_RETAINED.json','Published material test conditions only'),'P2-02':('C_T08_ENERGY_FULL.csv','Fixed q references171.875/195.959596Ahkg;not quantum outputs'),'P2-03':('C_T09_COMPONENTS_183.csv','T08mass difference5.448297415kg;T09known differences9.722608121/5.977891152kg'),'P2-04':('C_BOUNDARY_SIGN_VALIDATION.csv','Saving11040;cancel3680;reversed11040 existing probe rows'),'P2-05':('C_CONDITIONAL_MASS_DC_SUMMARY.csv','T08weighted lower-Crr saving0.412579010%;conditional saved speeds'),'P2-06':('C_T09_COMPONENTS_183.csv','Quantum-to-material improvement UNTESTED;complete pack183HOLD;footprint1FAIL')}
 for row in matrix:
  output,result=result_map[row['edge_id']];row.update(current_output_paths=output,quantitative_result=result,current_implementation='run_a.py' if row['edge_id'] in ['P1-03','P1-04','P1-05'] else 'run_b.py' if row['edge_id']=='P1-02' else 'run_c.py' if row['edge_id'] in ['P2-03','P2-04','P2-05'] else 'saved_evidence_readback_only')
 table('CAUSAL_PATH_EVIDENCE_RESULTS.csv',matrix)
 dump('REPORT_SOURCES.json',list(SRC.values()))
if __name__=='__main__':main()
