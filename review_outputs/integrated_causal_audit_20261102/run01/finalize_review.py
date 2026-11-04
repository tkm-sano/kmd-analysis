"""Index new audit evidence and verify protected inputs; never run scientific jobs."""
from pathlib import Path
import csv,json,hashlib,subprocess,collections,ast
import numpy as np
R=Path('/home/takuma/kmd-analysis');U=Path('/home/takuma/kmd-analysis-pre-clean-20261102-112222/untracked');B=Path('/home/takuma/kmd-analysis-preservation-20261014-173544-a64e484c/backup');O=Path(__file__).resolve().parent
def sha(p):
 with p.open('rb') as h:return hashlib.file_digest(h,'sha256').hexdigest()
def rows(p):
 with p.open() as h:return list(csv.DictReader(h))
def table(n,a):
 with (O/n).open('w',newline='') as h:w=csv.DictWriter(h,fieldnames=list(a[0]));w.writeheader();w.writerows(a)
inventory={}
for name in ['SOURCE_FILES.csv','SUPPLEMENT_SOURCE_FILES.csv']:
 for x in rows(O/name):
  if not Path(x['path']).is_relative_to(O):inventory[x['path']]=x
extra=[U/'review_outputs/cpx01_d12_case_design_20261017/PILOT_CASES.csv',U/'review_outputs/cpx01_d12_case_design_20261017/D12_INPUT_DETAILS.json',U/'review_outputs/cpx01_d13_phase4_final_20261022/VALIDATION.json',U/'review_outputs/staged_qaoa_validation_20261102/REPRODUCTION.md',R/'docs/research/THESIS_REVISION_AUDIT.md']
for p in extra:inventory[str(p)]={'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size}
tracked=set(subprocess.check_output(['git','ls-files'],cwd=R,text=True).splitlines())
changed=[];combined=[]
for p,x in sorted(inventory.items()):
 pp=Path(p);actual=sha(pp)
 if actual!=x['sha256']:changed.append(p)
 rel=str(pp.relative_to(R)) if pp.is_relative_to(R) else ''
 combined.append({'path':p,'sha256':actual,'bytes':pp.stat().st_size,'in_current_HEAD':rel in tracked,'storage':'WORKTREE' if rel else 'EXTERNAL_UNTRACKED_COPY' if pp.is_relative_to(U) else 'PRESERVATION_COPY','unchanged_since_audit_read':actual==x['sha256']})
table('COMBINED_SOURCE_INVENTORY.csv',combined)
# Physical feasibility and lineage checks; no optimization or trajectory simulation.
stage=U/'review_outputs/staged_qaoa_validation_20261102'
manifest=json.loads((stage/'mirror_family/MANIFEST.json').read_text());plans=rows(O/'B_PLAN_REFERENCES.csv');byrun=collections.defaultdict(list)
for x in plans:byrun[x['run_id']].append(x)
violations=[];unchanged_by_variant=collections.Counter()
for m in manifest:
 p=U/Path(m['instance_path']).relative_to(R)
 with np.load(p,allow_pickle=False) as z:
  demand=float(np.sum(z['demand']));service=float(np.sum(z['service']))
 if demand>216:violations.append([m['run_id'],'capacity',demand])
 initial=[0]+json.loads((stage/'mirror_family/RUNS/MEAN_P2'/m['run_id']/'FIT.json').read_text())['initial_route']+[0]
 for x in byrun[m['run_id']]:
  if float(x['objective_seconds'])+service>32400:violations.append([m['run_id'],'road_plus_service',float(x['objective_seconds'])+service])
  unchanged_by_variant[x['variant']]+=json.loads(x['route_indices'])==initial
(O/'B_PHYSICAL_CONSTRAINTS.json').write_text(json.dumps({'checked_inputs':460,'checked_plan_references':36800,'violations':violations,'capacity_limit_PE':216,'return_limit_s':32400,'same_route_as_saved_initial_by_variant':dict(unchanged_by_variant),'scope':'input constraint arithmetic, not native return or DC'},indent=2)+'\n')
# Preserve explicit failure row and version mismatch records as review findings.
packpath=U/'review_outputs/t09_open_data_model_20261029/run01/PACK_20KWH_SENSITIVITY.csv';issues=[]
for line,x in enumerate(rows(packpath),2):
 if x['overlap_condition'].startswith('FAIL'):
  issues.append({'issue_id':'F-C1','status':'FAIL','path':str(packpath),'line':line,'column':'overlap_condition/negative_face_area_m2','expected':'negative area >= positive area for full facing same footprint','actual':x['negative_face_area_m2']+' < '+x['positive_face_area_m2'],'difference_m2':float(x['negative_face_area_m2'])-float(x['positive_face_area_m2']),'cause':'independent loading/area probe violates assumed overlap','affected_claim':'same-footprint full-facing design acceptance'})
table('EXPLICIT_FAILURE_ROWS.csv',issues)
principal=[R/'README.md',R/'docs/QUANTITATIVE_GUIDE.md',R/'01_research_design/scenario_evaluation/final_quantitative_study_20261008/FINAL_QUANTITATIVE_RESULT_FREEZE.json',R/'01_research_design/methodology/CONTROLLED_MASS_TO_DC_MODEL_FREEZE.json',U/'docs/research/CPX01_D10_ADOPTION_DECISION_20261017.md',U/'review_outputs/cpx01_d11_validation_20261017/MANIFEST.json',U/'review_outputs/unified_no_windows_r0_r8_20261022/FREEZE.json',U/'review_outputs/r0_r8_main_results_20261023/FREEZE.json',stage/'mirror_family/CONFIGURATION_FROZEN.json',stage/'grover_depth/CONFIGURATION_FROZEN.json',stage/'active_adjacent_p3/CONFIGURATION_FROZEN.json',U/'review_outputs/material_ev_stage2_20261026/run02/SCENARIOS.json',U/'review_outputs/t09_open_data_model_20261029/run01/RUN_CONFIG.json',U/'review_outputs/t08_t09_conditional_bridge_20261030/run01/INPUTS.json']
lines=['# 証拠所在・採用版台帳 — 2026-11-02','',
'開始時HEAD：`1b00bd7927fa1e7688e4772ac1da9db46d9bac11`。開始時tracked差分なし。既存未追跡は`docs/research/THESIS_REVISION_AUDIT.md`と`tmp_RsrchMstrDc_1026_revised.docx`の2件で、今回変更していない。新しい成果物は本run01だけ。commit/pushなし。',
'','## 所在と正式版の判断','',
'R=`/home/takuma/kmd-analysis`、U=`/home/takuma/kmd-analysis-pre-clean-20261102-112222/untracked`、B=`/home/takuma/kmd-analysis-preservation-20261014-173544-a64e484c/backup`、L=`同保全親/relocated`。U/L/Bは公開リポジトリの同梱資料ではない。作業木内の実在もGit追跡とは別であり、COMBINED_SOURCE_INVENTORY.csvのin_current_HEADで区別する。元SOURCE_FILES.csvのGIT_TREEは物理的な作業木所在を指し、公開追跡を意味しない。',
'',
'採用はmtimeではなく採用決定・freeze・入力hash・source/設定・保存結果の連鎖で判断した。未追跡THESIS_REVISION_AUDITは探索の案内としてのみ利用し、その報告値を独立検算の正解にしなかった。新研究資料の公開・移動・復元はしていない。',
'',
'|系列|採用資料と版|選定理由・非採用との区別|','|---|---|---|',
'|A|D10 ADOPTION_DECISION（2026-10-17）→D11 operations/候補→原R1 full_v2/古典JSON。後続RD/Q採用記録とD13 native監査も照合|PROVISIONALより正式ADOPTEDが優先。36条件は探索的仮想政策。D13成功を実配送受入に拡張しない|',
'|B|UNIFIED_NO_CUSTOMER_WINDOWS_V1 R0〜R5入力→staged 20261102の3familyのCONFIGURATION_FROZEN/PROTOCOL/SOURCE_SNAPSHOTと各run|8最適化設定36,800参照の範囲を採用。旧窓あり460、UNIFIED全R0〜R8の548、旧MAIN20310行、11月1日追加群を別系列に保持|',
'|C|T08 stage2 20261026/run02 SCENARIOS/source/energy、T09 20261029/run01部材/設定、bridge 20261030/run01|T08=簡略閉会計、T09=既知部材+未知。bridgeは条件付き質量差/軌跡感度。旧B0/B1/B2は材料主入力としない|',
'|道路|integrated_research_results_20261028/run02/ROAD_NETWORK_CLOSUREと元audit|修正候補不採用・追加開発打切り。最終静的PASSだけで動的受入を宣言しない|',
'',
'## 主要採用資料の実ファイルSHA256','',
'|実パス|SHA256|HEAD追跡|','|---|---|---|']
for p in principal:
 if p.is_file():
  rel=str(p.relative_to(R)) if p.is_relative_to(R) else ''
  lines.append('|`'+str(p)+'`|`'+sha(p)+'`|'+str(rel in tracked)+'|')
lines+=['','全入力・個別結果・sourceのhashはCOMBINED_SOURCE_INVENTORY.csvを参照。B_PLAN_REFERENCES.csvは各36,800参照に原JSON path/hashを保存。CSV全列・型・null・範囲はCSV_SCHEMA_AUDIT.json、検算はCHECKS/SUPPLEMENT_CHECKS、版差はB_SOURCE_BINDING_GAPSに保存。',
'','## 調査範囲と証拠区分','',
'README、QUANTITATIVE_GUIDE、docs/research、01_research_design、configs/CANONICAL_CONFIG_INDEX、src、scripts、review_outputs、reproducibility/release・環境記録を調査。旧計算時sourceは公開aliasではなくfreezeと当時snapshotを優先。材料文献は保存Chen本文・来歴・設定記録を読んだ。今回は新規web文献探索や文献値の外部再測定を行っていない。',
'',
'過去独立記録（D11、causal_engineering_audit、native各phase、T09/bridge verification、道路CLOSURE）は既存証拠として保管し、今回の別コード検算とは区別した。ディレクトリ全ファイルの網羅的科学監査や全archive全byte照合を主張しない。',
'','## 新成果物と再実行入口','',
'6文書は00所在、01監査、02仕様、03実装/試行、04再現性不足、05判断。本領域内の補助CSV/JSON/コードは独立監査の追跡用。大規模実験は含まない。',
'',
'軽量監査の再実行（必要な外部資料が同じ場所にありnumpyを利用できる場合）：','',
'```bash','python -B review_outputs/integrated_causal_audit_20261102/run01/independent_audit.py','python -B review_outputs/integrated_causal_audit_20261102/run01/supplement_audit.py','python -B review_outputs/integrated_causal_audit_20261102/run01/finalize_review.py','```',
'',
'これらは本レビューの生成物を更新する。凍結して保管する場合は新しいレビューコピーで実行する。科学runner再生成の代替ではない。',
'',
f'最終保全照合：参照入力{len(combined):,}ファイル、読取り時hashからの変更{len(changed)}。今回実施したsubsetの保全であり全研究領域の完全保全ではない。新出力のhashはREVIEW_ARTIFACT_MANIFEST.json。']
(O/'00_SOURCE_INVENTORY.md').write_text('\n'.join(lines)+'\n')
for p in O.glob('*.py'):ast.parse(p.read_text())
final={'source_files':len(combined),'changed_sources':changed,'physical_constraint_violations':violations,'tracked_diff':subprocess.check_output(['git','diff','--stat'],cwd=R,text=True),'status':subprocess.check_output(['git','status','--short'],cwd=R,text=True),'scientific_runs_executed':0}
(O/'FINAL_VERIFICATION.json').write_text(json.dumps(final,ensure_ascii=False,indent=2)+'\n')
art=[{'path':str(p.relative_to(O)),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(O.iterdir()) if p.is_file() and p.name!='REVIEW_ARTIFACT_MANIFEST.json']
(O/'REVIEW_ARTIFACT_MANIFEST.json').write_text(json.dumps(art,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(final,ensure_ascii=False))
