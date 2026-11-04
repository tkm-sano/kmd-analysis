from common import *
import textwrap

def md(n,s):text(n,textwrap.dedent(s))
def mtable(df,cols):
 def fmt(v):
  if pd.isna(v):return 'NULL'
  if isinstance(v,(float,np.floating)):return f'{v:.7g}'
  return str(v).replace('|','/')
 return '|'+ '|'.join(cols)+'|\n|'+ '|'.join(['---']*len(cols))+'|\n'+'\n'.join('|'+ '|'.join(fmt(v) for v in row)+'|' for row in df[cols].itertuples(index=False,name=None))
def evid(id,path,condition,classification,experiment,numeric,statistics,scope,uncertainty,limitation,status,origin):return dict(claim_id=id,path=path,condition=condition,classification=classification,experiment=experiment,numerical_evidence=numeric,statistical_evidence=statistics,target_scope=scope,uncertainty=uncertainty,limitation=limitation,status=status,origin=origin)

def main():
 t=time.perf_counter();ex=frame(O/'EXACT_REFERENCE_STATUS.csv');imp=frame(O/'EXACT_REFERENCE_IMPACT_DETAILS.csv');bounds=frame(O/'EXACT_REFERENCE_BOUND_COMPARISON.csv');stat=frame(O/'PATH1_STATISTICAL_RESULTS.csv');un=frame(O/'PATH1_UNCERTAINTY_INTERVALS.csv');ctrl=frame(O/'QAOA_CONTROLLED_CELL_SUMMARY.csv');fit=frame(O/'QAOA_CONTROLLED_EXPERIMENT_RESULTS.csv');runtime=frame(O/'PATH1_RUNTIME_SUMMARY.csv');su=frame(O/'PATH2_SENSITIVITY_SUMMARY.csv');ops=frame(O/'PATH2_OPERATION_CONDITION_ANALYSIS.csv');ci=frame(O/'PATH2_GROUP_SENSITIVITY_INTERVALS.csv');bg=js(O/'evidence/EXACT_BASELINE_SUMMARY.json');newids=ex[(ex.old_exact_available==False)&ex.exact_fraction.ne('')].problem_id.tolist();remaining=ex[ex.exact_fraction.eq('')];qctrl=ctrl[(ctrl.problem_id=='R1_020')&(ctrl.method=='QAOA')];endpoint=su[(su.model=='T08')&(su.case_id=='Q48')];mainstat=stat[stat.primary_comparison];qaoarun=js(O/'evidence/QAOA_MAIN_RUN.json');p2run=js(O/'evidence/PATH2_ANALYSIS_RUN.json');checks=[]
 for p in sorted((O/'evidence').glob('*_CHECKS.csv')):
  d=frame(p)
  if len(d) and 'status' in d:checks.extend(d.to_dict('records'))
 # Evidence matrices distinguish tautological definitions, model theorems, and observations.
 p1=[]
 p1.append(evid('P1-D01','path1','DeltaJ>0 iff JC>JQ','必要十分条件','PATH1_METRIC_SPECIFICATION (Step1)','Definition; unit seconds; exact Fraction epsilon0','not an empirical discovery','same input/objective/constraints','none within definition','does not establish actual operation contribution','PASS','definition'))
 p1.append(evid('P1-N01','path1','positive probability of sampling some feasible route with J<JC is necessary for finite-shot improvement','必要条件','QAOA_MEASUREMENT_BUDGET_SENSITIVITY.csv','P(improve at least once)=1-(1-p)^shots','conditional independent draws from fixed simulated state','fixed input, fitted state, shot budget','state numerical precision; training variability separate','support availability alone is insufficient; finite-shot success not guaranteed','CONDITIONAL','sampling-model derivation'))
 p1.append(evid('P1-O01','path1','no positive improvement vs preregistered greedy in saved B cohort','観測された依存関係','PATH1_STATISTICAL_RESULTS.csv;PATH1_PAIRED_COMPARISONS.csv','0/36800; all460x8x10 saved-best plans feasible','input-first estimates; per-fit Wilson and group/measurement resampling in uncertainty CSVs','B no windows, R4=100; finite input+fit cohort','bootstrap zero-event degeneracy; conditional upper bound separate','unmatched current budgets; no learning stability inference','PASS','existing-data analysis'))
 for cfg in ['GROVER_P2','GROVER_P3']:
  rr=mainstat[(mainstat.config_id==cfg)&(mainstat.scale=='R5')].iloc[0];cc=un[(un.config_id==cfg)&(un.scale=='R5')&(un.classical_method=='ITERATED_GREEDY_ADJACENT_SWAP')&(un.metric=='mean_delta_J_s')&(un.kind.str.startswith('GROUP'))].iloc[0]
  p1.append(evid('P1-O02' if cfg.endswith('P2') else 'P1-O03','path1',cfg+' large-scale worsening','観測された依存関係','PATH1_STATISTICAL_RESULTS.csv scaleR5 '+cfg,f"N70,700 measurement reps; meanDeltaJ={rr.input_mean_delta_J_mean:.12g}s; inputSD={rr.input_mean_delta_J_sd:.12g}s; IQR={rr.input_mean_delta_J_iqr:.12g}s",f"hypothetical group sensitivity95=[{cc.lower95:.12g},{cc.upper95:.12g}]s",'125 customers, saved CPU simulator and original budget','25-source-group exchangeability hypothetical; no size-only causal attribution','not QAOA general inferiority; different supports/initials/fit budgets','CONDITIONAL','existing-data analysis'))
 p1.append(evid('P1-S01','path1','mirror orbit optimum equals initial and JC<=initial => DeltaJ<=0 for any output within this orbit','必要十分条件','PATH1_SUPPORT_AUDIT.csv; exact matching-chain DP','460/460 support minima equal initial; five saved mirror configurations','exact dynamic programming, independently checked by enumeration on n<=5','specified mirror matching orbit, all B inputs','exact finite-decimal input convention','sufficient condition for non-improvement, not global optimum or all mixer claim','CONDITIONAL','model theorem plus new exact support verification'))
 p1[-1]['classification']='観測された依存関係';p1[-1]['origin']='derived sufficient non-improvement condition verified by exact support DP'
 p1.append(evid('P1-S02','path1','active three-point grid selected initial t=0 in all460 inputs','観測された依存関係','PATH1_SUPPORT_AUDIT.csv; active raw RESULT','460/460 selected_t0; six total configs including mirror show initial output','not independent retraining','fixed t={0,.5,1} grid','larger angle search untested','does not prove all active-swap QAOA cannot improve','CONDITIONAL','source/readback audit'))
 for layer in [1,2]:
  z=qctrl[(qctrl.support=='FULL_PERMUTATION')&(qctrl.initial_state=='BASIS_INITIAL')&(qctrl.mixer=='GRAPH_SWAP')&(qctrl.layers==layer)].iloc[0]
  p1.append(evid(f'P1-C0{layer}','path1',f'R1_020 full-support basis graph p{layer} optimal attainment','観測された依存関係','QAOA_CONTROLLED_CELL_SUMMARY.csv',f"{z.primary_optimal_rep0_count}/97 primary independent-fit reps; meanDeltaInitial={z.mean_delta_J_initial_s:.12g}s",f"Wilson95=[{z.primary_optimal_Wilson95_lower:.12g},{z.primary_optimal_Wilson95_upper:.12g}]",'one diagnostic 4-customer input,64 COByLA eval cap,8192shots','independent optimizer starts; exact expectations; method-specific local optimization','not large-scale result or quantum advantage; saved greedy already globally optimal','CONDITIONAL','new controlled experiment'))
 p1.append(evid('P1-C03','path1','full support does not ensure acquisition; basis-projector p1 vs uniform-projector','観測された依存関係','QAOA_CONTROLLED_CELL_SUMMARY.csv R1_020','basis projector p1=0/97; uniform projector p1=97/97 optimal rep0','Wilson95 zero=[0,.0380935], all=[.9619065,1]','same full support, projector, layer1, eval/shot budgets','random-start distribution and deterministic optimizer fixed; input selected by baseline gap','does not imply every warm start or all projectors fail','CONDITIONAL','new controlled experiment'))
 p1.append(evid('P1-C04','path1','same-angle dephasing changes expected cost but need not improve sampled-best vs greedy','観測された依存関係','QAOA_SAME_ANGLE_DEPHASING.csv; QAOA_CONTROLLED_CELL_SUMMARY.csv','4656 same-angle Q states; new greedy improvements0/46560 Q measurement reps','96cell97learningx10measurement; all cells retained','chosen3 inputs,exact feasible-subspace CPU simulation','state expectation and sampled-best are distinct estimands','coherence diagnostic is not practical algorithm or QPU advantage','CONDITIONAL','new controlled experiment'))
 p1.append(evid('P1-T01','path1','tau_total<=H_plan required for deadline adoption','必要条件','PATH1_RUNTIME_RESULTS.csv;PATH1_RUNTIME_SCOPE_COMPARISON.md','9603 new pipeline timing records; H_plan=NULL','97 repeated fits per method/cell;291 new greedy timings','common provided initialization; CPU only','imports/initial construction/transfer/QPU queue not included; output counts differ classical vsQ','H_plan numerical threshold and operational total latency unverified','HOLD','definition plus measured timing scope'))
 p1.append(evid('P1-H01','path1','remaining exact references unavailable','未検証事項','EXACT_REFERENCE_STATUS.csv;EXACT_REFERENCE_BOUND_COMPARISON.csv','46 unproved; audited references414,including41 conditional saved MIP equality','no imputation; exact metrics use414; legacy407 separate','B n100/125 missing references','saved SCIP bound tiny gap; independent LP can be weaker','numerical closeness is not an exact optimum','HOLD','exact-reference audit'))
 p2=[]
 p2.append(evid('P2-D01','path2','DeltaM=b-delta; within verified positive-slope interval DeltaE>0 iff delta<b','必要十分条件','PATH2_BOUNDARY_ANALYSIS.csv;PATH2_OPERATION_CONDITION_ANALYSIS.csv','all920 trajectory/Crr cases positive derivative on[1000,1250]kg; min=.827572647958Wh/kg','deterministic convex piecewise-linear kernel, not statistical inference','mass substitution only; same trajectory/Crr/eta/other physics','exact branch selection; numerical kernel tolerance1e-7Wh verification','not sufficient for real material or practical delivery contribution','CONDITIONAL','model theorem plus new verification'))
 p2.append(evid('P2-B01','path2','T08 default added S-minus-LP mass cancels at b','必要十分条件','PATH2_BOUNDARY_ANALYSIS.csv;PATH2_SENSITIVITY_RESULTS.csv','b=5.448297415076934kg; delta=b yields zero DC in920 paired cases','deterministic mass arithmetic and frozen-kernel check','gross20kWh,V3.5,u1,common34kg,NP1.1,fp.75,fn.98,qn360','1e-14kg float-order difference from old5.448297415076922kg','extra material categories cannot overlap accounted coatings/fixed parts','CONDITIONAL','existing boundary independently regenerated and extended'))
 p2.append(evid('P2-B02','path2','same V/common components/no added mass: qS*u>qLP iff positive mass saving','必要十分条件','PATH2_BOUNDARY_ANALYSIS.csv','u*=.8770940719841043 at qS195.959596/qLP171.875','deterministic formula','T08 same average full-cell voltage and all common negative/fixed inputs','u is assumed extra full-cell utilization, not measured retention','does not prove this utilization is realizable','CONDITIONAL','model derivation'))
 p2.append(evid('P2-B03','path2','S full-cell voltage threshold with LP baseline held at3.5V','必要十分条件','PATH2_BOUNDARY_ANALYSIS.csv','V*=3.193155683779789V at qS,u1,extra0','deterministic formula includes negative mass change withV','T08 fixed34kg and original controls','mean full-cell voltage is a design assumption','not voltage window vs Li or cell measurement','CONDITIONAL','model derivation plus sensitivity'))
 for _,z in endpoint.iterrows():
  cc=ci[ci.rolling_case==z.rolling_case].iloc[0]
  p2.append(evid('P2-E01' if z.rolling_case=='CRR_LOWER_BOUND' else 'P2-E02','path2','default T08 transmission '+z.rolling_case,'観測された依存関係','PATH2_SENSITIVITY_SUMMARY.csv caseQ48',f"460 trajectories; DeltaE_sum={z.delta_sum_Wh:.12g}Wh; weighted={z.total_weighted_saving_percent:.12g}%; individual mean={z.mean_individual_saving_percent:.12g}%; SD={z.sd_individual_saving_percent:.12g}pp; range=[{z.min_individual_saving_percent:.12g},{z.max_individual_saving_percent:.12g}]%",f"hypothetical25group sensitivity95=[{cc.lower95:.12g},{cc.upper95:.12g}]%",'old C saved trajectories; no regen/aux/grade/payload changes','model input/structure/BOM uncertainty is separate; no probability assigned','model result, not measured DC or quantum-produced material improvement','CONDITIONAL','saved trajectories plus new model readback'))
 p2.append(evid('P2-S01','path2','known-component boundary depends on area/loading accounting','観測された依存関係','PATH2_T09_COMMON_INPUT_SENSITIVITY.csv;Step1 T09 pair linkage','fixed_loading B015 b9.722608121107783kg; fixed_area B051 b5.977891152148871kg;162 common-input cases','deterministic geometry/control grid','same gross,V,u,q,NP/fractions; known components only','unknown casing/tabs/foil margins/pack structure retained NULL','not comparison of two completed packs or empirical T08 validation','CONDITIONAL','new common-input structural sensitivity'))
 p2.append(evid('P2-O01','path2','mass-DC transmission varies across saved motion profiles and Crr','観測された依存関係','PATH2_OPERATION_CONDITION_ANALYSIS.csv;PATH2_OPERATION_STRATA.csv','460 paired trajectories x2Crr; W1/W3 plus positive-branch correction','covariate quartiles fixed by covariates only; group dependence retained','observed saved windows; old C distinct from B','distance/restarts/speed correlate with parent/scale; no causal adjustment claim','not intervention effect of real driving style','CONDITIONAL','new stratified descriptive analysis'))
 p2.append(evid('P2-A01','path2','Controlled-DC excludes regen/aux/grade/turn/payload variation','モデル上の仮定','frozen model JSON and kernel; PATH2_ANALYSIS_PROTOCOL.md','eta.9; rotational equivalent61kg; same saved1s trajectories','49/81 grids are deterministic coordinates, not independent experiments','only specified energy boundary','terminal unobserved interval not imputed','does not estimate all terminal battery energy in actual service','CONDITIONAL','frozen assumptions'))
 p2.append(evid('P2-H01','path2','quantum material improvement to practical pack and real-road service','未検証事項','UNRESOLVED_ITEMS.md','complete T09 pack NULL; LP/S proxies andV/u assumed','no experimental material or real-vehicle validation in this trial','upstream and downstream causal links outside current quantitative evidence','unknown material qualification and BOM; regional network acceptance remains deficient','do not assert real-world quantum contribution','HOLD','research boundary'))
 table('PATH1_CONDITION_EVIDENCE_MATRIX.csv',p1);table('PATH2_CONDITION_EVIDENCE_MATRIX.csv',p2);table('CONTRIBUTION_CONDITION_TABLE.csv',p1+p2)
 claims=p1+p2+[evid('F01','cross','arbitrary0.25% reduction as success criterion','未検証事項','researcher fixed policy','not adopted','not applicable','all paths','none','would contradict zero-effect-boundary research design','FAIL','rejected interpretation'),evid('F02','cross','CPU simulator timing interpreted as QPU execution or speedup','未検証事項','ENVIRONMENT.json and runtime scope','QPU execution false','not applicable','all route results','compiled/physical resources unknown','unsupported conversion','FAIL','rejected interpretation'),evid('F03','cross','T09 absolute known subtotal treated as complete measured pack','未検証事項','PATH2_T09_COMMON_INPUT_SENSITIVITY.csv','all completed masses NULL','not applicable','material path','unknown BOM','invalid accounting/measurement interpretation','FAIL','rejected interpretation')];table('CLAIM_EVIDENCE_MATRIX.csv',claims)
 # Task2-1 reports.
 md('EXACT_REFERENCE_FAILURE_AUDIT.md',f'''
 # 厳密参照53入力の終了理由監査

 判定：原因の実装上の意味と保存数値対応は確認。新規独立証明7、残り46はHOLD。

 元実装は`W/FINAL_SOURCE_SNAPSHOT/scripts/run_unified_no_windows.py`のreference()およびrun_exact_references.py。SCIPがoptimalを返し、書出しsolutionから全顧客一巡回路を抽出しても、独立目的値UとExact Dual Bound LがFractionで一致しない場合、`EXACT_BOUND_WITNESS_MISMATCH`で停止する。これはtime limitや求解不能の同義語ではない。

 53件全て：R4=21/R5=32、同じSCIP10.0.3 binary SHA `{bg['binary_hashes'][0]}`、optimal状態、timeout false。LP全有向arc・0基準索引・デポ・係数をNPZへ照合し一致。solutionヘッダの目的値は経路のFraction総和および係数annotationと一致した。一方、同実行ログのExact Primal=Exact Dualとsolution目的の差は{bg['mismatch_min_s']:.12g}〜{bg['mismatch_max_s']:.12g}秒、refined保存witnessとの差は{bg['refined_gap_min_s']:.12g}〜{bg['refined_gap_max_s']:.12g}秒。

 boundはSCIPの緩和/探索木が与える最小化下界、witnessは入力上の可行巡回路による上界。source writerはDecimal(str(float64))をLP係数に用い、検査はFractionで行った。float許容差で等価と昇格していない。旧SOURCE/FINAL_SOURCEの停止条件は同じで、版間のその条件差が原因とは確認されなかった。異なる版のソルバを使った53群ではない。

 独立SoPlex8.0.3で保存最終LPの連続緩和を再求解した。初回default toleranceでは非ゼロ残差が残るため証明として不採用。-f0/-o0で有理数双対を得て、degree/horizon/有効subtour制約と変数0..1から `L=sum(y*b)+sum(min(0,c-A^Ty))` をFractionで独立検証した。値が上界と厳密一致した場合のみ新規最適証明とした。

 pilotのR4_009では整数だが複数subtour、R5_001では分数LP解を確認した。厳密mincutで有効SECを追加したpilotも、分数DFJ緩和または上限で停止した。したがって「ログ表示の丸めだけ」と断定できず、元コードは微小な未解決差を認識して停止する一方、書出し解が一巡回路であれば追加SECを打たないという限界がある。SCIP内部の有理数primalと書出し経路の不一致を完全に特定したとは主張しない。

 共通特徴はevidence/EXACT_INPUT_FEATURES.csv/FEATURE_COMPARISON.csv。大規模で微小係数/近接費用が存在するが、証明済み群にも同様にあり、単一の入力特徴だけで失敗を説明できない。根拠のない原因を補完しない。

 実行前仕様・段階判断はEXACT_RECHECK_PROTOCOL.md、全CLI/LP/primal/dual/資源はexperiments/exact_*。148件（既存large95＋欠測53）を独立検査し、61件で独立LP下界と巡回路の等値を得た。この61は新規7と既存54の合計であり「61新規入力」ではない。53件の大規模branch-and-boundを無条件には投入せず、必要な境界監査を完了した。
 ''')
 md('EXACT_REFERENCE_IMPACT.md',f'''
 # 厳密参照と統計への影響

 新規証明：{', '.join(newids)}。元407参照への反例は0。受入参照は414（R0/R1/R2/R3各78、R4=59、R5=43）、未証明46（R4=19/R5=27）。旧407の統計もEXACT_REFERENCE_STATISTICAL_IMPACT.csvに別保存した。

 証拠クラスを分離：234件は今回全順列再列挙、78件は保存exact-integer Held–Karp DPと独立witness照合、61件は今回の有理数LP双対一致（既存54＋新規7）、41件は保存SCIP exact MIP下界とwitnessの一致を保持する条件付き参照（外部VIPR未実施）。独立LPがMIPより弱いことだけで旧41件を無効化しない。新たな可行上界が旧最適値未満となる反証はなかった。

 残り46の保存SCIP下界を含む最良利用可能gap上限の最大は{bounds[~bounds.new_exact_available].best_available_gap_upper_s.max():.12g}秒。一方、独立に検算したLP緩和だけでは最大{bounds[~bounds.new_exact_available].independent_LP_gap_upper_s.max():.12g}秒と弱くなる。両者はEXACT_REFERENCE_BOUND_COMPARISON.csvで別列・証拠クラスを保存している。微小gapでも最適値を推測で埋めない。

 主ΔJ（JC−JQ）は最適値に依存しないため全460入力で評価可能。gap/最適一致は414入力だけ、46はNULL。元36,800行中、新参照に接続する量子計画は414×8×10=33,120行（古典2対照を展開したCSVでは倍の行数になる）。7入力追加で分母が変わる影響を別表にした。零許容の最適一致は微小十進差にも敏感で、実務的に有意な秒差と同一視しない。
 ''')
 # Task2-2 reports.
 quality=mainstat[(mainstat.scale!='ALL')&mainstat.config_id.isin(['MEAN_P2','GROVER_P2','GROVER_P3'])].copy();quality=quality.rename(columns={'input_mean_delta_J_mean':'mean_DeltaJ_s','input_mean_delta_J_sd':'input_SD_s','input_mean_delta_J_iqr':'input_IQR_s'})
 md('PATH1_STATISTICAL_REPORT.md',f'''
 # 既存B系列：統計結果

 460入力・8設定・1fit/入力設定・10測定rep・36,800保存計画を元NPZと測定JSONへ照合。全保存bestが可行。旧A/Cを混合せず、R4=100顧客。主JCはgreedy adjacent、第二対照はrandom swapで別に集計した。主対照の正改善は0/36,800。初期解との差を主ΔJへ代用していない。

 主対照に対する代表設定の規模別結果（input内10rep平均→input等重み）：

 {mtable(quality,['scale','config_id','physical_inputs','valid_reps','mean_DeltaJ_s','input_SD_s','input_IQR_s','improve_percent','exact_inputs','mean_quantum_gap_percent','optimal_match_percent'])}

 全8設定×6規模＋ALL×2古典対照はPATH1_STATISTICAL_RESULTS.csv（112行）。量子・古典対応73,600行、input設定対照7,360行を別CSVに保存。平均/median/sampleSD/IQR/min/maxは入力平均の分布と全測定行の記述を別列にした。後者を独立標本数として推測しない。原repのばらつきはwithin_measurement_sd、入力間ばらつきはinput_mean_*_sdである。

 mirror5とactiveは保存初期解と同等だが、greedyが初期を改善した入力では主対照より悪い。新しい独立matching-chain DPで全460のorbit最小値=初期を確認し、これは支持内で初期より良い解がないことによる不成立条件と対応する。activeは限定3点gridでt0選択。GroverはR0〜R2でgreedyと同等、R3〜R5で悪化する保存条件だった。規模・支持・初期・予算・backendが同時に変わるため規模だけの因果効果とはしない。

 最適参照は監査後414。旧407のgap/一致率と監査後値はEXACT_REFERENCE_STATISTICAL_IMPACT.csv。欠測46は埋めず、R4/R5の欠測層を明示する。raw-shot invalid count未保存の行はNULL、保存bestの可行率100%でraw-shot可行率を埋めない。

 図はPATH1_STATISTICAL_FIGURESの品質差、改善率、gap分布、対応比較、測定SD（小規模拡大を追加）。全て保存CSVから再作成可能。図の線や群間差を量子優位性の証拠へ読み替えない。
 ''')
 md('PATH1_UNCERTAINTY_ANALYSIS.md','''
 # 経路1：不確実性の解釈

 PATH1_UNCERTAINTY_INTERVALS.csvに672区間を保存。主推定対象は保存された固定input/fitの平均ΔJまたは測定取得率。測定repの10,000回復元抽出は各input/fit内で行い、入力や親を独立に増やさない。25需要groupの10,000回復元抽出は同じgroup内のparent/input/設定/repをまとめる。前者は固定学習状態の測定乱数、後者は仮想的な需要group母集団への感度である。

 group間独立・交換可能性は実世界の確率標本から保証されていない。group区間は実配送の校正済みCIではなく、数値モデル誤差や材料不確実性も含まない。規模ALLでは460入力等重み、6規模等重みではない。元seed20261102/20261104、percentile95、有効cluster数、undefined数を保存した。

 改善観測0件をbootstrapすると[0,0]に退化する。これは将来改善確率0の証明ではない。input別0/10のWilson95上限は約27.75%。補助PATH1_ZERO_SUCCESS_FIXED_FIT_BOUND.csvでは、全fitを固定し測定stream間が独立と仮定した平均取得確率の片側上限を式から示す（ALL各設定4600batchで約0.0651%）。この強い条件付き上限を独立学習や未見入力へ適用しない。

 旧10repは同じ学習済みfitからの8192shots反復である。パラメータ学習の不安定性は旧主cohortから推定できない。新規97学習seedは3診断入力のexact期待値最適化・ランダム初期角という別の実験であり、旧cohortや実機学習へ移植しない。

 多重検定・p値による選択は行っていない。全8設定と2古典対照を報告し、主要比較greedyと第二比較randomを区別する。信頼区間がゼロを含まないことだけで量子優位や実運用寄与を認定しない。
 ''')
 # Task2-3.
 md('QAOA_CONTROLLED_EXPERIMENT_REPORT.md',f'''
 # 追加QAOA統制実験結果

 事前仕様QAOA_CONTROLLED_EXPERIMENT_DESIGN.mdに基づき、3診断入力×支持2×初期2×mixer2×layer2×方法2=96cell、97独立学習start/cell、各10測定rep×8192shotsを実施した。合計9,312fit（QAOA4,656/DEPHASED4,656）、93,120測定rep。pilot288fitは別stream・主集計外。main wall={qaoarun['wall_s']:.3f}秒、プロセスCPU={qaoarun['CPU_s']:.3f}秒。CPUの厳密順列部分空間モデルで、元staged8の再実行でもQPU実行でもない。

 97は最適取得率のprimary rep0に対する95% Wilson最大半幅0.10の精度から設定した。97×10を独立学習と数えない。学習seedはoptimizer初期角、測定seedは8192shot categorical抽出の別stream。同じ学習startを2方式で対応させ、それぞれ別に64評価上限で最適化した。exact期待値を用いるため学習時のshot noiseは扱わない。

 R1_020（4顧客、初期非最適）におけるQAOA結果：

 {mtable(qctrl,['support','initial_state','mixer','layers','primary_optimal_rep0_count','independent_learning_fits','primary_optimal_rep0_rate','primary_optimal_Wilson95_lower','primary_optimal_Wilson95_upper','mean_delta_J_initial_s','mean_delta_J_greedy_s'])}

 保存greedyは選択3入力で既に厳密最適のため、主ΔJの正改善は定義上不可能である。この負条件を保持した。R1_020のmirror支持は最適を含まず、full支持でもbasis-projector p1は0/97、uniform-projector p1は97/97。したがってfull supportだけで有限予算の成功は保証されない。layer差は同じ評価上限の局所最適化を含む結果で、global角度最適性やlayer一般則ではない。

 raw np.stdに1e-15秒級の丸めSDが残る77fitは、保存目的分数が全反復同一であることを確認しpublic summaryをSD0へ正規化した。raw実験CSVは変更せず、evidence/CONTROLLED_SD_NUMERICAL_REVIEW.csvに差を保存。

 同じ学習角度でDEPHASEDへ置換する4,656診断はQAOA_SAME_ANGLE_DEPHASING.csv。期待目的の干渉差を確認できる条件があるが、主指標は8192shot sampled-best対greedyであり、期待値の差と同じではない。別最適化DEPHASEDとの差はQAOA_CONTROLLED_PAIRED_CONTRASTS.csv。shots1/8/64/8192の解析的感度は37,248行、同じ最終状態の再利用で新しい独立実験とは数えない。

 新結果は全cell保持。初期incumbentの保持あり/なしを別列にした。rawが悪化しても初期解保持で悪化を防ぐことは定義上の選択効果で、量子による改善ではない。全shot histogramから最短解を独立再構成し、9,312fit×10測定の保存値と照合した。direct expmと固有分解、全支持可行性も検証した。

 旧Aの3/4顧客直接比較方針に合わせ本実験は3/4顧客のみ。新mixerはgraph Hamiltonianで、旧activeの逐次parity回路と同一ではない。小規模・選択入力の結果をn25/100/125や一般QAOAへ外挿しない。事前に固定した入力のうち都合の良いcellだけを結果として選んでいない。
 ''')
 # Task2-4.
 rt=runtime[runtime.config_id.isin(['FULL_PERMUTATION/UNIFORM_SUPPORT/PROJECTOR/p2','NEW_ITERATED_ADJACENT_GREEDY64'])]
 md('PATH1_RUNTIME_SCOPE_COMPARISON.md','''
 # 時間scopeの比較

 既存3680fit、初期460、古典近似920をPATH1_EXISTING_RUNTIME_BY_SCOPE.csvでscope別に集計。mirror fitはload/model構築を除くが最適化後precision検査・state保存を含む。Grover fitは旧学習pool再利用を含み、final validation/measurementを除く。active RESULTはload・grid・2測定モード・検証・NPZ保存まで含む。これらを同じ求解時間として差し引かない。

 新規9312fitと古典291反復のraw時間はPATH1_RUNTIME_RESULTS.csv。CPUモデル/software/affinity/threadsはevidence/ENVIRONMENT.json。preprocessing、parameter optimization、simulation内数、sampling、verification、postprocessing、total wall/CPUを区別した。simulation列は目的評価中に直接計測した内数で、最終状態再評価等はoptimization残差に含む。optimizer overheadとsimulationを別の総時間へ二重加算しない。

 新QAOAとDEPHASEDは同じinput/support/initial/mixer/p/64評価/10measurementの工程比較ができる。通常の新greedyは64route評価・1計画、QAOAはexact期待値評価・10計画で作業量が異なる。同環境の記述値として示すが、総時間差を公平な1計画の速度優位へ読み替えない。小規模QAOAの状態空間列挙と固有分解は前処理に含み、greedyへ不要な列挙を課していない。

 既存共通初期経路の生成、import/起動、外部転送/QPU queueは新pipeline totalに含まれない。古典初期生成は旧scopeで別記、転送等はNULL。warmupとpilotは別ファイル、主97反復に混ぜていない。QAOA各fitはCPU affinity=maxの1thread逐次、古典はQAOA終了後同じcoreで測定。経路2計算は別coreで実行。ホスト他負荷と時刻差は残るため交互実行による厳密なspeedup試験ではない。

 tau_total<=H_planは保持。H_plan数値は未確定、帰庫32400秒を代入しない。ここで得た秒数はCPUシミュレータ/古典パイプラインの実測でありQPU時間ではない。compiled depth/gates、物理qubit、実機noise、通信時間はHOLD。
 ''')
 md('PATH1_RUNTIME_DISTRIBUTIONS.md',f'''
 # 時間分布の結果

 固定例としてFULL/UNIFORM/PROJECTOR/p2のQAOA/DEPHASEDと新greedyを示す。全96cell・方法別・入力別の平均/median/SD/IQR/min/maxはPATH1_RUNTIME_SUMMARY.csv、旧scopeは別CSV。

 {mtable(rt,['problem_id','method','repetitions','total_wall_s_mean','total_wall_s_median','total_wall_s_sd','total_wall_s_iqr','total_CPU_s_mean'])}

 単位秒。QAOA/dephasedは学習1回＋測定10rep、greedyは64route評価で1計画。全fitの分布を保存しているが、この表の時間比をQPU speedupや実運用計画時間の比としない。CPUとwallの差はスケジューラ待ち/IO等を含み得る。zeroの未実行量子hardware項は「QPUを使用していない」という記録で実機計測ではない。
 ''')
 # Task2-5.
 md('PATH2_STATISTICAL_REPORT.md',f'''
 # 経路2：感度・境界・走行条件

 C旧古典460軌跡×2Crrを対応保持し、144パラメータcase、132,480行を計算した。q49点、u9×V9=81点、共通固定部材3点、追加部材相殺3点、T09既知差のmass probe8点。全て決定論的モデル出力であり独立実験数ではない。T09共通入力構造感度は別162行。

 デフォルトT08端点：

 {mtable(endpoint,['rolling_case','trajectories','delta_mass_kg','delta_sum_Wh','total_weighted_saving_percent','mean_individual_saving_percent','sd_individual_saving_percent','min_individual_saving_percent','max_individual_saving_percent','mean_transfer_K_EM','mean_transfer_K_Eq'])}

 削減率のSDは軌跡間のpercentage points。総和比と個別率平均は別推定対象。25group感度区間は：

 {mtable(ci,['rolling_case','groups','point','lower95','upper95','resamples'])}

 この区間は仮想需要group再標本化の感度で、材料・モデル誤差・未知BOMの確率分布ではない。

 元mass式からb=5.448297415076934kg、u*=0.8770940719841043、V*=3.193155683779789Vを再現した。旧float順序値との差約1e-14kgは検算許容内。delta=bでは920対応caseのDC差も0、b±1kgでは符号反転。1000〜1250kg内で各軌跡のDC(m)はstrictly increasing、全920の最小導関数は{p2run['min_derivative_Wh_kg']:.12g}Wh/kg。質量差とDCゼロ境界の一致はこの範囲・固定物理条件に限定する。

 改善伝達率K_EM=(DeltaE/E_LP)/(DeltaM/m_LP)とqのみのK_Eq=(DeltaE/E_LP)/((q*u−qLP)/qLP)を無次元比として定義。ゼロ分母はNULL、u/Vを同時に変えたcaseへ単一材料因果効果として適用しない。端点ではK_EMの軌跡平均約0.857/0.859、K_Eq約0.0292。実材料の実現性能を推定したものではない。

 T09は固定loadingとLP固定areaで既知差bが9.722608121107783kg/5.977891152148871kgへ変わる。共通E/V/u/q/NP/fractionsで部材差を算出したが、完成packはNULLのまま。T08との絶対質量比較・実証validationには用いない。

 走行条件は距離、再発進、moving平均速度、正dv2和でquartile分布を保存。PATH2_OPERATION_CONDITION_ANALYSIS.csv/STRATA.csvを参照。W1/W3と正値化branch補正を含み、Crrはtrajectory内対応。規模/parent/需要groupの交絡を残すため、相関を運転介入の因果効果としない。旧C460を新B460へ結び付けない。
 ''')
 md('PATH2_MODEL_UNCERTAINTY.md','''
 # モデル不確実性と適用範囲

 T08主：gross20kWhから正負塗工材を設計し、cell other19kgとpack other15kgを固定、additionalを別項にする。usable18kWhは走行stockで質量設計へ代入しない。qLP171.875/qS195.959596は保持率基準逆算proxy、u/V/NP/活物質率等は仮定。保持率/ICEをuへ再度掛けない。完成パック実測値ではない。

 T09補完：positive/negative coatings,Al,Cu,separator,liquidの既知subtotal。area/loading/porosity/密度transferでbが変わる。casing/tabs/foil margins/pack structureはNULL/変数delta。19+15kgのT08固定部材をT09subtotalへ加えて残差を埋めない。T09_ROW183の全面対向FAILは維持し、追加共通入力gridへ紛れ込ませない。

 数値verification、実材料/セルのvalidation、実車DCのvalidationは別。今回の検査は凍結kernelと同一軌跡mass置換の再現、部材算術、ゼロ境界、構造感度。材料密度/電圧/利用率/形成/Li在庫/power/thermal/life/safetyの妥当性は未実証。

 独立な49実験や920実車走行ではない。trajectory間分布、parameter範囲、未知部材境界、仮想group再標本化感度を区別する。未知部材やproxyに根拠のない確率分布・CIを与えない。Crr lower/upperは凍結モデルの二設定で95%確率区間ではない。

 平坦、回生なし、補機・旋回除外、積載0、運転者55kg、rotational equivalent61kg、eta.9、dt1sを保持。区間総仕事を正値化し、massによるmask変化をbranch correctionへ入れる。末端未観測tailを0で埋めない。道路地域受入/実車外部妥当性と量子材料改善への帰属はHOLD。
 ''')
 # Cross-path summary and handoff.
 md('STEP2_CONTRIBUTION_CONDITIONS_SUMMARY.md','''
 # 寄与条件の抽出

 経路1：主greedy対照で改善0件という負結果を保持する。mirror支持最小=初期の全460確認は、支持内に改善余地がない条件を特定した。全支持は必要な改善候補を含み得るが、初期状態/mixer/layer/有限最適化/測定予算が取得を制約することを3/4顧客統制実験で示した。期待値の干渉差とsampled-bestの方式差、初期incumbent保持による悪化回避を区別する。時間・実機・実道路へ一般化しない。

 経路2：材料入力が有効容量・電圧の条件を満たしても、追加/未知部材deltaがbに達すれば質量とDC効果が消失する。凍結軌跡/物理条件と検証mass範囲では正のDC質量傾きのため、delta<b/=/ >bが成立/ゼロ/逆転と対応する。T09の幾何部材はb自体を変える。実際にその材料や完成packが成立したという証明ではない。

 いずれも個別技術の性能改善だけでは寄与を断定できない。経路1には探索支持・出力規則・計算工程・運用締切、経路2には部材会計・実用移行・走行条件が媒介する。これはEV配送を社会技術システムの一事例として検討するための定量的条件台帳であり、制度効果や実運用改善を測定したものではない。

 必要十分条件は定義/指定モデル内の同値、必要条件は経路上の成立要件、観測依存は保存cohort/診断実験の結果、モデル仮定と未検証事項は別列。詳細は両PATH*_CONDITION_EVIDENCE_MATRIX.csvとCONTRIBUTION_CONDITION_TABLE.csv。Step3の統合考察は今回完成させていない。
 ''')
 md('STEP3_HANDOFF.md',f'''
 # Step 3引継ぎ：確定結果と根拠

 独立Step2 trial。正式採用は未決定、Step3は未実行。原稿へ直接反映しない。

 1. RQ1の主要結果はgreedy対照改善0/36,800、全best可行。初期対照との差と混同しない。規模/設定/反復/入力/seedが残るPATH1_PAIRED_COMPARISONS.csvと112行summaryを使う。主JCを結果を見て変更しない。
 2. 厳密参照は414、46HOLD。新規証明7と既存証拠クラス（再列挙234・保存DP78・独立LP61・保存MIPのみ41）を併記。414全てを今回再求解したとは書かない。旧407との指標変化は専用impactCSV。
 3. mirror orbit最小=初期を全460で新DP検証。active t0選択。支持制限による不成立と最適化失敗を区別し、Grover大規模悪化をQAOA一般の劣位へ拡張しない。
 4. 新統制は3診断input×96方法cell、97learning/cell、10measurement/fit。R1_020 graph basis p1は58/97、p2は78/97、full-projector basis p1は0/97対uniform97/97。各Wilson区間とexact期待値学習の限定を示す。同角度DEPHASEDと別学習DEPHASEDを区別する。
 5. CPU時間は新9,603パイプライン記録と旧scope別表。Q/dephased工程は対応、greedy1出力とQ10出力のtotalを公平な1計画speedupとしない。H_plan、QPU/compiled/physical resourcesは未確定。
 6. T08主のb≈5.448kg、u*≈.877094、V*≈3.193156、DC総和比≈.412579/.413590%。個別率平均/SD、group感度、K_EM/K_Eqを区別。T09のb≈9.722608/5.977891kgは会計構造依存、完成packはNULL。
 7. delta=bでmass/DCが消失し、両側で反転する指定モデル内条件と、1000〜1250kgの920軌跡/Crr正傾き確認を根拠にする。範囲外・回生/補機/勾配/積載変動へ外挿しない。

 改善の定義からの同値を新実証と呼ばず、実験で確認した支持/初期/学習依存と、モデル上の感度・未接続を分離する。材料の量子由来改善と実道路運用改善は考察後段で未実証接続として扱う。全HOLD解消をStep3開始条件にせず、各主張の限定を保持する。

 参照順：EXECUTIVE_SUMMARY.md → PATH1_STATISTICAL_REPORT.md / QAOA_CONTROLLED_EXPERIMENT_REPORT.md / PATH2_STATISTICAL_REPORT.md → 条件CSV → UNRESOLVED_ITEMS.md → FINAL_AUDIT_REPORT.md。図表はFIGURE_INDEX.csvから対応CSV/スクリプトを辿る。
 ''')
 md('UNRESOLVED_ITEMS.md','''
 # 未解決事項

 |ID|HOLD内容|結論への影響・次に必要な証拠|
 |---|---|---|
 |H01|厳密参照46|gap/一致率は414に限定。ゼロ許容の整数最適証明、必要に応じexact branching/外部証明。極小gapでも最適としない|
 |H02|保存SCIP MIPのみ41の外部VIPR|保存下界=可行witnessとして条件付き採用。独立LPが弱いだけで棄却しない。外部証明で強化可能|
 |H03|現行staged8と主greedyの予算完全統制|新小規模統制は別実装。旧8設定の公平な総性能順位は未確定|
 |H04|未見入力/全量学習安定性|旧10repは測定のみ。新97learningは3診断input・exact期待値・COBYLA random-start条件のみ|
 |H05|運用H_planと真のtau_total|import/初期構築/転送/queue/実行環境を含む根拠ある計画締切が必要。32400秒を代用しない|
 |H06|QPU/compiled/物理qubit|CPUシミュレーションを実機時間/資源へ換算しない。native回路/compile/誤りモデルが必要|
 |H07|raw-shot可行率の一部未保存|best plan可行率と区別。必要なら保存sampleから別監査|
 |H08|材料proxyの実用full-cell移行|利用率/電圧/形成/Li在庫/密度/寿命/安全等の独立実証が必要|
 |H09|T09未知BOM/完成pack|case/tabs/foilmargin/packstructureを実測/設計根拠で埋めるまでdelta/NULL。残差補完しない|
 |H10|量子計算による実材料改善|今回実証対象外。モデル感度を量子帰属効果としない|
 |H11|地域道路/実車/実運用/B→DC|旧地域受入FAIL、B→運転軌跡未接続。旧C速度を新Bへjoinしない|
 |H12|末端未観測・除外物理|tail、回生/補機/勾配/旋回/積載変動の独立証拠・別モデルが必要|
 |H13|正式採用・研究成果/原稿統合|研究者の採否未決定。本trialで実施しない|

 旧FAIL（地域道路受入、T09_ROW183対向条件）と誤解釈FAIL（QPU読み替え・完成pack断定・任意削減率成功基準）を保持する。HOLD/FAILがあることを理由に実施済みの統計/実験を未実施とは扱わない。
 ''')
 md('STATISTICAL_VALIDITY_AUDIT.md','''
 # 統計・研究解釈の監査

 |項目|判定|確認内容|
 |---|---|---|
 |主比較/分母|PASS|JC greedy、random別、initial補助、J*共通。全460とexact414を分離|
 |階層|PASS|25group/26parent/input460/config8/fit1/measurement10。36,800独立学習としない|
 |欠測/非可行|PASS|全保存best可行を再計算、exact46はNULL、invalid raw未保存はNULL|
 |不確実性|CONDITIONAL|group交換可能性・測定stream独立は仮定。有限cohort/条件付き測定/仮想母集団感度を分離|
 |ゼロ改善区間|CONDITIONAL|bootstrap[0,0]は観測分布の退化。Wilson/条件付きゼロevent上限を併記、学習へ外挿しない|
 |新規学習反復|PASS|97optimizer-start/cellと10measurement/fitを分離。rep0 Wilson、fit bootstrap|
 |要因統制|CONDITIONAL|小規模同入力/支持/初期/mixer/p/評価/測定予算。support間ではgraphも変わる。旧staged8の全条件統制とは別|
 |時間比較|CONDITIONAL|scope内のCPU分布。Q10出力/greedy1出力と共通初期生成除外を明示。H_plan未設定|
 |モデル範囲|CONDITIONAL|T08主/T09補完、既知部材とunknownを分離。凍結物理/同軌跡/観測窓のみ|
 |49点/Crr|PASS|独立実験数にしない。軌跡内対応と決定論的格子を保持|
 |多重比較/検定|PASS|検定0。全cell/設定を表示、主要greedyと探索的機構診断を区別|
 |未実証接続|HOLD|実道路改善・実材料の量子由来改善・実機優位は未実証|

 scipy未導入のshell Pythonを統計には使わず、既存科学環境Python3.11へ切替えた。exact監査のFraction演算/CLIはshell Python3.13、科学計算/図は既存.condaの版を記録。入力は変更していない。解析コードの不備を修正した場合もtrial内だけで、NUMERICAL_VERIFICATIONとlogに最終検算を残した。
 ''')
 # Task completion and execution log.
 tasks=[('2-1','COMPLETE','CONDITIONAL','53終了理由/148独立LP/234再列挙/7追加証明/414参照','46未証明;41保存MIP外部証明なし'),('2-2','COMPLETE','PASS','36,800再検算/73,600対照差/112統計/672区間/図6','母集団・学習推定の限定'),('2-3','COMPLETE','CONDITIONAL','pilot288/main9312fit/93120measurement/同角度4656診断','3診断入力、CPU exact expectationのみ'),('2-4','COMPLETE','CONDITIONAL','旧scope集計/新9603 timing/97反復/図3','H_plan・実機・完全1計画scope未確定'),('2-5','COMPLETE','CONDITIONAL','132480 model rows/162T09 common cases/920正傾き/図5','BOM/材料/実道路未実証'),('2-6','COMPLETE','CONDITIONAL','両経路条件台帳/claim分類/Step3 handoff','Step3考察・正式採用は未実施')]
 table('STEP2_COMPLETION_MATRIX.csv',[dict(task=a,execution_status=b,scientific_status=c,work=d,remaining=e) for a,b,c,d,e in tasks])
 md('ADDITIONAL_EXPERIMENT_LOG.md',f'''
 # 追加計算の判断と実行

 - 厳密：最初に53終了理由を監査。default SoPlex残差は証明へ採用せず、rational zero-tolerance pilot、厳密mincut separation pilotを実施。既存large95も検査して影響範囲を拡大。148独立LP、61等値証明（新7/旧54）、残る証拠クラス/上下界を保存。新規大規模整数branchingの一括実施は、既存主要ΔJに不要で分数DFJ pilotが残るため省略し、46HOLDを保持。単なるtimeoutとして省略したのではない。
 - 既存統計：不要なQAOA/SUMO再実行をせず、保存NPZ/測定/古典経路から算術・統計・区間を計算。
 - QAOA：支持/初期/mixer/pが旧群で同時変化するため統制追加を実施。実行前仕様とinput選択、Wilson精度から97learning、pilot288fit→resource gate→main9312fit。main wall={qaoarun['wall_s']:.3f}s。全cell保持、取得改善をgateにしなかった。
 - 時間：新fitに内訳をinstrument。greedy同入力291測定、warmup/pilot別。旧時間の不一致scopeは解消したふりをせず残した。
 - T08/T09：既存49点だけではjoint u/V・会計構造依存を十分に表せないため、共通入力81格子/2policyとmass境界probeを追加。460保存trajectoryを使用し新SUMOは実行しなかった。model wall={p2run['wall_s']:.3f}s。
 - 走行条件：距離/再発進/速度/加速のcovariate quartile、対応Crr、group感度を計算。回生/補機/勾配等の物理境界は変更していない。

 全新規コードはscripts/、実行CLI/seed/環境/原数値はexperiments/・evidence/・logs/。各仕様書にはpilot後の追加固定も実行順で記録した。pilot失敗を隠さず、数値・資源診断として保持している。
 ''')
 # Figure linkage.
 figs=[]
 mapping={'PATH1_STATISTICAL_FIGURES':('PATH1_INPUT_CONFIG_STATISTICS.csv;PATH1_STATISTICAL_RESULTS.csv;PATH1_PAIRED_COMPARISONS.csv','scripts/path1_statistics.py;F1b from scripts/refine_figures.py'),'QAOA_CONTROLLED_EXPERIMENT_FIGURES':('QAOA_CONTROLLED_CELL_SUMMARY.csv;QAOA_MEASUREMENT_BUDGET_SENSITIVITY.csv;QAOA_SAME_ANGLE_DEPHASING.csv;QAOA_CONTROLLED_EXPERIMENT_RESULTS.csv','scripts/controlled_analysis.py;F1/F3 refined by scripts/refine_figures.py'),'PATH1_RUNTIME_FIGURES':('PATH1_RUNTIME_RESULTS.csv;PATH1_RUNTIME_SUMMARY.csv','scripts/runtime_analysis.py'),'PATH2_FIGURES':('PATH2_SENSITIVITY_SUMMARY.csv;PATH2_T09_COMMON_INPUT_SENSITIVITY.csv;PATH2_OPERATION_CONDITION_ANALYSIS.csv','scripts/path2_analysis.py')}
 for folder,(source,code) in mapping.items():
  for p in sorted((O/folder).glob('*.png')):figs.append(dict(png=str(p.relative_to(O)),pdf=str(p.with_suffix('.pdf').relative_to(O)),source_CSV=source,script=code,scope='CSV-derived scientific plot; no real-road or QPU validation claim'))
 table('FIGURE_INDEX.csv',figs)
 md('EXECUTIVE_SUMMARY.md',f'''
 # Step 2主要結果

 **TRIAL COMPLETE。科学的解釈はCONDITIONAL。** Task2-1〜2-6を実施し、Step3で使用できる結果・根拠台帳を保存した。

 1. 厳密参照の未証明53は全てSCIP optimal終了後のFraction bound-witness不一致。単なるtimeoutではない。7入力を独立有理数双対等値で追加証明し参照414、残46HOLD。旧407の反証0。41件は保存MIP等値のみの条件付き参照。
 2. 既存B460×8×10=36,800は主greedy対照改善0、全best可行。mirror支持最小=初期を全460で新DP確認。Groverは小規模で主対照同等、大規模で悪化。旧初期解差を主改善としない。
 3. 新統制3診断input・96cell・97learning/cell・10measurement/fit、9,312fit/93,120測定を実行。R1_020のfull graph basis p1=58/97、p2=78/97、full projector basis p1=0/97対uniform97/97の最適取得。主greedy超えはなく、支持・初期・層・学習・shotsの条件依存として解釈。
 4. CPU新9,603pipeline時間を計測、旧scopeを別集計。CPUシミュレータをQPUへ換算せず、H_plan数値なし。Q10出力/greedy1出力等のscope差を保持。
 5. T08主の5.448297kg、u*.877094、V*3.193156を検証。460trajectory×2Crrの総和DC削減率は.412579/.413590%、個別率mean.409329/.410435%、SD.012172/.012018pp。仮想group95感度は[.409778,.415257]/[.410775,.416284]%。モデル値であり測定DCや量子材料改善の実証ではない。
 6. 追加144case/132,480行とT09共通条件162行を分析。delta=bでmass/DCが消失、同一物理条件の1000〜1250kgではDC傾きが全920caseで正。T09の既知差は構造により9.722608/5.977891kg、完成packはNULL。

 条件台帳はCONTRIBUTION_CONDITION_TABLE.csv、主張監査はCLAIM_EVIDENCE_MATRIX.csv。実運用/材料/QPUへの未接続は残る。正式採用・原稿統合・Step3考察は未実施。
 ''')
 md('README.md',f'''
 # KMD修士研究 Step 2 分析・追加実験 trial

 独立した1回のtrial。Step1設計に基づき実際の統計分析、厳密参照再検査、追加小規模QAOA統制、CPU時間、T08/T09/DC感度、図、根拠台帳を作成した。正式採用・原稿統合・commit/push/公開なし。Step3は実行していない。

 入口：EXECUTIVE_SUMMARY.md、FINAL_AUDIT_REPORT.md、STEP3_HANDOFF.md。各Taskの実施状況はSTEP2_COMPLETION_MATRIX.csv。入力の実在パス/版/hashはSOURCE_PROVENANCE.csv、保全はevidence/。元データ・コード・原稿は読取のみ。

 |Task|主成果物|
 |---|---|
 |2-1|EXACT_REFERENCE_FAILURE_AUDIT.md / EXACT_REFERENCE_STATUS.csv / EXACT_REFERENCE_RECHECK_RESULTS.csv / EXACT_REFERENCE_IMPACT.md / EXACT_REFERENCE_BOUND_COMPARISON.csv|
 |2-2|PATH1_STATISTICAL_RESULTS.csv / PATH1_PAIRED_COMPARISONS.csv / PATH1_SUCCESS_RATE_ANALYSIS.csv / PATH1_UNCERTAINTY_ANALYSIS.md / PATH1_STATISTICAL_REPORT.md / PATH1_STATISTICAL_FIGURES/|
 |2-3|QAOA_CONTROLLED_EXPERIMENT_DESIGN.md / QAOA_CONTROLLED_EXPERIMENT_RESULTS.csv / QAOA_CONTROLLED_EXPERIMENT_REPORT.md / QAOA_CONTROLLED_EXPERIMENT_FIGURES/|
 |2-4|PATH1_RUNTIME_RESULTS.csv / PATH1_RUNTIME_SCOPE_COMPARISON.md / PATH1_RUNTIME_DISTRIBUTIONS.md / PATH1_RUNTIME_FIGURES/|
 |2-5|PATH2_SENSITIVITY_RESULTS.csv / PATH2_BOUNDARY_ANALYSIS.csv / PATH2_MODEL_UNCERTAINTY.md / PATH2_OPERATION_CONDITION_ANALYSIS.csv / PATH2_STATISTICAL_REPORT.md / PATH2_FIGURES/|
 |2-6|PATH1_CONDITION_EVIDENCE_MATRIX.csv / PATH2_CONDITION_EVIDENCE_MATRIX.csv / STEP2_CONTRIBUTION_CONDITIONS_SUMMARY.md / STEP3_HANDOFF.md|
 |監査|NUMERICAL_VERIFICATION.csv / STATISTICAL_VALIDITY_AUDIT.md / CLAIM_EVIDENCE_MATRIX.csv / STEP2_FINAL_AUDIT.md / FINAL_AUDIT_REPORT.md|
 |横断|STATISTICAL_METHODS.md / ADDITIONAL_EXPERIMENT_LOG.md / CONTRIBUTION_CONDITION_TABLE.csv / UNRESOLVED_ITEMS.md / REPRODUCIBILITY_REPORT.md / FIGURE_INDEX.csv|

 図はPNG/PDF計{len(figs)}組、全て対応CSVとscriptをFIGURE_INDEXに記録。raw新実験はexperiments/、各段階logはlogs/、検査/環境/入力hashはevidence/。広いfile stat baselineは保全補助で全バイト監査とは異なる。

 元系列：Bは時間窓なし460問題・R4=100、旧Cは保存速度460trajectory、旧Aは履歴。保存T08/T09はリポジトリ外preservationも参照し、独立trialを持ち出すだけで全上流データが付属するとはしない。具体的再実行条件はREPRODUCIBILITY_REPORT.md。
 ''')
 # Reproducibility instructions intentionally target fresh directory, never rerun into existing data.
 md('REPRODUCIBILITY_REPORT.md','''
 # 再現方法

 使用環境はevidence/ENVIRONMENT.json。元Git HEAD/remoteと開始状態はSTART/GIT_STATUS_START/GIT_DIFF_START。入力実在・保存場所・SHA256はSOURCE_PROVENANCE.csv、Step1入力hash照合はINPUT_HASH_BASELINE.csv。元B NPZ、測定JSON、古典RESULT、SCIP LP/log/solution、C trajectory、T08/T09原本が外部preservationにも必要。存在しない旧パスを推測して使わず、*_RELOCATIONS.csvの実在解決とhash一致を検査する。

 科学環境は既存`.conda/bin/python`3.11.15、NumPy2.2.5、pandas2.2.3、SciPy1.15.3、Matplotlib3.11。exact前半のFraction/CSV監査はshell Python3.13.5、NumPy2.3.5/pandas2.3.3で実施。整数/分数等値は環境のfloat表示へ依存しない。CLIは同じ保存SoPlex8.0.3（SCIP10.0.3 package）。全てCPU、GPU/QPU実行false。

 **既存trialへ再実行しない。** 新しい一意のreview_outputs配下へscriptsと実行前protocol文書をコピーする。common.pyのOはscript親の新trial、Rはそのrepo。scripts/evidence/logs/experiments/各FIGURESディレクトリを作り、元入力をpinしてから実行する。開始保全台帳はこのtrialのSTART作成処理と同等に別保存する。

 実行順：

 1. exact_audit.py（460witness・234列挙・53保存LP/log監査）。
 2. prepare_exact_models.pyで148の最終LP/log/solutionを実在・hash確認して接続。exact_recheck.py --pilot と exact_separation.py --pilot（zero-tolerance/valid-bound/resource診断）。full前のgateは分数解でも有効境界を残す場合にproceedとする。
 3. exact_recheck.py（148LP）→resolve_exact_status.py（弱いLPを理由に旧MIPを棄却しない）→exact_features.py。
 4. path1_statistics.py → zero_success_bound.py。
 5. controlled_qaoa.py --pilot → gate確認後controlled_qaoa.py（main97learning）。全cellを残す。
 6. runtime_analysis.py（Qmain終了後同core）、controlled_analysis.py（shot histogram/同角度/予算感度）、path2_analysis.py（保存trajectory;別core使用可）。
 7. control_sd_review.pyで目的分数が全反復同一のSDを厳密0としてpublic summaryへ正規化（元実験CSVは保持）。support_and_verification.py / dp_reference_review.py → refine_figures.py → write_reports.py → final_audit.py。

 初回default toleranceのSoPlex単独diagnosticは証明ではなく参考logで、科学結果再現には-f0/-o0が必須。QAOA/measurement/bootstrap seedは各CSVとprotocol。最終angles/probabilities、shot histogramから抽出bestを再現できる。厳密LPの全モデル/dual/primal/コマンドもexperimentsに保存。

 bitwiseで比較する対象は入力hashと保存原本。wall/CPU/RSSは実行環境に依存し、再実行で同じ数値を要求しない。新trial絶対パス・作成時刻でhashが変わる派生ファイルは、キーと数値列を比較する。計算コード版はCODE_SHA256.csv、成果物のhashはOUTPUT_SHA256_MANIFEST.csv。未確定external proofや物理接続を再現済みとしない。
 ''')
 table('NUMERICAL_VERIFICATION.csv',checks)
 # Placeholder final audit is filled with preservation evidence by final_audit.py.
 dump('evidence/REPORT_BUILD.json',dict(scientific_checks=len(checks),failed_checks=sum(x['status']=='FAIL' for x in checks),path1_conditions=len(p1),path2_conditions=len(p2),claims=len(claims),figures=len(figs),new_exact=7,accepted_exact=414))
 print('Reports and evidence matrices saved:',O)
if __name__=='__main__':main()
