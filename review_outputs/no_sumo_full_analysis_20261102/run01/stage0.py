"""Freeze definitions before the batch or full outcome evaluation."""
from common import *
def main():
 t=time.monotonic();old=[]
 for root,name in [(P1,'REVIEW_ARTIFACT_MANIFEST.json'),(P2,'ARTIFACT_MANIFEST.json'),(P3,'ARTIFACT_MANIFEST.json'),(P4,'ARTIFACT_MANIFEST.json')]:
  for x in js(root/name):
   p=use(root/x['path'],x['sha256']);old.append({'path':str(p),'sha256':x['sha256']})
  for p in root.glob('*.md'):use(p).read_text()
 table('PRIOR_ARTIFACTS_PINNED.csv',old)
 adopted=js(P4/'ANALYSIS_PROTOCOL.json');dump('PRIOR_PROTOCOL_RETAINED.json',adopted)
 group={x['parent_id']:x['group_id'] for x in rows(P4/'A_INPUT_COVERAGE.csv')};manifest=js(S/'mirror_family/MANIFEST.json');ops=rows(U/'review_outputs/cpx01_d11_validation_20261017/operations_2808.csv');refs=rows(P1/'B_PLAN_REFERENCES.csv')
 inv=[]
 for x in rows(P4/'A_INPUT_COVERAGE.csv'):use(x['input_path'],x['input_sha256']);inv.append(dict(series_id='A_OLD_TW',**x))
 for m in manifest:use(m['instance_path'],m['instance_sha256']);inv.append({'series_id':'B_NO_CUSTOMER_WINDOWS','problem_id':m['run_id'],'parent_id':m['parent_id'],'group_id':group[m['parent_id']],'input_path':str(resolve(m['instance_path'])),'input_sha256':m['instance_sha256'],'scale':m['scale_id'],'n':m['n']})
 for x in refs:use(x['source_path'],x['source_sha256'])
 for x in ops:use(x['classical_source']);use(x['quantum_source'])
 for p in [T8/'SCENARIOS.json',T8/'MATERIAL_ENERGY.csv',T9/'PACK_20KWH_SENSITIVITY.csv',BR/'T09_MASS_BOUNDARIES.csv',BR/'DC_MASS_RESPONSE.csv',BR/'T08_T09_DC_COMPARISON.csv',R/'01_research_design/methodology/CONTROLLED_MASS_TO_DC_MODEL_FREEZE.json']:use(p)
 table('INPUT_LEDGER.csv',inv);table('PARENT_GROUP_MAPPING.csv',[{'parent_id':k,'group_id':v} for k,v in sorted(group.items())])
 schemas={
 'A_POLICY_DECISIONS_2808.csv':{'PK':['condition_id','problem_id'],'required':['input_sha256','parent_id','group_id','acquired','adopted_method','fallback_reason','departure_s','route','F_PE','F_count','denominator_PE','return_s','return_deadline_s','status']},
 'A_DELIVERY_COMPLETION_BY_STOP.csv':{'PK':['comparison_scope','condition_id','problem_id','arm','task_id'],'required':['input_sha256','parent_id','arrival_s','service_start_s','complete_s','deadline_s','slack_s','late_s','q_PE','on_time','status']},
 'A_MECHANISM_COMPARISON.csv':{'PK':['condition_id','problem_id','arm'],'required':['input_sha256','parent_id','departure_s','route','availability_feasible','F_PE','return_s','status']},
 'B_PLAN_REFERENCES_36800.csv':{'PK':['problem_id','config_id','measurement_rep'],'required':['input_sha256','parent_id','group_id','measurement_seed_entropy','route_indices','objective_s','classical_initial_s','exact_optimum_s','global_gap_percent','optimal_match','OD_distance_m','fit_id','missing_reason','status']},
 'C_CONDITIONAL_MASS_DC_SUMMARY.csv':{'PK':['condition_id'],'required':['series_id','problem_id','parent_id','group_id','input_sha256','status','missing_reason','units']}}
 dump('OUTPUT_SCHEMAS_FROZEN.json',schemas)
 protocol={'version':'NO_SUMO_FULL_ANALYSIS_V1','authorization':'Current user authorizes complete existing-data analysis; prior task-local full-analysis prohibition is retained historically, superseded for A/B/C arithmetic only','base_protocol_sha256':sha(P4/'ANALYSIS_PROTOCOL.json'),'A_primary':'PE on-time rate; policy-prioritized minus classical-only in percentage points','B_primary':'raw sampled-best OD_seconds minus fixed classical initial, lower better; reduce measurement reps within input first','C_primary_scope':'Frozen trajectory controlled sensitivity; weighted DC saving and known mass boundaries; no unique universal material-effect estimand beyond existing separate designs','A_populations':{'policy':78,'acquired_mechanism':64,'conditions':36,'policy_rows':2808,'mechanism_arm_rows':9216},'B_populations':{'inputs':460,'settings':8,'reps':10,'references':36800,'exact_inputs':407,'missing_exact_inputs':53},'groups':{'parents':26,'demand_clusters':25,'unit':'physical input, nested within parent and source demand group'},'C_roster':'All saved T08 MATERIAL_ENERGY rows; all183 T09 rows; all25760 bridge rows; historical trajectories not current B','statistics':{'primary':'finite-cohort paired descriptive results','uncertainty':'predefined supplementary demand-group bootstrap; not calibrated sampling CI for real fleet','resamples':10000,'seed':20261102,'interval':'percentile95','tests':0,'multiplicity':'no significance tests; list all predeclared contrasts, no best-condition selection'},'sensitivity':{'A':'four arms and analytic departure thresholds; no new OD multiplier in main run','C':'all existing delta probes and two frozen Crr envelopes','B':'all460 and exact407 separately; recovery strata descriptive'},'missing':'null plus explicit reason; unacquired policy fallback; no imputation or denominator deletion','signs':{'A_rates':'policy-Qpriority minus C-only, percentage points','B':'sampled minus Cinitial, seconds or metres; positive worse','C':'LP minus S, Wh or kg; positive saving'},'batch_ceiling':{'max_projected_full_wall_s':1800,'max_process_RSS_bytes':4294967296},'restrictions':['NO_SUMO','NO_ROUTING','NO_QAOA','NO_ROAD_OR_INPUT_MODIFICATIONS','NO_THESIS_EDITS']}
 dump('FROZEN_PROTOCOL.json',protocol)
 (O/'00_FROZEN_ANALYSIS_PROTOCOL.md').write_text('''# 全件分析の事前固定仕様

`FROZEN_PROTOCOL.json` と `OUTPUT_SCHEMAS_FROZEN.json` を少数batch・全件結果確認前に保存した。現在の依頼でA/B/Cの既存データ全件算術を実行する。前回設計の主指標・分母・比較方向を保持し、旧タスクの全件禁止表記を変更しない。

AはPE加重定時率を主、件数率を副。D03=due_start+102秒、サービス一度、待機max(arrival,ready)、帰庫due32400を別判定。D10/D11の36政策と未取得14の切替を保持。政策78と成功64の機構4条件を分離する。Bはraw sampled-bestと古典初期解のOD目的値差を主とし、exact407と未確定53を分離。Cは設計別の条件付き質量・固定速度DCで、全設計を一つの量子効果量へまとめる主指標は設定しない。

固定有限cohortの対応記述を主とする。26親を実体group_idで25需要clusterに対応付け、同じclusterの親・規模・政策・seedをまとめた10,000回seed20261102 percentile95%区間を補助感度として計算する。実世界の確率標本・モデル誤差CIとは呼ばない。検定0、p値による選択なし。seedは問題内で平均し、親別対応差を併記する。未知を0にしない。

保存ODはN0由来の研究用固定費用表。地域受入FAILは保持する。Bの顧客定時率・速度・DCを計算しない。C材料改善を量子計算機の実証成果にしない。新しい道路、OD、経路、QAOA、SUMO、研究docs、DOCX変更は禁止。

少数batchはAの保存例・境界fixture、BのR0〜R5および参照欠測、Cの代表設計・全FAILと速度例を含む。不一致0で、実測からの見積がwall1800秒・process RSS4GiB以内の場合のみ全件へ進む。値の改善を合格条件にしない。出力はこの新レビュー領域に限定する。
''')
 dump('INITIAL_GIT_STATE.json',{'HEAD':subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),'status':subprocess.check_output(['git','status','--short'],cwd=R,text=True),'diff':subprocess.check_output(['git','diff','HEAD'],cwd=R,text=True),'python':sys.version,'platform':platform.platform()})
 finish('STAGE0',t,{'prior_artifacts_pinned':len(old),'A_inputs':78,'B_inputs':460,'references':len(refs),'schemas_frozen_before_batch':True})
if __name__=='__main__':main()
