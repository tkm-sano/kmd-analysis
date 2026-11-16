"""Render the final design report from immutable pilot artifacts."""
import json
import math
from pathlib import Path

DOC=Path(__file__).resolve().parent
ROOT=DOC.parents[2]
OUT=ROOT/'output/toc_delivery/comparison_design_20261116_v1'

def read(p):return json.loads(Path(p).read_text())

def main():
 s=read(DOC/'SUMMARY_DATA.json');a=read(OUT/'design/variance_ANALYSIS.json')
 cp=read(OUT/'PIPELINE_COMPLETION.json');status=cp['status']
 cand=read(OUT/'design_supplement/CANDIDATES_ALL_METHODS.json')
 sens=read(OUT/'design_supplement/WITHIN_VARIANCE_SENSITIVITY.json')
 limits=read(OUT/'design_supplement/RESOURCE_LIMIT_PRECISION.json')
 failure=read(DOC/'CONFIRMATION_NATIVE_CAP_FAILURE.json')
 lines=['# 配送計画比較：実測による実験設計・最終報告',
 '実験ID：`comparison_design_20261116_v1`。上限付き予備実験・算定処理・候補表・非実行manifestの作成は完了。本実験開始は **HOLD**。本実験は実行していない。',
 '計画作成90試行を実行し、83試行を採用、7試行を不採用として保全した。Aの再設計・実事業者代表性の再検証は完了条件に加えていない。',
 '|決定項目|今回の採用値／固定値|根拠・実測|本実験へ残る判断／条件|',
 '|---|---|---|---|',
 '|1試行|保存入力の読込・初期化から割当、訪問順、最大2便の接続、積込／バース、全枝停止・選択、最終二重検査まで。失敗も1試行|既存比較契約を継承し90試行で実測|変更不要。便・候補・shots・内部4枝をRへ数えない|',
 '|総時間上限τ|予備の固定値240秒、BCD内部上限150秒|120秒leanは9/15、240秒retainedは15/15採用。固定後45/45、確認14/15|**本実験採用保留**。確認のS3・Dでnative上限超過。集約・検査・転送の予算配分等を別IDで再検証し、変更後の分散を再測定する|',
 '|内部設定|D：訓練1000 shots／評価、最終4096 shots／呼出し、最大80評価、最大2 pricing rounds、1 restart、p=2、macro groups=3。C：Routing配分0.5。BCD/対照：内部4プロセス、各1コア・native1 thread|既存retained設定。二つの事前候補を全方式へ同じ回数だけ与えた。実呼出し・未選択枝も保存|最適shotsや真の収束を証明した値ではない。確認不合格のため本実験用には未採用|',
 '|独立試行数R_a|分散測定3回／規模／手法、確認1回。いずれも運用上の初期バッチ。本実験R_aはnull|固定後45試行と別seed確認15試行。Aの品質は決定的な1値として扱い、計時は反復|h_D、率精度、総予算、0観測分散の扱いを選ぶ。確認不合格の現設定から本実験Rを採択しない|',
 '|需要数M|固定需要の主比較：S2でM=1。S1/S3も各規模M=1の補助ケース|N=1000/2000/4000の凍結3入力。同一familyの入れ子で、3独立familyではない|一般化は未採用。M=5/10/30等は仮定感度だけで、新需要を生成していない|',
 '|統計解析|精度設計。主：固定S2のD−C距離差、独立Welch、両側95%。率：WilsonとClopper–Pearson。補助は探索的点ごと95%|既存主比較・主要距離指標・95%を継承。同じseed/反復番号だけで対応解析しない|h_D=1/5/10 kmは提案候補、未採用。δはこの精度設計では要求しない。複数主要比較への変更は事前family指定とHolm等の別登録|',
 '|停止規則|本実験は事前固定した試行一覧で終了。p値・通常CIの幅による追加なし。資源・入力／code不一致・回収失敗は安全停止し未実行を保持|一覧hashと固定件数の変更拒否、失敗・未達・期限超過・旧分散の混入拒否を検証|採用R・全seed・実行順序・A参照会員は条件確定後に固定。現在manifestはexecutable=false|',
 '',
 '比較対象は凍結`A_rule_v1`＋FCFS、有向CWのB、OR-Tools RoutingのC、限定Huang AOA＋車両日列のD、および`D_CLASSICAL_REPLACEMENT`。後者は同じ最大3マクロ群の最大6順序を古典列挙する置換対照で、既存の量子省略対照とは区別した。DはQiskit statevectorシミュレーターであり、実機QPUの優位性や事業者実績の改善を主張しない。',
 '共通物理条件は1地点1単位、容量60／便、最大2便、積込1800秒／非空便、地点作業120秒、8〜20時、個別時間窓なし。車両／バースはS1=10/2、S2=20/4、S3=40/8。既存有向Route ODを使用し、凍結入力・OD・A・READMEを変更していない。',
 'T_kindは`comparison_parent_wall_including_process_setup_v1`。入力・fresh child起動・必要なimport・候補転送・親の二重検証までを含む。旧native Tや旧逐次版と同条件の時間として混ぜない。τは研究用比較予算で、運用締切の根拠はない。',
 '',
 '|段階|実行／採用|全試行T_attempt合計［秒］|位置付け|', '|---|---:|---:|---|']
 labels={'selection_lean':'設定選択 lean（120秒）','selection_retained':'設定選択 retained（240秒）','variance':'固定後の分散測定','confirmation':'別seed確認'}
 for p in s['phase_costs']:lines.append(f"|{labels[p['stage']]}|{p['attempts']} / {p['adopted']}|{p['wall_s']:.3f}|{'調整費用' if p['stage'].startswith('selection') else '本実験へ流用しない予備データ'}|")
 lines += [f"合計{s['T_attempt_sum_s']:.3f}秒（{s['T_attempt_sum_s']/3600:.3f}時間）。予備90試行のcap合計19,800秒、全パイプライン管理上限21,600秒。完了時の管理カウンタは{cp['elapsed_including_prior_invocations_s']:.3f}秒（初回起点を最初の試行より300秒前とした保守的補正を含む）。",
 '共通コーディネータimportと部分T_exportはSUMMARY_DATA.json、試行間の実測gapと準備・回収の提案予備費用は追加候補表に別記した。部分T_exportだけで出力全体を測れたとはしない。予約core×wallと実CPU時間も区別する。',
 '最初のlean後に、Aが残した親affinity 1コアで次登録が停止したため、設定固定前に実行管理だけを修正した。試行後に4コアへ復帰し、完了済み15試行を再実行せず継続。手法・試行内計時・内部設定は変更していない。lean旧版、修正後retained/分散/確認のsource snapshotと変更理由を保全した。',
 '',
 '固定S2の予備結果は以下（平均±標本SD、各手法3回、成功条件付き）。AのD/Wは1つの決定的値であり、3回は計時反復である。本実験結果ではない。',
 '|手法|D［km］|W［分］|T_program［秒］|', '|---|---:|---:|---:|']
 s2=next(x for x in a if x['case_id']=='S2')
 names={'D_CLASSICAL_REPLACEMENT':'古典置換対照'}
 for method,m in s2['methods'].items():
  cells=[]
  for metric in ('D','W','T_program'):
   v=m['metrics'][metric];cells.append(f"{v['mean']:.4f} ± {math.sqrt(v['variance']):.4f}")
  lines.append('|'+names.get(method,method)+'|'+'|'.join(cells)+'|')
 lines += ['D−Cの観測平均距離差は+50.3567 km。ただし全規模のC/Dで距離の標本分散は0であり、通常式を機械的に当てた縮退区間を精度保証・真の分散0・統計的優越性の証拠にはしない。正規χ²上側分散感度は0分散について未識別とし、追加SDを仮定した表を併記した。確認データを分散推定へ追加していない。',
 '固定後は全cellで可行率3/3だが、個別cellの95% Clopper–Pearson下限は約0.2924。失敗確率0とは扱わない。S3・Cは可行でも共通D/W目標に3/3未達であり、到達率と打切りを別に保存した。未達をτで到達した記録には変えていない。',
 '',
 '確認のS3・Dは入力VALID、終了NORMAL、検証状態NATIVE_DEADLINE_REJECTED、adoptable=false。外側は177.864秒で240秒以内だったが、native全体は153.584秒で固定150秒を3.584秒超過した。4枝は約109.4〜109.5秒でVALIDATEDとなっており、native全体の集約等を含む区間の予算不足が確認された。棄却計画・二重検証・全枝・量子処理を保存し、採用D/W/Tはnullのまま。',
 'この失敗をseed置換や上限の遡及緩和で成功へ変更していない。次の設定候補では集約・選択・検査・転送等の予約を再設計し、時間配分／内部設定を変えた後の分散・確認を新seedで再測定する必要がある。現IDの事前追加終了規則に従い、追加の調整実行はしない。',
 '',
 'S2だけを本実験対象とする費用・率精度の候補例（未採用）。h_D=5 kmの点分散表を表示するが、距離分散の不確かさは未解決であり、この表は品質精度の保証ではない。率の半幅は絶対確率ポイントで、相対誤差ではない。',
 '|率の最悪半幅|全手法同一R|総試行数|出力等込み期待時間［h］|試行cap合計［h］|提案予備費用込み予約［h］|24h予約内|', '|---|---:|---:|---:|---:|---:|---|']
 for hp in (.15,.1,.05):
  x=next(x for x in cand if x['scale']=='S2' and x['metric']=='D' and x['h']==5 and x['rate_h']==hp and x['sensitivity']=='point' and x['allocation']=='uniform_all' and x['main_budget_s']==86400)
  lines.append(f"|±{hp*100:.0f}ポイント|{x['R_a']['C']}|{x['total_attempts']}|{x['estimated_wall_including_orchestration_s']/3600:.2f}|{x['sum_attempt_caps_s']/3600:.2f}|{x['planning_reserve_wall_s']/3600:.2f}|{'はい' if x['within_planning_time_reserve'] else 'いいえ'}|")
 lines += ['全手法均等と分散・費用配分を972行で比較。点分散0の距離では率精度が回数を決めるが、W/Tの分散感度では品質精度が回数を増やす。Aの品質は1値、計時・取得率の反復はR_Aとして分ける。独立試行全体の最良値だけで比較する処理は行わない。',
 'C/Dの十分な成功数の見積もりは、予備のexact成功率下限を仮定した二項モデルで各手法90% assuranceを置く計画用近似（同時90%保証ではない）。費用は失敗を含む全T_attemptから推定。内部4枝の並列効果は既に時間に含まれ、さらに4で割らない。',
 '予約費用は実測最大gap＋回収10秒/試行＋共通準備300秒という提案値。共有ホスト／IOの絶対上界ではない。S1/S3も本実験へ含める場合は各規模の費用を加算する。',
 '',
 '0分散を未知のまま扱うための対称な追加SD感度例（追加SDは両手法で同じ、実測値でも採用仮定でもない。率半幅±15ポイント、A/B/対照は各39回）。',
 '|追加SD［km］|h_D［km］|R_C=R_D|総試行cap［h］|', '|---:|---:|---:|---:|']
 for sd,h in [(0,5),(1,1),(5,1),(5,5),(10,5),(10,10)]:
  x=next(x for x in sens if x['scale']=='S2' and x['additional_SD_C_km']==sd and x['additional_SD_D_km']==sd and x['h_km']==h and x['rate_h']==.15)
  lines.append(f"|{sd}|{h}|{x['R_a']['C']}|{x['sum_attempt_caps_s']/3600:.2f}|")
 lines += ['これらは要求精度と分散仮定で回数・費用が大きく変わることを示す候補であり、どれも採用していない。分散仮定の独立した根拠を採るか、追加の有限予備設計で確認する必要がある。',
 '',
 '資源上限から全5手法均等Rを制限した場合の率精度（同じ予約費用基準）。元の精度を維持できたとは扱わない。',
 '|総時間候補|実行可能な均等R|Wilson最悪半幅|', '|---:|---:|---:|']
 for x in limits:
  if x['scale']=='S2':lines.append(f"|{x['budget_s']/3600:.0f} h|{x['R_a_uniform_all']['C']}|±{x['worst_case_Wilson_rate_halfwidth']*100:.2f}ポイント|")
 lines += ['1/4/24時間は総費用の提案候補であり、承認済みの本実験予算ではない。距離の縮退した点予測半幅0は、達成可能な品質精度の保証として表示しない。',
 '',
 '|規模|サンプルした子木peak［GiB］|native HWM和［GiB］|親HWM込み保守的proxy［GiB］|', '|---|---:|---:|---:|']
 for m in s['memory_by_scale']:lines.append(f"|{m['scale']}|{m['sampled_worker_tree_peak_GiB']:.2f}|{m['native_tree_HWM_sum_GiB']:.2f}|{m['conservative_memory_proxy_GiB']:.2f}|")
 q=s['quantum_observations']
 lines += ['上表は固定後予備の観測範囲。子プロセス木RSS合計を0.5秒で監視し32GiB超過時停止、Aは既存4GiBのaddress-space上限も維持した。HWMは異時点・共有ページの重複を含み、サンプル間peakの厳密な同時物理メモリ値ではない。',
 f"量子部分は全枝・不採用試行を含め開始{q['started_calls']:,}／完了{q['completed_calls']:,}呼出しを観測。完了記録の訓練{q['observed_training_shots']:,}、最終{q['observed_final_shots']:,} shots、観測qubits={q['qubits']}。これはシミュレーター上のサンプル数。native accounting不完全フラグのある{q['native_accounting_flag_incomplete_trials']}試行はそのまま保持し、完了呼出し観測と総量の完全性を混同しない。",
 '初可行な内部候補と親の最終検証時刻、D/W履歴、親の四区間、native branch timing_events、量子training/circuit/evolution/sampling/decode時間、共通完成器・検査の観測区間は生ログとTELEMETRYへ保存。共通完成器は割当・スケジュールを含み、独立した修復段階はない。重複するhybrid/complete/quantum時間や4枝の合計を親wallへ足し込まない。CPUは親・枝・プロセス木観測でscope付きの値として保存し、未観測区間を0としない。',
 '',
 '解析は固定需要のC/D独立2群を主とし、失敗は全試行率に残す。成功条件付き品質の対象case・成功数を明示。需要集団を解析する場合だけ需要内の手法平均差を同一familyで対応させ、需要平均差分散に含まれる実行誤差を二重加算しない。現M=1から需要間分散は推定しない。M=5/10/30、R=1/3/5等の一般化表は需要間SDを仮定した感度であり、**30需要×5回を採用していない**。',
 'Jは既存の(D/D_A+W/W_A+T/T_A_ref)/3、等重み、全指定A会員の時間中央値を継承。分母0・参照不成立は理由付きnull、A各行を一律1へ書き換えない。Jの補助区間は当該A参照に条件付け、A時間中央値自体の推定不確かさを含めない。主比較は1 contrast/metric/scale、補助の点ごと95%区間に同時保証はない。非有意を同等・非劣性とは判定しない。',
 '',
 '開始条件に残るのは、(1)確認で露呈したnative予算・集約予約の再設計と、変更後設定での分散／確認、(2)研究上必要なh_D、率精度、総費用と補助規模の範囲、(3)0観測分散の扱いに対する独立な根拠または追加の有限予備、(4)それらに基づくR_a・全seed・順序・A参照会員の固定。δやAの事業者代表性を新たな必須条件にはしていない。',
 '現在のMAIN_MANIFEST.jsonは非実行の保留manifest。入力hash・比較手法・版・内部設定・τ・資源・選択規則・解析・停止規則を保持するが、未採用のRとseed一覧を埋めて実行可能と偽ってはいない。設定変更前の分散を新設定へ流用しない。',
 '',
 '成果物・再現入口：',
 '',
 '- [決定規則・物理条件・解析方針](PROTOCOL.md)、[実行・集計コマンド](REPRODUCE.md)',
 '- [全手法均等／分散費用配分CSV](../../../output/toc_delivery/comparison_design_20261116_v1/design_supplement/CANDIDATES_ALL_METHODS.csv)',
 '- [固定需要内分散感度](../../../output/toc_delivery/comparison_design_20261116_v1/design_supplement/WITHIN_VARIANCE_SENSITIVITY.json)、[資源内精度](../../../output/toc_delivery/comparison_design_20261116_v1/design_supplement/RESOURCE_LIMIT_PRECISION.json)',
 '- [需要数Mの仮定感度](../../../output/toc_delivery/comparison_design_20261116_v1/design/GENERALIZATION_SENSITIVITY.json)',
 '- [全枝・時系列・資源の集計](../../../output/toc_delivery/comparison_design_20261116_v1/design/TELEMETRY.json)、[率・打切り](../../../output/toc_delivery/comparison_design_20261116_v1/design/RATES_AND_CENSORING.json)',
 '- [保留main manifest](../../../output/toc_delivery/comparison_design_20261116_v1/design/MAIN_MANIFEST.json)、[確認失敗の診断](CONFIRMATION_NATIVE_CAP_FAILURE.json)',
 '- [最終hash監査](FINAL_AUDIT.json)、[旧変更・README保全の基準](BASELINE_HASHES.json)、各段階REGISTEREDとSOURCE_SNAPSHOT、依存版とVeRyPy sourceを保全。',
 '',
 '検証は関連回帰89件、新しい設計9件（前者と8件重複）、追加配分2件、人工fixture全5手法、0分散不足／正分散の追加表、段階間affinity復帰を実行。初期互換不具合と実行管理の停止履歴もvalidation/とログに保全。最終監査の成否・件数はFINAL_AUDIT.jsonを正本とする。commit/push、README変更、凍結入力・過去結果の上書き、本実験実行は行っていない。',
 '方法論の参照はPROTOCOL.mdのCampelo & Takahashi、Campelo & Wanner、Morris et al.、Bucher et al.。当該文献がこの予算・shots・回数の最適性や精度保証を認定したとは説明しない。']
 rendered=[]
 for line in lines:
  if rendered and line.startswith('|') != rendered[-1].startswith('|') and line and rendered[-1]:rendered.append('')
  if rendered and rendered[-1].startswith('# '):rendered.append('')
  rendered.append(line)
 (DOC/'FINAL_REPORT.md').write_text('\n'.join(rendered)+'\n')
 ledger={'experiment_id':'comparison_design_20261116_v1','bounded_pilot_pipeline_complete':True,
  'main_start_allowed':False,'main_started':False,'main_settings_adopted':False,
  'trial_definition_adopted':True,'fixed_pilot_tau_s':240,'fixed_pilot_BCD_native_cap_s':150,
  'M_per_scale':1,'independent_demand_families':1,'main_R_a':None,'main_seed_list':None,
  'primary':'fixed S2 independent D minus C distance mean difference, precision design,95%',
  'h_D_km':None,'delta_required':False,'rate_precision':None,'main_total_budget_s':None,
  'sample_distance_variances_measured_zero':True,'informative_primary_variance_upper_bound_available':False,
  'necessary_conditions_before_main':failure['required_before_main'],
  'no_A_redesign_or_operator_representativeness_gate':True,
  'pilot_attempts':90,'pilot_adopted':83,'tuning_variance_confirmation_kept_separate':True,
  'full_execution_artifacts':'output/toc_delivery/comparison_design_20261116_v1',
  'selected_settings_identity':status['setting_identity']}
 if (DOC/'FINAL_AUDIT.json').exists():
  audit=read(DOC/'FINAL_AUDIT.json');ledger.update(audit_pass=audit['pass'],audited_output_files=audit['audited_output_files'])
 (DOC/'DECISION_LEDGER.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
 adopted=read(DOC/'ADOPTED_SETTINGS.json');adopted.update({'main_settings_adopted':False,
  'status':'fixed settings used for pilots; main adoption HOLD after confirmation native cap failure',
  'confirmation_adopted':14,'confirmation_attempts':15,
  'selection_attempt_wall_cost_s':sum(x['wall_s'] for x in s['phase_costs'] if x['stage'].startswith('selection'))})
 (DOC/'ADOPTED_SETTINGS.json').write_text(json.dumps(adopted,ensure_ascii=False,indent=2)+'\n')
 print('Final report and decision ledger written; main HOLD')

if __name__=='__main__':main()
