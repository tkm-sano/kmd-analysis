"""Postcollection integrity checks and formatting only; never launches planning.

The preregistered analysis.py and its estimates remain unchanged. This file
records coverage limits and formats both registered allocation policies.
"""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import statistics
import time

DOC=Path(__file__).resolve().parent
ROOT=DOC.parents[2]
OUT=ROOT/'output/toc_delivery/non_time_variance_pilot_20261117_v1'
METHODS=('A','B','C','D','D_CLASSICAL_REPLACEMENT');SCALES=('S1','S2','S3')
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def csvrows(p):
    with p.open(newline='') as f:return list(csv.DictReader(f))
def close(a,b):return a is not None and b is not None and math.isclose(a,b,rel_tol=1e-12,abs_tol=1e-10)
def hours(x):return 'null' if x is None else f'{x/3600:.2f}'

def run(finish=False):
    begin=time.perf_counter();m=read(OUT/'REGISTERED.json');s=read(OUT/'SUMMARY_DATA.json');cand=read(OUT/'MAIN_CANDIDATES.json');cost=read(OUT/'COST_ACCOUNTING.json');checks=[]
    def check(name,ok):checks.append({'check':name,'pass':bool(ok)})
    planned={r['run_id']:r for r in m['runs']};raw={i:read(OUT/'runs'/i/'RESULT.json') for i in planned}
    check('75_unique_preregistered_ids',len(planned)==75 and len(s['rows'])==75 and {r['run_id'] for r in s['rows']}==set(planned))
    check('all_result_identities_match_registration',all(r['experiment_id']==m['experiment_id'] and r['config_hash']==m['config_hash'] and r['physical_hash']==m['physical_hash'] and r['T_kind']==m['T_kind'] and r['run_id']==i and r['case_id']==planned[i]['case_id'] and r['method']==planned[i]['method'] and r['seeds']==planned[i]['seeds'] for i,r in raw.items()))
    check('all_registered_branch_seeds_retained',all(b.get('seeds')==planned[i]['branches'][b['branch_id']] for i,r in raw.items() for b in r['branches']))
    check('branch_core_pins_match_registration',all(b.get('cpu_affinity')==[m['cpu_profile']['cpu_ids'][b['branch_id']]] for r in raw.values() for b in r['branches']))
    management=[read(OUT/'runs'/i/'MANAGEMENT.json') for i in planned]
    check('parent_affinity_restored_after_every_trial',all(x['parent_affinity_restored']==m['environment']['affinity'] for x in management))
    check('one_boot_and_nonoverlapping_outer_trials',all(x['boot_id']==m['environment']['boot_id'] for x in management) and all(b['before_management_write_perf_counter']>=a['after_execute_perf_counter'] for a,b in zip(management,management[1:])))
    check('75_trial_csv_ids',len(csvrows(OUT/'PILOT_SUMMARY.csv'))==75 and {r['run_id'] for r in csvrows(OUT/'PILOT_SUMMARY.csv')}==set(planned))
    check('15_condition_csv_rows',len(csvrows(OUT/'CONDITION_SUMMARY.csv'))==15)
    check('180_candidate_csv_json_ids',len(cand)==180 and len(csvrows(OUT/'MAIN_CANDIDATES.csv'))==180 and {r['candidate_id'] for r in csvrows(OUT/'MAIN_CANDIDATES.csv')}=={r['candidate_id'] for r in cand})
    group={(g['scale'],g['method']):g for g in s['conditions']};means={}
    for sc in SCALES:
        for method in METHODS:
            rr=[r for r in raw.values() if r['case_id']==sc and r['method']==method];g=group[sc,method];attempts=[r['T_attempt'] for r in rr if r['T_attempt'] is not None]
            check(sc+':'+method+':cost_only_new_attempts',len(attempts)==g['T_attempt_all']['n'] and close(statistics.mean(attempts),g['T_attempt_all']['mean']))
            check(sc+':'+method+':success_ids_exact',[r['run_id'] for r in rr if r['adoptable']]==g['successful_trial_IDs'])
            means[sc,method]=g['T_attempt_all']['mean']
    check('total_attempt_cost_exactly_once',close(cost['T_attempt_total_s'],sum(r['T_attempt'] for r in raw.values())))
    for c in cand:
        rmap=c['R_a_by_scale'];n=c['total_attempts_all_scales'];values=[rmap[sc][method] for sc in SCALES for method in METHODS]
        check(c['candidate_id']+':total_all_15',n==sum(values) if all(x is not None for x in values) else n is None)
        if n is not None:check(c['candidate_id']+':new_cost_all_3_scales',close(c['estimated_T_attempt_wall_s'],sum(rmap[sc][method]*means[sc,method] for sc in SCALES for method in METHODS)))
        check(c['candidate_id']+':not_adopted_no_wall_cap',c['adopted'] is False and c['decision']=='HOLD' and c['finite_wall_upper_bound_s'] is None)
        if c['variance_mode']=='observed' and all(group[sc,'C']['metrics']['D']['variance']==group[sc,'D']['metrics']['D']['variance']==0 for sc in SCALES):
            check(c['candidate_id']+':zero_variance_unidentified',n is None and all(c['quality_required_successes'][sc]['C'] is None and c['quality_required_successes'][sc]['D'] is None for sc in SCALES))
    check('all_generated_json_readable',all(isinstance(read(p),(dict,list)) for p in OUT.glob('*.json')))
    index={c['candidate_id']:c for c in cand}
    lines=['# 登録済み本実験候補の配分比較（未採用）','','登録したanalysis.pyの180候補を再計算せず整形した。全てS1〜S3・全5手法の費用を含む。必要成功数は品質区間を計算するための採用計画数、R_aは失敗を含む予定試行数。','','費用列は「T_attempt積算 / 観測gap・wrapper費用を加えた部分積算」の時間。初期管理前処理と最後の出力の未計測部分、将来の固定準備・集計を保証しない。有限wall上界・承認予算ではない。各群の観測分散へ対称にsigma_add²を加える仮定で、実測SDではない。率半幅は±15ポイント、各群の予備exact成功率下限を将来pと仮定し必要成功数へ90%到達を置く計画感度（全条件同時保証ではない）。','','|率半幅候補|率用R/条件|15条件総数|T費用 / gap等込みの部分費用 [h]|各条件の観測max×件数のT感度 h|','|---|---:|---:|---:|---:|']
    rate_refs=[]
    for hp in (.15,.1,.05):
        c=next(c for c in cand if c['scope']=='inherited_S2_primary' and c['variance_mode']=='observed' and c['h_D_km']==1 and c['rate_Wilson_worst_halfwidth']==hp and c['allocation']=='uniform_all_15')
        n=c['rate_only_total_attempts'];attempt=c['rate_only_estimated_T_attempt_s'];extra=(n-1)*cost['gap_stats_s']['mean']+n*cost['wrapper_outside_T_s']/75
        max_sensitivity=c['rate_required_attempts_each']*sum(g['T_attempt_all']['max'] for g in group.values())
        rate_refs.append({'rate_halfwidth':hp,'R_each':c['rate_required_attempts_each'],'total_15_conditions':n,'estimated_T_attempt_s':attempt,'estimated_gap_wrapper_s':extra,'estimated_measured_components_s':attempt+extra,'observed_max_T_attempt_sensitivity_s':max_sensitivity,'max_sensitivity_is_not_upper_bound':True,'distance_precision_identified':False,'initial_preparation_s':None,'final_output_s':None,'adopted':False})
        lines.append(f'|±{hp*100:g}ポイント|{c["rate_required_attempts_each"]}|{n}|{hours(attempt)} / {hours(attempt+extra)}|{hours(max_sensitivity)}|')
    tele=read(OUT/'TELEMETRY.json');rates=read(OUT/'RATES_AND_CENSORING.json')['rates']
    lines += ['', '## 取得状態・量子処理の実測', '', '計画取得率・検証済み可行計画の率は各15条件とも5/5。各条件の95%区間はWilson 56.55〜100%、Clopper–Pearson 47.82〜100%で、全条件同時の保証ではない。二項モデル下の率区間であり、全成功でも失敗確率0とはしない。既存目標は採用計画の最終D/Wによる記述用照合で、停止条件ではない。', '', '|規模|A目標到達|B|C|D|古典置換対照|', '|---|---:|---:|---:|---:|---:|']
    for sc in SCALES:
        vals=[]
        for method in METHODS:
            rr=next(x for x in rates if x['scale']==sc and x['method']==method and x['kind']=='inherited_target_met')['all_started']
            vals.append(f'{rr["numerator"]}/{rr["denominator"]}')
        lines.append('|'+sc+'|'+'|'.join(vals)+'|')
    lines += ['', '目標未達は計画取得失敗・物理的不可行ではない。厳密な親側初到達時刻は全行nullを維持し、終了Tを代入しない。', '', '|規模|D量子呼出し/初期を含む総start|実評価成功数|実測訓練shots|実測最終抽出shots|初期評価準備|cache hit|', '|---|---:|---:|---:|---:|---:|---:|']
    for sc in SCALES:
        bb=[b for t in tele if t['scale']==sc and t['method']=='D' for b in t['branches']]
        calls=sum(len(b['quantum_calls']) for b in bb);ev=sum(b['training_successes'] for b in bb);train=sum(b['observed_training_shots'] for b in bb);final=sum(b['observed_final_shots'] for b in bb)
        initial=sum(b['initial_evaluations'] for b in bb);cache=sum(b['cache_hits'] for b in bb)
        check(sc+':all_quantum_shots_observed',train==10000*ev and final==10000*calls and initial==calls and all(b['shots_accounting_complete'] for b in bb))
        lines.append(f'|{sc}|{calls:,}|{ev:,}|{train:,}|{final:,}|{initial:,}|{cache:,}|')
    peak=max(r['sampled_tree_peak_RSS_KiB'] for r in raw.values())/1024
    lines += ['', f'全255枝を回収し、登録coreへのpinと試行後の親affinity復帰を照合した。観測した子プロセス木RSS合計の最大は{peak:.1f} MiB。sampling間の厳密peak保証ではない。訓練実評価は初期評価を含み、cache hitは実評価/追加shotsへ加算しない。80は評価上限であり、各呼出しが80回実行したとはしていない。内部枝・呼出し・shotsは外側r_pilotへ加算しない。', '']
    lines += ['## 成功条件付き平均差の区間', '', '以下のW/T/Jは探索的な点ごとの95%独立Welch区間。各群成功5件で、有限分散・独立群・概ね正規という少数標本近似に条件付く。共有ホストの時間相関は除去・検証できておらず、Tの区間を無条件の被覆保証とはしない。Jは登録した各規模A全5会員の時間中央値等の参照値に条件付きで、参照推定自体の不確実性は含まない。距離差は全6比較とも平均0、両群観測分散0のため区間は理由付きnull。', '', '|規模|差|W差 分 [95%区間]|T差 秒 [95%区間]|J差 [参照条件付き95%区間]|', '|---|---|---|---|---|']
    def interval(c):
        delta=c['mean_difference'];bounds=c['CI95']
        return f'{delta:.4f} [null: {c["null_reason"]}]' if bounds is None else f'{delta:.4f} [{bounds[0]:.4f}, {bounds[1]:.4f}]'
    for sc in SCALES:
        for left in ('C','D_CLASSICAL_REPLACEMENT'):
            own={c['metric']:c for c in s['comparisons'] if c['scale']==sc and c['left']==left}
            lines.append('|'+sc+'|D−'+left+'|'+'|'.join(interval(own[k]) for k in ('W','T_program','J'))+'|')
    lines += ['', '両群0分散・成功数不足の区間はnullであり、0幅の精度保証には置換しない。非有意は同等・非劣性ではない。観測maxによる時間感度も、将来の時間上界ではない。', '']
    lines+=['','率の回数だけでは距離差の精度を保証しない。観測分散だけ／ゼロ分散のchi-square上側感度では品質Rは未識別のnull。以下は追加SDを仮定した感度のみ。','']
    for scope,title in [('inherited_S2_primary','既存継承案：S2主要、S1/S3探索的・点ごと95%'),('three_scale_primary_Bonferroni','3規模主要案：3つのD−C距離比較にBonferroni')]:
        lines += ['## '+title,'','既存継承案でもS1/S3へ同じhを課すのは、登録済みの追加的な精度感度であり、探索的比較を主要へ昇格する意味ではない。3規模主要案は各区間alpha=.05/3。Holm検定と通常95%区間の併用ではない。','','|追加SD/群 km|h km|均等の必要成功数 C/D各|均等R/条件|均等総数|均等費用 h|配分R_C/R_D (S1; S2; S3)|配分総数|配分費用 h|','|---:|---:|---:|---:|---:|---:|---|---:|---:|']
        for sd in (1,5,10):
            for h in (1,5,10):
                own=[c for c in cand if c['scope']==scope and c['variance_mode']=='additional_SD' and c['sigma_add_each_group_km']==sd and c['h_D_km']==h and c['rate_Wilson_worst_halfwidth']==.15]
                a=next(c for c in own if c['allocation']=='uniform_all_15');b=next(c for c in own if c['allocation']=='cost_variance_CD')
                pairs='; '.join(f'{b["R_a_by_scale"][sc]["C"]}/{b["R_a_by_scale"][sc]["D"]}' for sc in SCALES)
                lines.append(f'|{sd}|{h}|{a["quality_required_successes"]["S2"]["C"]}|{a["R_a_by_scale"]["S2"]["D"]}|{a["total_attempts_all_scales"]}|{hours(a["estimated_T_attempt_wall_s"])} / {hours(a["estimated_with_gap_wrapper_s"])}|{pairs}|{b["total_attempts_all_scales"]}|{hours(b["estimated_T_attempt_wall_s"])} / {hours(b["estimated_with_gap_wrapper_s"])}|')
        lines+=['','費用分散配分のA/B/古典置換対照は各規模39試行、A品質参照は1値とA計時・率の反復を区別する。各規模の必要C/D成功数、率±10/±5ポイントを含む全180行はMAIN_CANDIDATES.csv/JSONを参照。配分はT_attempt費用比に基づく整数近似で厳密最適とはしない。率用の最低試行数と成功数換算を同時に最適化した配分ではないため、率精度が件数を決める行では均等案より高費用になることもある。安い案を自動採択しない。','']
    lines += ['## 計測・保全の補足','','各試行前の管理preflightは、元の計時器とは別に全規模の入力・登録source・依存ファイルをhash照合する。元のT内の入力hash確認・読込は省略していない。これは全75試行に共通の登録済み管理処理で、旧データは費用・分散へ混ぜない。照合I/OはOS cacheへ影響し得る。完全coldや旧実行との計時環境同一性は主張しない。cache clear/prefetchや手法別暖機、実行途中のI/O高速化はしていない。','','wrapper外の管理preflight等は主に試行間gapに含む。初回coordinator記録前の管理準備と最終の出力は別計時しておらずnullであり、import-only setupを全準備としない。MAIN_CANDIDATESのgap/wrapper込み列も、未知の固定準備・最終出力を含む完全な総費用保証ではない。登録・解析・最終監査の観測時間は個別のTIMING JSONを参照。親HWMは共通coordinatorの生存期間中のhighwaterで、各試行固有のpeakではない。','','開始前後に完了したgit statusはREADME/AGENTS/.gitignore/src/kmd_toc/scripts/configs/toc_deliveryの対象範囲のみで差分なし。全体status/diffは無関係な過去ログのNFS読込みが続いたため実行前に停止し、全体cleanを確認したとはしない。保全hash監査はBASELINE_HASHESの839ファイルが対象。旧評価イベントログ全件を個別に再hashしたとはしない。旧namespaceへの書込み、commit/pushは行っていない。','','集計CLIは全JSON/CSVと完了要約の出力後、ツールから終了コード143が報告された。原因は未特定。再試行や実規模試行の追加で埋めず、AGGREGATE_OUTPUT_AUDITで全ID・CSV/JSON行数・費用の新規試行由来・未採用/上界なし・0分散nullを独立に照合した。これは75試行の失敗・中断ではない。','','## 再現補足','','REPRODUCE.mdのaggregate/finalize後、既存Pythonで `python -B docs/research/non_time_variance_pilot_20261117_v1/postcollection_report.py --finish` を実行すると本補足と出力整合性監査を再作成する。実規模計画作成は起動しない。追加したファイルはpostcollectionの監査・整形用で、登録済みanalysis.pyとその推定値は変更しない。','','SOURCE_SNAPSHOT.tar.gzとSUPPORTING_ASSETS.tar.gzを別ディレクトリへ、supporting→primary sourceの順で復元する。VeRyPy資産はVERYpy_SOURCE_SNAPSHOT/PROVENANCE/LICENSE、凍結入力はREGISTEREDの既存絶対パスとhashを使い、需要・ODを再生成しない。元作業treeへ上書き展開しない。異なるホスト・コア・依存条件のTをこの標本へ混ぜない。本実験manifestは最後までHOLD。']
    (DOC/'CANDIDATE_COMPARISON.md').write_text('\n'.join(lines)+'\n')
    write(OUT/'RATE_PRECISION_COST_REFERENCE.json',rate_refs)
    audit={'pass':all(c['pass'] for c in checks),'scope':'postcollection output integrity; no extra planning, no estimator change','analysis_cli_reported_exit_code':143,'analysis_exit_reason':'unidentified; outputs and completion summary emitted before reported termination','registered_analysis_source_unchanged':sha(DOC/'analysis.py')==m['source_hashes'][str((DOC/'analysis.py').relative_to(ROOT))],'postcollection_script_sha256':sha(Path(__file__)),'checks':checks}
    write(OUT/'AGGREGATE_OUTPUT_AUDIT.json',audit)
    if finish:
        base=read(OUT/'FINAL_AUDIT.json');base['postcollection_output_integrity']= {k:v for k,v in audit.items() if k!='checks'};base['process_recovery_audit']=read(OUT/'PROCESS_RECOVERY_AUDIT.json');base['measurement_scope_and_limits']='MEASUREMENT_SCOPE_AND_LIMITS.json';base['full_git_status_verified']=False
        base['pass']=base['pass'] and audit['pass'] and audit['registered_analysis_source_unchanged'] and not base['process_recovery_audit']['remaining_registered_children']
        write(OUT/'FINAL_AUDIT.json',base);write(DOC/'FINAL_AUDIT.json',base)
        report=DOC/'FINAL_REPORT.md';text=report.read_text();marker='\n## 登録済み候補の配分比較・計測範囲の補足\n';text=text.split(marker)[0]
        text+=marker+'\n全精度・両配分の具体表、管理I/Oと未計測の固定準備/出力、保全・集計CLI終了状態の範囲は [CANDIDATE_COMPARISON.md](CANDIDATE_COMPARISON.md) を参照。主Tは変更せず、登録済み解析の180行を整形した。\n\n'+ '\n'.join(lines[2:])+'\n'
        report.write_text(text)
        status=read(DOC/'COMPLETION_STATUS.json');status.update(pass_audit=base['pass'],postcollection_integrity_pass=audit['pass'],main_decision='HOLD',main_started=False);write(DOC/'COMPLETION_STATUS.json',status)
    write(OUT/'POSTCOLLECTION_REPORT_TIMING.json',{'wall_s':time.perf_counter()-begin,'outside_T':True,'scope':'output validation, formatting, reporting supplemental observed-cost components; no planning'})
    print(json.dumps({'postcollection_pass':audit['pass'],'registered_analysis_source_unchanged':audit['registered_analysis_source_unchanged'],'finish':finish,'checks':len(checks)}),flush=True)
    if not audit['pass']:raise SystemExit('POSTCOLLECTION_AUDIT_FAILURE')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--finish',action='store_true');run(p.parse_args().finish)
