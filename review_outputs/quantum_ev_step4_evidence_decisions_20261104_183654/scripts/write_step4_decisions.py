from pathlib import Path
import csv,json,hashlib,collections,re
O=Path(__file__).resolve().parents[1];R=O.parents[1];U=Path('/home/takuma/kmd-analysis-pre-clean-20261102-112222/untracked');S2=R/'review_outputs/quantum_ev_step2_analysis_trial_20261104_155535';S3=R/'review_outputs/quantum_ev_step3_synthesis_trial_20261104_174309';W=R/'review_outputs/quantum_ev_thesis_step3_integration_20261104_173959';T8=U/'review_outputs/material_ev_stage2_20261026/run02';T9=U/'review_outputs/t09_open_data_model_20261029/run01';T6=U/'review_outputs/material_ev_stage1_20261024/run03';H=U/'docs/research/EV_QUANTUM_APPLICABILITY_BASELINE_REVIEW_20261023.md';P=U/'review_outputs/causal_engineering_audit_20261027/run01/SOURCES/chen2020.pdf';M=R/'01_research_design/methodology/CONTROLLED_MASS_TO_DC_MODEL_FREEZE.json'
source=list(csv.DictReader((O/'evidence/SOURCE_LEDGER.csv').open()));sm={x['path']:x for x in source}
def pin(p):
 p=Path(p).resolve();assert p.is_file(),p
 if str(p)not in sm:
  with p.open('rb')as f:h=hashlib.file_digest(f,'sha256').hexdigest()
  x=dict(path=str(p),sha256=h,bytes=p.stat().st_size,role='Step4採用判断に直接参照した根拠',locator='主張台帳のlocator参照');sm[str(p)]=x;source.append(x)
 return sm[str(p)]['sha256']
def md(name,s):(O/name).write_text(s.strip()+'\n')
def csvout(name,rows):
 with(O/name).open('w',newline='')as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
claims=[]
def c(id,path,claim,judgment,adoption,arithmetic,input_status,dep,files,locator,condition,allowed,forbidden,issue='限界として保持可能',needed='主張を広げない限り追加検証不要'):
 files=[Path(f)for f in files];hashes=[pin(f)for f in files]
 claims.append(dict(claim_id=id,pathway=path,claim=claim,judgment=judgment,adoption_decision=adoption,numerical_verification=arithmetic,scientific_input_basis=input_status,Chen_dependency=dep,evidence_files=';'.join(map(str,files)),evidence_sha256=';'.join(hashes),evidence_locator=locator,applicability_conditions=condition,usable_thesis_expression=allowed,prohibited_expression=forbidden,unresolved_handling=issue,required_verification=needed))
c('P1-01','1','36,800保存bestは可行、主greedyへの正改善0','PASS','主結果として採用','PASS：主対照行・Fraction差を再検算','保存入力・制約・対照を確認。実配送妥当性とは別','NO',[S2/'PATH1_PAIRED_COMPARISONS.csv',W/'NUMERICAL_AUDIT_CHECKS.csv'],'primary_comparison=True;460×8×10;JQ,JC Fraction','B時間窓なし、8保存設定、保存best、容量/帰庫制約','対象460入力の36,800保存bestは全て可行であり、主greedyに対する正のΔJは確認されなかった。','量子最適化は一般に改善できない／全shot・実配送が成功した')
c('P1-02','1','R5 Grover p2の平均ΔJと入力間SD','PASS','主結果として採用','PASS：70入力へ集約し再計算','有限保存cohortの記述統計','NO',[S2/'PATH1_PAIRED_COMPARISONS.csv',O/'evidence/VERIFICATION_RESULT.json'],'R5/GROVER_P2、各入力10測定平均','ΔJ=JC−JQ、入力を等重み、sample SD','R5の70入力では平均ΔJが−5,983.7秒、入力間SDが1,314.4秒であった。','700または36,800独立入力の平均／実配送母集団平均')
c('P1-03','1','R5 group補助感度区間','CONDITIONAL','補助統計として採用','PASS：前回独立再現記録を入力hashと共に継承','仮想需要group再標本化、実配送無作為標本ではない','NO',[S2/'PATH1_UNCERTAINTY_INTERVALS.csv',W/'NUMERICAL_AUDIT_RESULT.json'],'10,000回 seed20261102、−6516.668692〜−5515.460176s','group内の親・規模・測定依存を保持','需要group再標本化による補助感度区間は−6,516.7〜−5,515.5秒であった。','実配送母平均の保証された95%信頼区間')
c('P1-04','1','参照414入力の証拠区分','CONDITIONAL','証拠強度を明記して参照採用','PASS：234+78+61+41=414、未証明46','列挙234/保存整数DP78/独立有理双対61/保存MIPのみ41','NO',[S2/'EXACT_REFERENCE_STATUS.csv',S2/'PATH1_REFERENCE_STRENGTH_SENSITIVITY.csv'],'accepted_exact_available=True;reference_evidence_class','41は外部VIPRなし、373強化参照感度を併記','採用参照は414入力であり、そのうち41入力は保存MIP等値証拠に条件付けられる。','414全てを今回独立に最適証明した')
c('P1-05','1','追加7入力の有理数双対証明','PASS','限定した参照強化として採用','PASS：既存一次証明の独立検算を継承','双対可行性と可行巡回路費用の有理等値','NO',[S2/'EXACT_REFERENCE_RECHECK_RESULTS.csv',S2/'EXACT_REFERENCE_BOUND_COMPARISON.csv',W/'NUMERICAL_AUDIT_CHECKS.csv'],'R4_021,030;R5_019,024,052,062,063','入力・行列と証明の同一性に限定','独立有理数双対により7入力を追加証明した。','未証明46も最適と推定してgapへ算入した')
c('P1-06','1','旧未証明53のSCIP停止理由','PASS','停止条件の訂正として採用','PASS：保存状態と証明差の監査記録','optimal終了と厳密な下界/保存経路一致は別','NO',[S2/'EXACT_REFERENCE_FAILURE_AUDIT.md',S2/'EXACT_REFERENCE_STATUS.csv'],'old proof/termination and witness−bound','旧53入力の保存実行に限定','旧53入力はoptimal終了後も有理数下界と保存巡回路費用が一致せず、単純なタイムアウトとは扱わない。','53入力は全てタイムアウトした')
c('P1-07','1','未証明46入力のglobal最適gap/一致','HOLD','該当gap・最適一致の確定値は不採用','数値を補完しない','最適証明不足','NO',[S2/'EXACT_REFERENCE_STATUS.csv'],'UNPROVED_VALID_BOUNDS=46','可行なJ・主対照差は使用可。global J*は使用不可','46入力の参照最適値は未証明であり、gap・最適一致の集計から除いた。','微小gapなので最適／460全件の最適一致率','当該断定には追加検証不可欠；現在は限界として保持可能','整数・有理数の最適証明。現行限定結果を完成するための再求解は不要')
c('P1-08','1','mirror支持内最小=初期、active t=0','CONDITIONAL','支持・探索設計の制約として採用','PASS：保存支持監査・実装を確認','matching-chain DPと保存3点gridに限定','NO',[S2/'PATH1_SUPPORT_AUDIT.csv',S3/'PATH1_CONTRIBUTION_CONDITIONS.md'],'mirror orbit/global区別、active 460 t=0','支持と主greedyが初期以下という対象条件','この支持内の候補では主greedyへの改善余地がなく、active保存gridは全460入力でt=0を選択した。','全mixer・全支持・全QAOAの限界')
c('P1-09','1','追加統制9,312fit/93,120測定と取得件数','PASS','診断入力の結果として採用','PASS：raw測定93,120行・rep0から件数再集計','3入力合計96条件×97fit、10測定を学習反復としない','NO',[S2/'experiments/QAOA_MAIN_MEASUREMENTS.csv',S2/'QAOA_CONTROLLED_EXPERIMENT_DESIGN.md'],'R1_020/FULL_PERMUTATION/BASIS_INITIAL/GRAPH_SWAP/QAOA/rep0','CPU exact期待値学習、各8192shots','指定条件の最適解取得はp1で58/97、p2で78/97であった。','主greedyより58/97または78/97改善した')
c('P1-10','1','Wilson区間と取得確率の解釈','CONDITIONAL','指定条件内の取得評価として採用','PASS：Wilson式をraw件数から再計算','97開始角と測定手順に条件付き','NO',[O/'evidence/VERIFICATION_RESULT.json',S2/'QAOA_CONTROLLED_CELL_SUMMARY.csv'],'p1 49.8437–68.9978%;p2 71.4216–87.0861%','主greedyは3診断入力で既に最適。未見需要のCIではない','条件付きWilson 95%区間はp1が49.8〜69.0%、p2が71.4〜87.1%である。','入力全体における量子優位の確率を示した')
c('P1-11','1','9,603工程時間記録と固定例中央値','PASS','CPU計測として採用','PASS：行数確認、前回raw固定例集計を継承','測定scope・同一ホスト条件を確認','NO',[S2/'PATH1_RUNTIME_RESULTS.csv',S2/'PATH1_RUNTIME_PROTOCOL.md',W/'tables/RUNTIME_FIXED_EXAMPLE.csv'],'R1_001/FULL_PERMUTATION/UNIFORM_SUPPORT/PROJECTOR/p2/97each','学習＋10測定、wall中央値、非重複工程、除外工程明記','固定4顧客例のCPUパイプライン中央値はQAOA34.6ms、別学習脱位相35.0msであった。','QPU実機時間／greedyへの総時間優位')
c('P1-12','1','τ_total≤H_planという適用条件','CONDITIONAL','定義した運用上の必要条件として採用','不等式は定義上の条件。閾値の実測なし','締切内取得のみで採用・実配送成功を保証しない','NO',[S2/'STEP2_CONTRIBUTION_CONDITIONS_SUMMARY.md',S2/'UNRESOLVED_ITEMS.md'],'H05;3.11','必要な工程の全てと実際の計画締切を含む','運用上の計画採用には全工程時間がH_plan以内であることを要するが、本研究でH_planは同定していない。','帰庫期限32400秒が計画計算時間の閾値である')
c('P1-13','1','QPU・公平な総性能・実出発効果の定量化','HOLD','数値的な性能・運用効果の断定は不採用','CPUと出力数の違いを確認。実機/時刻測定なし','旧予算統制、compiled資源、H_plan/採用/実運用が未接続','NO',[S2/'PATH1_RUNTIME_PROTOCOL.md',S2/'UNRESOLVED_ITEMS.md'],'H03,H05,H06','保存解品質差とCPU計測を報告する範囲は妨げない','総性能順位、QPU資源、取得時間による出発・配送成果の変化は未検証である。','量子方式が実務上高速化し配送を改善した','当該断定には追加検証不可欠；現行研究の限界として保持可能','同出力・同予算比較、コンパイル/実機測定、全工程時刻とH_plan')
c('P1-14','1','量子優位性または量子一般の不可能性','NOT CLAIMED','結論から除外','主cohortの正改善0は確認','アルゴリズム・支持・比較系・規模を越える一般化根拠なし','NO',[S2/'PATH1_STATISTICAL_REPORT.md',S3/'PATH1_LIMITATIONS.md'],'結果範囲と一般化の分離','対象条件を越える主張を行わない','本研究は量子優位性を確認しておらず、量子計算一般の可能性を否定するものでもない。','量子優位性が成立した／量子計算は配送に寄与し得ない')
c('M-01','2','Chen原著が報告した容量・保持率と測定方法','PASS','文献内の実験報告として採用','PASS：保全PDF再抽出から数値・Methods確認','原著Fig5g、Li金属CR2025、2.0–4.8V、室温、1C=200mA/g','DIRECT_SOURCE',[P,O/'evidence/CHEN2020_REEXTRACTED.txt'],'pp7–8 Fig5g；p11 Electrochemical characterization','本研究で追試したのではない。活物質担持1–2mg/cm²、粉末配合75%','Chen et al.（2020）は、指定の半電池試験において100cycle後1CでLP121mAh/g・保持率70.4%、S-200194mAh/g・99.0%を報告した。','本研究で再現実験した／EV黒鉛全電池容量が測定された')
c('M-02','2','171.875/195.959596Ah/kgの由来','PASS','逆算参照値の算術・来歴として採用','PASS：121/.704、194/.99と実行丸めを照合','原著の直接初回値ではない。S実行値は小数6桁丸め','YES',[T6/'T06.json',T8/'SCENARIOS.json',O/'evidence/VERIFICATION_RESULT.json'],'LP_QREF/S200_QREF、scenario.parameters.q_ref','逆算分母の基準cycle/activationは未確定','171.875および195.959596Ah/kgは100cycle容量と報告保持率から作成した逆算参照値である。','原著が初回容量171.875/195.959596を直接測定した')
c('M-03','2','逆算qペアを実用全電池の確定材料入力として採用','HOLD','主分析の確定材料値として不採用','算術PASSと入力適格性は別','Stage1 allHOLD、T07 ALL_HOLD、T08 HOLD、practical NOT_EVALUATED','YES',[H,T6/'T06.json',T8/'T07.json',T8/'T08.json',T8/'SCENARIOS.json'],'§5.1/§6/§7/§10.2；scientific_adoption','参照シナリオ実行の許可を科学的採用へ昇格しない','逆算参照値の実用全電池への適格性は確認されておらず、確定材料入力としては採用しない。','実用材料容量が確定し、主たる代表改善量を得た','主材料入力として採用するには追加検証不可欠','同一基準/レート/試料の放電容量、保持分母/前処理/正規化、fullcell容量・電圧・Li在庫・寿命/安全の接続')
c('M-04','2','u1/V3.5/N/P1.1/負極360/34kg固定の入力根拠','CONDITIONAL','明示した仮定シナリオのみ採用','PASS：実行JSONの値とadoption=HOLDを確認','V/u/負極/固定部材は実用LP/S測定値ではない。75%は実験配合の移用','NO_DIRECT_VALUE;YES_COMPOSITE',[T8/'SCENARIOS.json',T9/'RUN_CONFIG.json',H,O/'evidence/T08_PARAMETER_ADOPTION.csv'],'parameters、§7初期値評価','gross20kWhとusable18kWhの区別、保持率/ICE二重計上なし','仮定した設計・部材条件を固定してモデル応答を算定した。これらを実用セル設計の確定値とはしない。','全ての入力が原著で実測・科学的採用済みである','実製品代表値とするには追加検証不可欠；仮定としては保持可能','平均fullcell電圧、利用率とformation、負極仕様、部材BOMと採用境界')
c('P2-01','2','T08連続入力の解析感度','CONDITIONAL','材料値に依存しない主モデル結果として採用','記号式の微分・符号を確認','設計会計モデル、各入力の実現性/独立操作は未証明','NO_SYMBOLIC',[T8/'SOURCE_SNAPSHOT/pack_design.py'] if (T8/'SOURCE_SNAPSHOT/pack_design.py').is_file()else [S2/'scripts/path2_analysis.py',S3/'data/PATH2_ANALYTICAL_SENSITIVITY.csv'],'M=E/V[1/(qufp)+r/(qnfn)]+F+δ','正の定義域、他条件固定、設計依存Dが変化するなら微分項追加','他条件を固定した簡略会計ではq・u・V等の増加は質量を減少させる。設計部材が変化する場合、全微分にその項を含める。','材料能力が現実に独立改善でき、同じ割合でpackが軽量化する')
c('P2-02','2','ΔM=b−δと一般的相殺・逆転条件','PASS','会計恒等式として主分析へ採用','定義から成立する恒等式','同じ部材境界、重複/欠落した差分をδへ明示する','NO_SYMBOLIC',[S3/'PATH2_MAIN_VS_REFERENCE_RESULTS.md',S2/'scripts/path2_analysis.py'],'b=基準−比較の既知会計差、δ=比較−基準の会計外部材差','bの具体値やδ実値が確定したことを意味しない','同じ部材境界ではΔM=b−δであり、δ=bで差が消失し、δ>bで質量差の符号が逆転する。','全材料に共通の固定相殺閾値は5.448kgである')
c('P2-03','2','同電圧・同部材での有効比容量条件','CONDITIONAL','限定した解析的条件として主分析採用','質量式の符号から導出','材料名・逆算定数を不要とする不等式','NO_SYMBOLIC',[S3/'PATH2_MAIN_VS_REFERENCE_RESULTS.md',S3/'data/PATH2_ANALYTICAL_SENSITIVITY.csv'],'q_s u_s > q_ref u_ref','同E/V/fp/負極/部材、追加差0。別条件では全式へ戻す','同電圧・共通部材等の条件下では有効比容量の大小が正極塗工材の質量差の符号を定める。','利用率0.877094が全技術に普遍的な必要十分条件である')
c('P2-04','2','材料入力を使わない凍結DC質量応答','CONDITIONAL','主モデル結果として採用','PASS：460速度×2Crrで核とaffine式/端点/微分を再検算','保存速度・固定物理から算定、q/u/V不要。質量区間は研究用probe','NO_CAPACITY_INPUT',[M,R/'src/kmd_quantitative/energy/frozen_sources/run_full_controlled_dc.py',O/'evidence/DC_MATERIAL_FREE_RECHECK.csv',S3/'data/DC_MASS_KERNEL_INDEPENDENT.csv'],'E(m)=Σmax(a_t m+c_t,0)/.9；1000–1250kg','平坦・回生なし・補機/旋回対象外、同速度・同Crr・固定61kg回転等価質量','検証した走行質量1000〜1250kgでは、全920軌跡/Crr条件でDC電力量の質量に対する傾きは正であった。','材料改善が確認され、実EVで0.413%削減した')
c('P2-05','2','質量相殺とDCゼロ点・逆転の接続','CONDITIONAL','範囲付き主モデル結果として採用','PASS：凸区分線形の非減少微分と正の下端右微分','Chen非依存DC核＋一般質量会計の接続','NO_SYMBOLIC',[O/'evidence/DC_MATERIAL_FREE_RECHECK.csv',S3/'PATH2_MAIN_VS_REFERENCE_RESULTS.md'],'slope>0 at1000 right、convex ⇒ strict increase on interval','両走行質量が1000–1250kg内、同一保存速度/非pack質量/物理','この検証範囲ではΔMとΔE_DCの符号が一致し、δ=bが質量差とDC差のゼロ点になる。','全車両・全速度・全質量に普遍的な同値条件')
c('P2-R01','2','T08質量96.145655/90.697357kgとb5.448297kg','CONDITIONAL','条件付き参考例のみ採用；主たる材料効果量として不採用','PASS：原T08予算とFraction境界一致','逆算q＋V/u/負極/固定19+15kg仮定。科学的入力HOLDを継承','YES',[T8/'SCENARIOS.json',T8/'T08.json',S2/'PATH2_BOUNDARY_ANALYSIS.csv',O/'evidence/VERIFICATION_RESULT.json'],'COND_LP_REF/COND_S200_REF、T08_DEFAULT_MASS','入力未採用の参考シナリオであることを同じ本文/表/図に表示','未適格な逆算参照入力を用いる仮定例では、簡略質量差は約5.45kgとなる。実製品差の推定値ではない。','確定材料入力から完成パック5.448kg軽量化を実証した')
c('P2-R02','2','利用率.877094/電圧3.193156Vの具体境界','CONDITIONAL','条件付き参考例のみ採用','PASS：実行丸めqから境界を再現','逆算qと他の固定仮定に依存','YES',[T8/'SCENARIOS.json',S2/'PATH2_BOUNDARY_ANALYSIS.csv',O/'evidence/VERIFICATION_RESULT.json'],'T08_DEFAULT_UTILIZATION/T08_DEFAULT_VOLTAGE','LP側V3.5/u1固定、S側一変数変更。電圧変更は負極Ahも変更','同じ未適格入力を固定した仮定例のゼロ質量差境界はu約.8771、平均全電池電圧約3.193Vとなる。','実用材料がこの閾値を満たす／普遍的な成立条件を実測した')
c('P2-R03','2','DC総和比.412579/.413590%、平均.409329/.410435%','CONDITIONAL','条件付き参考例のみ採用；主代表削減率として不採用','PASS：端点920行から総和比/個別平均/sample SD再集計','入力HOLDのq由来質量差→固定残余走行質量→凍結DC','YES',[T8/'SCENARIOS.json',T8/'MATERIAL_ENERGY.csv',S2/'PATH2_OPERATION_CONDITION_ANALYSIS.csv',O/'evidence/VERIFICATION_RESULT.json'],'総和比100ΣΔE/ΣELP、平均個別率、SD.012172/.012018pp','旧460保存速度、2Crr、空荷・固定非pack質量・回生/補機除外','この未適格材料入力に基づく参考シナリオのモデルDC総和比は約.4126%/.4136%である。実EVや量子技術の達成値ではない。','量子材料改善で実車の電力量が約0.413%減ると確定した')
c('P2-R04','2','49点q、81点u/V、固定/追加質量、運転層別とgroup区間','CONDITIONAL','Chen依存の参考感度としてのみ採用','PASS：qLP/qS importと各case生成のコード/出力を確認','49点端点とu/Vの固定qは逆算入力。新独立材料データではない','YES',[S2/'scripts/path2_analysis.py',S2/'PATH2_SENSITIVITY_SUMMARY.csv',S2/'PATH2_OPERATION_STRATA.csv',S2/'PATH2_GROUP_SENSITIVITY_INTERVALS.csv'],'main qLP/qS、q_only/u_V/common_fixed_mass/additional_mass','132480行は決定論的格子、各基準質量・分母もq由来','連続格子・運転層別・group感度も同じ未適格な参照入力に依存する補助例である。','連続感度にしたのでChen依存が解消した／材料独立の統計保証')
c('P2-06','2','T09の面積・箔・膜・液の部材会計','CONDITIONAL','設計構造の補完として採用','PASS：保存式・既知小計・NULLと代表差を照合','NMC等から移用した密度/膜、設計probe。LP/S外部妥当性は未成立','STRUCTURE_NO;NUMERIC_YES',[T9/'model.py',T9/'RUN_CONFIG.json',T9/'PARAMETER_SOURCES.csv',T9/'T09_FINAL_ACCEPTANCE.md'],'両面箔area=face/2、void/liquid、known subtotal','活物質と塗工材の重複禁止、T08固定34kgの重ね加算禁止','T09は面積・構造による既知部材会計の変化を補うが、LP/S実セルや完成packの外部実証ではない。','公開データにより対象材料の全部材と完成パックを独立実証した')
c('P2-R05','2','T09具体差9.722608/5.977891kg・162共通条件','CONDITIONAL','条件付き参考例のみ採用','PASS：代表2設計の部材差を再計算、162全件NULL','同じ逆算q、移用密度・膜・液と設計担持/空隙率に依存','YES',[T9/'PACK_20KWH_SENSITIVITY.csv',S2/'PATH2_T09_COMMON_INPUT_SENSITIVITY.csv',S2/'scripts/path2_analysis.py'],'B015/B051;fixed_loading/fixed_area_LP, u=1,V=3.5','既知小計差、担持.1kg/m²/空隙.25等。完成pack差でない','同じ未適格参照入力と指定設計probeにおける既知部材差は約9.72/5.98kgである。','T09はChen依存を独立に検証し完成pack軽量化を示した')
c('P2-07','2','完成パック/未知BOMと対象材料設計の確定','HOLD','確定質量・実用性の断定は不採用','183原入力および162共通入力の完成質量NULLを保持','外装/タブ/箔余白/冷却/BMS/構造、対象密度/液保持等の独立証拠不足','YES_FOR_TARGET',[T9/'PACK_20KWH_SENSITIVITY.csv',T9/'T09_FINAL_ACCEPTANCE.md',T9/'RUN_CONFIG.json'],'complete_pack_mass_kg=null、T09 PARTIAL/T10 HOLD','既知小計とunknown差δを分離。δ=0は差が等しい仮定','対象材料の完成pack質量と最終軽量化の符号は、未知BOMが未確定のため判定できない。','未知部材0kg／δ=0が実証済み／T08とT09の完成品直接順位','当該断定には追加検証不可欠；モデル構造研究には限界として保持可能','同一LP/Sの全BOM・密度/空隙/厚さ/面積とfullcell条件、未知部材差の独立根拠')
c('P2-08','2','低担持と固定19kgの互換性','CONDITIONAL','設計互換性への注意として採用','PASS：原著1–2mg/cm²とT09仕様を条件に面積/Al/膜を算術確認','Al15µm等はChen自身の実測仕様ではなくT09移用仮定','YES_MIXED_ASSUMPTIONS',[P,T9/'RUN_CONFIG.json',O/'evidence/LOW_LOADING_COMPATIBILITY.csv',H],'loading .01–.02kg/m²、Al+膜と19kg比較','同じ低担持を維持し、同じT09箔/膜条件を置いた場合のみ','原著の低担持を維持しT09の箔・膜条件を置くと、これらだけでT08固定19kgを超え、両設計を同一視できない。','全ての実用セル設計が不可能／原著が誤りである')
c('P2-09','2','量子計算→対象材料改善→実用EV効果','NOT CLAIMED','実証済みの結論から除外','原著は古典DFT/VASPと電極実験。量子機の改善達成なし','本研究に計算精度→設計→材料試作→fullcell→実車の証拠連鎖なし','UNVERIFIED_LINK',[P,T8/'SCENARIOS.json',T9/'T09_FINAL_ACCEPTANCE.md',S2/'UNRESOLVED_ITEMS.md'],'原著Computational detailsとMethods、H08/H10/H11','探索可能性と達成性能を分離','量子材料解析から実材料性能への接続は検証しておらず、参考DC差を量子由来効果とは帰属しない。','量子計算が材料を改善し実EVのDC削減を達成した')
c('I-01','統合','能力・適用・成果の三層と二経路比較','CONDITIONAL','研究の方法的貢献・考察として採用','数値の共通効果量は算出しない','経路1の有限比較と経路2のモデル関係、未接続を分ける','MIXED_EXPLICIT',[S3/'CROSS_PATH_SYNTHESIS.md',S3/'PATH2_MAIN_VS_REFERENCE_RESULTS.md',W/'drafts/CHAPTER6.md'],'第6章の比較、Step4で主/参考を再判定','相異なる指標を同一改善率へ合成しない。観測必要条件とモデル十分条件を区別','技術能力が成果へ伝わるための媒介条件を、二つの異なる作用経路の証拠範囲を明示して比較した。','二経路の実証効果量を統合して社会システム全体の改善を証明した')
c('I-02','統合','社会制度・市場・導入普及・実道路配送全体の転換','NOT CLAIMED','実証範囲から除外','該当する測定・内生モデルなし','MLP/TIS参照は社会制度・市場効果の実証ではない','NO',[S3/'GENERALIZABILITY_ASSESSMENT.md',W/'drafts/CHAPTER6.md',S2/'UNRESOLVED_ITEMS.md'],'設計運用Bと導入普及Aの分離','大田区事例の固定境界内モデル。道路受入不成立も保持','本研究は主として設計・運用条件を扱い、社会技術システム全体の転換や普及過程を実証していない。','大田区の社会技術システム全体を再現し制度的寄与を証明した')
c('D-01','文書','Step3 Word試行版をそのまま科学的採用できる','HOLD','原稿全体の無修正採用は不採用；内容単位で本台帳を適用','旧数値監査PASS・Word表示確認は科学的入力採用の代替でない','補正済みS3とWord統合版の主分析/参考序列が不一致','YES_IN_PATH2',[S3/'CHEN_2020_ADOPTION_CORRECTION.md',S3/'PATH2_MAIN_VS_REFERENCE_RESULTS.md',W/'THESIS_SECTIONS_TRIAL.md',W/'ADOPTION_REVIEW.md'],'Word章5.5/5.6、要旨/結論/図5-4/5-5および旧採用推奨B','今回はWord編集せず、不整合の採否だけ決定','Step3 Word原稿の材料具体値は未適格入力に基づく参考例であり、主結果の代表値としての無修正採用は行わない。','48頁PDF検査と算術PASSにより科学的な原稿完成を確定した','原稿を正式使用する前に分類反映が不可欠；追加科学実験とは別','本Step4の主分析/参考/HOLDを本文・要旨・図表・結論・台帳へ一貫反映。今回は編集しない')
csvout('CLAIM_EVIDENCE_MATRIX.csv',claims)
# Full dependency chain at the actual saved file/column level.
deps=[
('N01','原著100cycle容量/保持率',P,'Fig5g;Methods','直接文献報告','なし','文献内報告のみPASS','121/70.4%,194/99.0%'),
('N02','逆算参照q',T8/'SCENARIOS.json','parameters.q_ref','N01','算術逆算とS丸め','算術PASS、主入力HOLD','171.875,195.959596Ah/kg'),
('N03','設計仮定',T8/'SCENARIOS.json','u,V,NP,q_negative,fp,fn,cell_other,pack_other','N02とは独立した仮定値','qと共に質量計算へ入力','仮定シナリオ限定CONDITIONAL','u1,V3.5,19+15kg等'),
('N04','T08質量',T8/'T08.json','budgets.COND_LP_REF/COND_S200_REF','N02+N03','grossエネルギーと正負極会計','参考例CONDITIONAL','96.145655/90.697357kg'),
('N05','T08具体境界',S2/'PATH2_BOUNDARY_ANALYSIS.csv','T08_DEFAULT_*','N02+N03+N04','差/一変数ゼロ式','参考例CONDITIONAL','5.448297kg,.877094,3.193156V'),
('N06','車両質量置換',T8/'T08.json','running_masses','N04+凍結B0残余質量','1043.888888889+M_T08','参考例CONDITIONAL','約1140.034544/1134.586246kg'),
('N07','参考DC電力量',S2/'PATH2_OPERATION_CONDITION_ANALYSIS.csv','baseline_DC_Wh,alternate_DC_Wh,individual_saving_percent','N06+保存速度+凍結物理','同一速度下のモデルDC','参考例CONDITIONAL','総和比.412579/.413590%'),
('N08','49点/81点/固定追加部材/運転層別/group',S2/'scripts/path2_analysis.py','qLP/qS imports;cases,ops,bins,ci','N02+N03+N04+N06+N07','連続格子でも基準/端点/分母に依存','参考例CONDITIONAL','132480行は独立材料証拠ではない'),
('N09','T09既知部材小計・差',T9/'PACK_20KWH_SENSITIVITY.csv','B代表行known_cell_components_sum_kg','N02+N03+T09移用密度/膜/液/担持/面積方針','容量→面積→部材、未知BOM NULL','参考例CONDITIONAL、完成packHOLD','9.722608/5.977891kg'),
('N10','T09 162共通条件/走行質量probe',S2/'scripts/path2_analysis.py','t09(),t9rows,T09_MASS_PROBE','N02+T09構造+T08走行質量参照','known差をT08参照質量でprobe；完成T09 packではない','参考例CONDITIONAL','未知差を0とする点も仮定'),
('N11','一般質量式・微分',S3/'data/PATH2_ANALYTICAL_SENSITIVITY.csv','記号q,u,V,f等','記号定義のみ','特定材料数値を代入しない','主モデルCONDITIONAL','材料の実現性保証なし'),
('N12','一般収支恒等式',S3/'PATH2_MAIN_VS_REFERENCE_RESULTS.md','ΔM=b−δ','同一部材境界の定義','b具体値を除けばChen非依存','数学関係PASS','δ=bは定義的ゼロ点'),
('N13','材料非依存DC質量応答',O/'evidence/DC_MATERIAL_FREE_RECHECK.csv','1000/1250kg端点・右微分','460保存速度+凍結物理+宣言質量probe区間','容量qもN04/N06も使わない','主モデルCONDITIONAL','920条件、最小傾き.827573/.854195Wh/kg')]
csvout('evidence/MATERIAL_DEPENDENCY_GRAPH.csv',[dict(node_id=a,node=b,file=str(p),sha256=pin(p),locator=l,parents=parents,transmission=t,decision=d,value_or_limit=v)for a,b,p,l,parents,t,d,v in deps])
# Unresolved issues: indispensable is defined relative to an intended claim, not as an obligation to do more experiments now.
issues=[
('U01','逆算qペアの主材料入力適格性','M-03;P2-R01–R05','主材料入力への昇格には追加検証不可欠','主分析には採用しない。参考例と分けることで現行研究の限界として保持可能','同条件・同基準容量、保持分母、前処理、S正規化、fullcellの電圧/Li在庫/形成・寿命/安全','新値を推定で代入しない'),
('U02','完成パックBOMとT09対象材料受入','P2-07;P2-R05','完成pack効果の断定には追加検証不可欠','既知部材モデルと一般δ境界だけを採用、NULL保持','対象材料固有の密度・空隙・厚さ/面積・外装/端子/余白/冷却/BMS/構造の独立値','残差補完や別材料外部データでHOLDを解除しない'),
('U03','未証明46/保存MIP41の外部証明','P1-04;P1-07','全460最適参照・414全独立証明には不可欠','Jの対照差、414/41明示と373層別で限界として保持可能','46の厳密証明、41の外部検証','本Step4のために新solver実験は不要'),
('U04','旧予算統制・未見入力・学習安定性','P1-01;P1-09;P1-13','一般的性能順位・未見入力保証には不可欠','保存cohortの記述と3入力診断へ限定して保持可能','同一出力/総予算、別入力、開始角と学習noiseの検証','今の非改善結果を削除しない'),
('U05','H_plan・全工程時刻・計画採用','P1-12;P1-13','定量的運用時間効果を主張するなら不可欠','条件式と未同定を明示して保持可能','実業務締切と全工程・採用/出発/配送時刻','帰庫期限を計算予算へ流用しない'),
('U06','QPU資源/時間/物理qubit','P1-13;P1-14','実機性能・量子優位の主張には不可欠','CPU計測と概念/実装上の資源条件に限定して保持可能','native回路、compile、誤りモデル/実機計測/queue','CPU値から推測しない'),
('U07','量子材料計算から実材料改善への接続','P2-09','量子帰属効果を主張するなら不可欠','現在の寄与条件研究ではNOT CLAIMEDとし限界保持可能','対象物性精度→設計→合成/電極/fullcell/packの独立証拠連鎖','感度シナリオで代替しない'),
('U08','道路受入・新B→走行DC・実車校正','P2-04;P2-09;I-02','実EV/地域運用結果への外挿には不可欠','保存固定速度モデルとBの解品質を別に採用して保持可能','道路受入、実車DC、Bルートと速度への検証済接続','460という件数でBとCをjoinしない'),
('U09','回生/補機/勾配/旋回/実積載/未観測末端','P2-04;P2-05','全行程の実車総電力を主張するなら不可欠','凍結モデルの対象外/unknownとして保持可能','別モデル版と独立測定、PE→kgの根拠','既存物理核へ無断追加しない'),
('U10','一部raw-shot可行率未保存','P1-01','全shot可行率を主張するなら不可欠','best可行率だけに限定して保持可能','保存sampleの範囲確認、必要なraw counts','bestの可行性を全shotへ拡張しない'),
('U11','材料独立の実用的数値範囲','P2-01;P2-R04','代表的材料改善量の推定には不可欠','記号感度・研究probe区間として保持可能','実用材料/設計制約から独立に妥当化した範囲','49点を新しい材料証拠としない'),
('U12','社会制度・市場・普及のモデル化','I-02','社会技術システム全体の転換実証には不可欠','本研究境界外としてNOT CLAIMED','別研究の社会的・制度的観測と内生モデル','MLP/TIS引用を実証の代用にしない'),
('U13','Step3 Wordの主分析/参考分類不整合','D-01','その原稿を無修正で正式利用することは不可','本Step4は判定を確定。今回はWordを保全し編集しない','将来編集する場合に要旨/5.5/5.6/図5-4/5-5/考察/結論へ本判定を反映','科学実験追加ではなく表現・採用役割の是正'),
('U14','Papachristos同定・一部主要候補本文','I-01','未確認文献に依存する主張を使う場合は確認不可欠','既に除外/確認範囲限定済みなら現行主要主張を妨げない','原引用意図・原著本文を確認','類似同年論文で補填しない'),
('U15','Wordネイティブ表示・大学最終様式','D-01','そのWordを提出する前に確認が必要','科学的採用判断とは分離し、今回は編集・レンダリングしない','研究者側の最終表示・体裁確認','数値PASSから提出完成としない'),
('U16','原網/需要の完全再生成と非公開依存','I-01;P1-01','公開cloneだけで全再現を主張するなら不可欠','保存入力・hash・計算確認の範囲へ限定して保持可能','原表セル、元生成器、中間処理と環境','研究全体の完全再現PASSとしない')]
csvout('evidence/UNRESOLVED_ISSUES_REGISTER.csv',[dict(id=a,issue=b,claims=c,verification_indispensable_for=d,current_handling=e,next_evidence=f,prohibition=g)for a,b,c,d,e,f,g in issues])
# Compare both previous Step3 products. They are independent and neither can override the primary adoption fields.
md('evidence/STEP3_VERSION_CONFLICTS.md',f'''# 先行Step3の解釈差と優先根拠

参照した版は二つある。Word統合版は{W}、補正済み統合考察版は{S3}である。単に時刻で選ばず、前者のCLAIM_EVIDENCE_LEDGER/ADOPTION_REVIEW/要旨/5.5–5.6/結論と、後者のCHEN_2020_ADOPTION_CORRECTION/PATH2_MAIN_VS_REFERENCE_RESULTSを比較した。

両版とも数値の条件付き性や完成pack未確定を述べているが、Word版ではChen逆算入力の主分析採否HOLDと、具体値を参考例に後置する序列が十分には反映されていない。Word版の「数値監査PASS」「条件付き候補B」は確定材料入力の承認とは解釈しない。原稿一括の無修正科学採用はD-01 HOLDとした。

本Step4では10月23日レビュー、Stage1最終run03 T06、10月26日run02 SCENARIOS/T07/T08、10月29日T09受入記録を優先する。補正済みStep3の主/参考区分はこれら一次成果物と整合するため、その区分を採用判断に採り入れた。過去の会話全件の独立復元を行ったとは主張しない。

補正済みStep3のSTEP4_HANDOFFにはWordコピーへの編集手順が含まれているが、今回の研究者指示はWord追加編集を禁止している。本Step4は科学的採否の確定のみを実施し、旧handoffの編集工程は実行しない。既存成果物はいずれも変更しない。
''')
# Core material audit.
v=json.load((O/'evidence/VERIFICATION_RESULT.json').open());compat=list(csv.DictReader((O/'evidence/LOW_LOADING_COMPATIBILITY.csv').open()))
md('MATERIAL_INPUT_PROVENANCE_AUDIT.md',f'''# 材料入力の来歴・科学的採用監査

## 判定

**Chen et al.（2020）の逆算容量171.875/195.959596Ah/kgは、主分析の確定材料入力として不採用（HOLD維持）とする。** 原著内の実験報告は文献記述としてPASS、逆算の算術はPASSである。指定値を用いた質量・具体的境界・電力量は条件付き参考例に限って採用する。これらの具体値を研究の主たる材料改善量・代表省電力量として採用しない。

「過去の棄却」として確認できた実体は、論文一般の否定や数式の誤りではなく、**特定用途への主入力採用保留**である。保存機械可読台帳はREJECTEDではなくHOLDである。この違いを変更しない。過去の会話全件まで復元したとはしない。

## 1　採否履歴と根拠の優先順

1. {H} の§5.1は「主設計値への採用保留」、§6は半電池→全電池移用の不足、§7は固定部材・平均電圧等の根拠不足を記録する。§10.2は逆算参照を参考S1とし、単一の実用LP/S初期容量ペアを推薦できないとする。
2. {T6/'T06.json'} はタスクstatus=PASSである一方、9レコード全てadoption=HOLDである。LP_QREF/S200_QREFはUSER_SUPPLIED_REFERENCE_ONLYで、初回測定容量ではない。
3. {T8/'SCENARIOS.json'} は条件付き数値実行を許すが、全パラメータのadoption=HOLDを維持する。T07.jsonはstatus=PASS、scientific_adoption=ALL_HOLD、practical_qualification=NOT_EVALUATEDである。T08.jsonもstatus=PASS、scientific_adoption=HOLDである。実行許可・検算成功を科学的採用の変更と読めない。
4. {T9/'T09_FINAL_ACCEPTANCE.md'} はT09 PARTIALと対象LP/S受入未達を明記する。全183行の完成pack質量はNULLであり、他材料データの算術検証を対象材料の科学的検証に読み替えていない。
5. 補正済みStep3はこのHOLDに整合する。Word統合版の採用序列が曖昧な箇所は、今回の判定で上書きするのではなく、独立した採否判断として訂正を記録する。既存ファイルは保全する。

## 2　原著が直接報告する量と逆算した量

原著PDF：{P}。同一byteコピーをevidence/CHEN2020_PRIMARY.pdfに保存し、pdftotextで再抽出した。出版社/PMC/著者公開サイトの再取得は今回アクセス制限があり、既存保全PDFを一次資料として使用した。オンライン再取得成功とは記録しない。

原著pp7–8のFig5g対応記述は、1C=200mA/g、100cycle後LP121mAh/g/70.4%、S-200194mAh/g/99.0%である。Methods p11はLi金属箔対極/参照極のCR2025、2.0–4.8V、室温、担持1–2mg/cm²、粉末:SuperP:PVDF=7.5:1.5:1を記す。75%は乾燥塗工材内の粉末比であり、セル全体の活物質率ではない。室温という記載は確認できたが、厳密なKelvin温度・試料別履歴・容量保持分母サイクル・硫黄処理後の正規化は確定できていない。旧JSONのnullは今回書換えない。

1mAh/g=1Ah/kgであり、121/.704=171.875、194/.990=195.959595…は算術上正しい。実行設定は後者を195.959596に丸めている。Stage1の195.960は別の丸めであり、今回の下流具体値の正本はrun02の六桁値である。小数末尾の一致は実験精度を意味しない。

保持率の分母容量を逆算できることと、その分母が製造後の初回放電・formation後の可逆全電池容量であることは異なる。Fig5b/cの初回0.5CとFig5gの1Cを混ぜない。LP初回充電238×初回効率.652≈155.2Ah/kgという別算術値を、Sの1C逆算値と対にして代替入力へ採用しない。121/194という100cycle後の直接報告ペアも、初期設計値の代替ではない。

原著の材料解析は古典DFT/VASPと電極実験であり、量子計算機が達成した性能改善の報告ではない。

## 3　入力から具体的出力までの依存

機械可読の全ノードはevidence/MATERIAL_DEPENDENCY_GRAPH.csv、実行パラメータの元adoptionはevidence/T08_PARAMETER_ADOPTION.csvに記録した。各ノードに実在パス・SHA256・参照列を付した。

|段階|保存一次成果物・計算|判定|
|---|---|---|
|原著試験値|原PDF Fig5g/Methods|文献内報告PASS|
|逆算q|SCENARIOS.json parameters.q_ref|算術PASS／主材料入力HOLD|
|u/V/負極/固定部材|同JSON、gross20kWh、u1、V3.5、N/P1.1、負極360、fp.75/fn.98、19+15kg|仮定例に限定|
|T08質量|T08.json：96.145654799/90.697357384kg|参考CONDITIONAL|
|具体的b/u*/V*|Step2 PATH2_BOUNDARY_ANALYSIS|{v['T08_b_kg']:.9f}kg／{v['u_boundary']:.9f}／{v['V_boundary']:.9f}V、参考CONDITIONAL|
|走行質量|凍結B0を一度だけ置換、1043.888888889+M_T08|参考CONDITIONAL。実車脱着実測ではない|
|モデルDC|同じ旧460速度×2Crr、凍結核|約.412579/.413590%は参考CONDITIONAL|
|T09既知小計差|q→活物質→面積/厚み→箔/膜/液|約9.722608/5.977891kgは参考CONDITIONAL。完成pack NULL|

T08はM=E_g/V[1/(q u f_p)+r_NP/(q_n f_n)]+F+δの簡略会計である。E_g=20000Whとusable18000Whを混同せず、セル容量和と端子容量を区別する。保持率/ICEを二重に掛けず、運転者55kgや基準packも二重計上しない。算術を正しくするための条件であって、入力の実用適格性を保証するものではない。

F=34kgを両側共通に加えると絶対質量差からは相殺されるが、絶対走行質量・DC率の分母から消えるわけではない。追加非共通部材の差は別途δに入る。従って具体bがq依存であること、具体DC率がqだけでなく残余質量・固定物理にも依存することを保持する。

## 4　連続入力・T09にしても消えない依存

Step2 scripts/path2_analysis.pyはT08 SCENARIOSからqLP/qSを直接読む。49点q走査はこの二値を端点とし、81点u/V格子はqSを固定してLP基準との差を取る。固定部材17/34/51kg、相殺前後の追加部材probeも同じ参照qを使う。運転条件層別とgroup区間は同じq由来の質量差と基準電力量から計算される。新しい材料独立の確率的証拠ではない。

T09も同じ逆算qを使い、固定担持では面積、固定面積では必要担持・厚みに伝達する。共通162条件のqLP/qS、密度4458/2200、膜・液仕様、担持.1kg/m²、空隙.25等は対象材料の実測セットではない。密度にはNMC622等からの移用、液には別製品の参照が含まれる。T09は面積依存性を明示するが、Chen入力を独立に適格化しない。

T09_MASS_PROBEのDCは、T09完成packを走行質量へ実装したものではない。既知差bをT08参照走行質量へ置いた感度probeであり、T09未知BOMはNULLのままである。T08とT09を同じ精度の完成品として直接順位付けしない。

低担持の整合性も別に確認した。原著の1–2mg/cm²を維持しT09のAl15µm・密度2699kg/m³、膜面密度.013275kg/m²を仮定すると、LP/SそれぞれでAl+膜だけが19kgを超えた（evidence/LOW_LOADING_COMPATIBILITY.csv）。これは仮定の組合せの不整合であり、原著foil仕様や全ての高担持再設計が不可能という主張ではない。S-200の名称に含まれる200mgは処理用硫黄源の量であり、実パックの追加硫黄質量へそのまま変換しない。

## 5　Chen具体値を採用しなくても保持できる主分析

第一に、正の定義域・他条件固定のT08記号式の微分である。設計依存部材Dを加える場合はその微分も必要であり、q/u/Vを現実に独立操作できることの証明ではない。

第二に、同一部材境界の恒等式ΔM=b−δである。δ=bは定義的ゼロ点であり、特定材料のb=5.448kgという定量境界の科学的適格性とは区別する。

第三に、材料比容量を入力しないDC質量応答である。本Step4では460速度×2Crrで凍結核とaffine表現、1000/1250kg端点、微分を再照合した。E(m)=Σmax(a_t m+c_t,0)/ηはη>0で凸区分線形であり、下端右微分が正ならこの区間で狭義増加である。最小右微分は下/上Crrで{v['DC_material_free']['CRR_LOWER_BOUND']['min_slope_Wh_kg']:.9f}/{v['DC_material_free']['CRR_UPPER_BOUND']['min_slope_Wh_kg']:.9f}Wh/kgであった。

この計算はqLP/qSもT08のpack質量も使用しない。ただし1000–1250kgはStep2で宣言された研究probe区間であり、独立した実車妥当範囲を獲得したわけではない。保存速度、平坦、回生なし、補機/旋回除外、固定η.9・回転等価61kgというモデル条件を継承する。両比較走行質量がその区間内なら、同じ速度・物理条件におけるΔMとΔEの符号が一致する。一般的な実車省電力率はここから導かない。

## 6　採用可能な記述と禁止する記述

使用可：「材料値の実用適格性を別に留保した上で、質量会計と固定速度DCモデルにより、性能が質量・電力量へ伝達する条件、消失する条件を整理した。」

参考例として使用可：「未適格な逆算参照入力と指定仮定を用いる場合、約5.45kgの簡略質量差、約.413%のモデルDC差を得る。この値を実用材料やEVの代表効果量とはしない。」

使用不可：「Chenを根拠に材料容量の改善が確定し、完成packが5.448kg軽量化し、EVが約.413%省電力になった。」数値検算PASSは、この因果・適格性の欠落を解消しない。
''')
# Main decision document.
counts=collections.Counter(x['judgment']for x in claims)
md('STEP4_EVIDENCE_DECISIONS.md',f'''# Step 4　科学的採用判断

判定日：2026年11月4日。**Step4の採用判断を完了した。** 本台帳は、今回調べた証拠版の範囲での確定した判断である。全HOLDを解消したという意味ではない。Wordの追加編集・既存成果物の書換え・commit/push/公開は行わない。

## 1　判定規則

PASSは指定範囲の主張に必要な根拠が確認されたもの、CONDITIONALは列記された仮定・モデル条件・証拠制約を伴うもの、HOLDはその主張を確定するための根拠が不足するもの、NOT CLAIMEDは本研究の結論として主張しないものである。

数値の検算状態、科学的入力根拠、最終主張の判定、採用上の役割を独立した列にした。例えば逆算qの算術主張M-02はPASSであるが、実用入力としての主張M-03はHOLDであり、具体的境界P2-R01/R02は参考CONDITIONALである。HOLDを使う数値例を示せることは、HOLDの解除でも主材料入力としての採用でもない。

CONDITIONALにも「主モデルの解析結果」「補助統計」「入力未適格の参考例」という違いがある。CLAIM_EVIDENCE_MATRIX.csvのadoption_decisionを併読する。参考例のHOLD注記を落とした時点で採用条件を満たさない。

## 2　科学的に採用する成果

- 経路1：指定B入力の解品質・可行性、主greedyへの正改善0、統計単位と反復階層、入力別ばらつき、層別参照証拠、3診断入力の取得件数と条件付きWilson、範囲を明示したCPU計測を採用する。最適取得の改善をgreedy解品質改善へ読み替えない。
- 経路2の主分析：T08の記号的連続感度、同一部材会計のΔM=b−δ、材料値を使わない凍結DCの質量応答、および検証範囲内での質量/DCゼロ点の対応を採用する。実用材料性能を確定した結果ではない。
- T09：部材・面積方針による構造依存と未知BOMを明示する補完モデルとして採用する。対象LP/Sの全部材・完成packの外部検証完了とはしない。
- 統合：技術能力→適用→成果の媒介条件比較を方法的・考察上の成果として採用する。二経路の共通改善率、量子帰属効果、制度・市場転換の実証を採用しない。

## 3　主結果には採用しない具体値

Chen逆算q171.875/195.959596Ah/kgは主材料入力としてHOLDである。そこから得たT08質量約96.15/90.70kg、b約5.4483kg、u約.877094、V約3.193156V、モデルDC総和比約.412579/.413590%、T09既知差約9.722608/5.977891kg、49点/81点/162条件、運転層別/group区間を、確定材料値の主効果量として採用しない。

これらは「入力未適格の参考例」としてのみCONDITIONAL採用する。掲載する場合は主分析と分離し、本文・表題・注記・図・要旨・結論の全てで適格性未確認を維持する。具体値を掲載しない選択も主モデルの解析結論を損なわない。完成packの未知質量はNULLを維持する。

## 4　根拠の優先と過去判定の意味

10月23日レビュー、Stage1最終run03 T06、Stage2 run02 SCENARIOS/T07/T08、T09受入記録を直接確認した。いずれも数値実行と科学的採用を分け、対象材料のHOLDを保持する。過去判断の実体は用途適格性の採用保留であり、論文の一般的棄却でも算術失敗でもない。

補正済みStep3のCHEN_2020_ADOPTION_CORRECTIONは上流と整合するため採用区分に反映した。Word統合版にこの序列が不十分な箇所があるため、その原稿全体の無修正科学採用はHOLDとした。既存版の完了報告やファイル更新時刻を、入力適格性に優先させていない。

## 5　主張別の確定判定

全{len(claims)}主張：PASS {counts['PASS']}、CONDITIONAL {counts['CONDITIONAL']}、HOLD {counts['HOLD']}、NOT CLAIMED {counts['NOT CLAIMED']}。件数は科学的成果の大小を表さない。根拠パス・SHA256・適用条件・使用可能文・禁止文・追加検証条件はCLAIM_EVIDENCE_MATRIX.csvを正本とする。

'''+ '\n\n'.join(f"### {x['claim_id']}　{x['claim']}\n\n判定：{x['judgment']}。採用判断：{x['adoption_decision']}。\n\n根拠："+'、'.join(Path(f).name for f in x['evidence_files'].split(';'))+f"（実在パス・SHA256・行条件は台帳）。\n\n適用条件：{x['applicability_conditions']}。\n\n論文使用可能文：{x['usable_thesis_expression']}\n\n追加検証の扱い：{x['unresolved_handling']}。"for x in claims))
md('UNRESOLVED_ISSUES.md','''# 未解決事項と追加検証の必要性

全HOLDの解消は今回の完了条件ではない。追加検証の「不可欠」は、特定の拡張主張を採用するために必要という意味であり、現在の限定主張を成立させるために無条件で追加実験を要求する意味ではない。

現在採用した主張の範囲を守れば、以下の科学的HOLDは限界として保持できる。主材料入力の確定、完成pack/実EV/量子帰属、全460最適参照、公平な性能順位を新たに断定する場合には、それぞれ指定した証拠が不可欠である。これらを断定したまま限界節だけにHOLDを置くことは認めない。

Word版の分類不整合U13は別である。その版を正式な研究原稿として使用する前に、主分析/参考/HOLDの序列を一貫して反映する必要がある。今回は追加編集禁止のため判定のみを確定し、Wordを変更しない。

'''+ '\n\n'.join(f'## {a}　{b}\n\n対象主張：{c}。\n\n追加検証が不可欠となる範囲：{d}。\n\n今回の扱い：{e}。\n\n必要な証拠：{f}。\n\n禁止：{g}。'for a,b,c,d,e,f,g in issues)+'\n\n既存道路受入とT09 row183全面対向条件の不適合を保持する。今回の4区分は科学的主張の採否であり、既存FAIL記録を削除したりPASSへ読み替えたりしない。')
md('STEP4_FINAL_REPORT.md',f'''# Step 4 最終報告

**STEP4 COMPLETE：科学的な採用判断を確定した。** 全HOLD解消や原稿提出完成を意味しない。対象は既存分析の証拠評価であり、Wordの追加編集は実施していない。

## 採用可能な研究成果

1. 経路1の有限保存cohortにおける解品質・可行性・主greedy非改善、参照証拠の層別、追加小規模統制の取得件数と条件付き区間、CPU時間の指定scopeを採用する。量子優位性と一般的不可能性は採用しない。
2. 経路2の主成果として、記号的な質量感度、同一部材会計の相殺・逆転条件、材料入力を使わない固定速度DC質量応答と検証範囲内の符号対応を採用する。T09は構造依存・未知BOMの補完として採用する。
3. 二経路の技術能力・適用・成果の区別と媒介条件比較を、条件を明示した方法的貢献として採用する。社会技術システム全体の転換を実証したとはしない。

## Chenの過去判断と具体値の扱い

原著内報告と逆算算術は確認できたが、実用材料入力としての適格性は未確認である。過去の機械可読判定はREJECTEDではなくHOLDであり、T07/T08のstatus PASSとは別にscientific_adoptionがALL_HOLD/HOLDとなっている。

逆算qからの約5.448kg、.877094、3.193156V、約.413%、T09約9.72/5.98kg、連続格子と運転層別は、入力未適格の条件付き参考例としてのみ採用する。主たる代表材料効果量としては不採用である。数値的に正しいことから科学的採用を推定しない。

## 今回の検証

保存データと材料非依存DCの軽量検算を{v['checks']:,}項目実施し、不一致{v['failures']}件であった。43,276という検査数は独立標本数ではない。全460速度×2Crrで、材料qを使わないDC核/affine/端点/正の微分を照合した。新規の量子学習、SUMO、solver、材料/実車実験は0件である。入力根拠のHOLDは数値検算では解消しない。

## 残存HOLD

主材料q/fullcell適格性、T09未知BOM/対象材料実証、未証明46と保存MIP41外部証明、旧予算・未見学習、H_plan/全工程時刻、QPU、量子材料への帰属、道路/実車/モデル対象外物理が残る。これらは採用済みの限定的主張では研究限界として保持でき、拡張主張へ昇格させる場合に追加検証が不可欠である。

Step3 Wordの無修正採用はHOLDである。科学的判定を反映する表現・採用役割の是正が、将来その版を使用する前に必要となる。これは科学的採用判断が未完了という意味ではなく、今回禁止された原稿編集が未実施という意味である。

## 判定台帳と作業終了

主張{len(claims)}件：PASS {counts['PASS']}、CONDITIONAL {counts['CONDITIONAL']}、HOLD {counts['HOLD']}、NOT CLAIMED {counts['NOT CLAIMED']}。各行に実在パス・SHA256・適用条件・採用判断・論文で使用可能な文を記録した。

保存先：{O}。

要求5ファイルを作成した。保全照合はevidence/PRESERVATION_FINAL.json、完了チェックはevidence/STEP4_COMPLETION_AUDIT.jsonを参照する。既存Step3成果物・Word・元データは変更しない。原稿編集や追加研究には進まず、Step4の終了をもって作業を停止する。
''')
md('README.md',f'''# Step4 科学的採用判断の確定

保存先：{O}。

要求成果物はSTEP4_EVIDENCE_DECISIONS.md、CLAIM_EVIDENCE_MATRIX.csv、MATERIAL_INPUT_PROVENANCE_AUDIT.md、UNRESOLVED_ISSUES.md、STEP4_FINAL_REPORT.mdである。

最初にSTEP4_FINAL_REPORT.md、次に材料来歴監査と主張CSVを参照する。CSVは数値検算、科学的入力根拠、最終4区分、主分析/参考の採用役割、論文使用可能文を分けている。HOLDを解除せず参考例を保持したことを、確定入力の採用と読まない。

一次証拠のパス/ハッシュはevidence/SOURCE_LEDGER.csv、依存グラフはevidence/MATERIAL_DEPENDENCY_GRAPH.csv、検算はevidence/VERIFICATION_RESULT.jsonとVERIFICATION_CHECKS.csv、2版のStep3差はevidence/STEP3_VERSION_CONFLICTS.mdへ記録した。原著PDFのbyte同一コピーと再抽出本文もevidence内へ保存した。アクセス制限による今回のオンライン取得不成功と、既存保全原著の確認を区別する。

本Step4で科学的採否を確定した。Wordの追加編集、既存成果物への書込み、commit/push/公開/外部送信は行わない。HOLDの解消や次段階の原稿編集へ継続せず、本Step4で終了する。
''')
csvout('evidence/SOURCE_LEDGER.csv',source)
(O/'evidence/DECISION_COUNTS.json').write_text(json.dumps(dict(total=len(claims),counts=dict(counts)),ensure_ascii=False,indent=2))
print('decisions',len(claims),dict(counts),'sources',len(source))
