"""Read-only audit of registered work; write reports only under new experiment ID."""
import json
import math
from pathlib import Path
import sys
import tarfile
import hashlib
import time
from pilot import ROOT,DOC,OUT,ID,SCALES,METHODS,read,digest,atomic,fingerprint,load_registration,validate,attempt_state

def number(v,digits=3):return 'null' if v is None else f'{v:.{digits}f}'

def finalize(root):
    started=time.perf_counter();root=Path(root).resolve();m=load_registration(root);s=read(root/'SUMMARY_DATA.json');tele=read(root/'TELEMETRY.json');checks=[]
    def check(name,ok,detail=None):checks.append({'check':name,'pass':bool(ok),'detail':detail})
    check('registration_fixed_75',len(m['runs'])==75 and m['run_list_hash']==fingerprint(m['runs']))
    check('no_external_old_observations',len(s['rows'])==75 and {r['run_id'] for r in s['rows']}=={r['run_id'] for r in m['runs']})
    main=read(root/'MAIN_MANIFEST.json');check('main_HOLD_nonexecutable',main['executable'] is False and not main['runs'] and main['decision']=='HOLD')
    check('main_formal_choices_unadopted',all(main[k] is None for k in ('R_a','h_D_adopted','rate_halfwidth_adopted','primary_scope_adopted','formal_seed_list','execution_order','A_time_reference_members')))
    try:validate(main);rejected=False
    except (ValueError,KeyError):rejected=True
    check('main_rejected_by_execution_validator',rejected)
    with tarfile.open(root/'SOURCE_SNAPSHOT.tar.gz') as archive:
        for name,h in m['source_hashes'].items():check('snapshot:'+name,hashlib.sha256(archive.extractfile(name).read()).hexdigest()==h)
    for name,h in m['source_hashes'].items():check('current_registered_source:'+name,digest(ROOT/name)==h)
    for r in s['rows']:
        path=root/'runs'/r['run_id']
        if r['attempt_collection_state']=='FINISHED':
            check(r['run_id']+':branch_recovery',len(r['branches'])==len(next(x for x in m['runs'] if x['run_id']==r['run_id'])['branches']))
            check(r['run_id']+':attempt_cost_retained',r['T_attempt'] is not None and r['T_attempt']>=0)
            if r['adoptable']:
                check(r['run_id']+':saved_plan',digest(path/'plan.json')==r['plan_sha256'])
                check(r['run_id']+':physical_adoption',r['plan_state']=='VALID' and r['validation_state']=='VALIDATED' and r['execution_state']=='NORMAL')
                check(r['run_id']+':main_T_definition',r['T_program']==r['T_attempt'] and r['T_kind']==m['T_kind'])
                eligible=[b for b in r['branches'] if b.get('adoptable')]
                winning=min(eligible,key=lambda b:(round(b['D']*10000),round(b['W']*60),b['branch_id']))
                check(r['run_id']+':selection_all_branches',winning['branch_id']==r['selected_branch_id'])
            else:check(r['run_id']+':null_failed_quality',all(r.get(k) is None for k in ('D','W','T_program')))
        else:check(r['run_id']+':unstarted_unfinished_not_success',not r['adoptable'] and r['T_program'] is None)
    for t in tele:
        for b in t['branches']:
            tag=t['run_id']+f":branch{b['branch_id']}"
            if b['state']=='NORMAL':
                check(tag+':native_single_thread',b['native_observed_threads']==1)
                check(tag+':one_core',len(b.get('affinity') or [])==1)
            if t['method']=='D' and b['state']=='NORMAL':
                check(tag+':all_pricing_calls',b['all_quantum_calls_processed'])
                check(tag+':actual_shots',b['observed_training_shots']==10000*b['training_successes'] and b['observed_final_shots']==10000*b['quantum_completed'])
                check(tag+':counter_reconcile',b['counter_shots_reconcile'])
                check(tag+':accounting_complete',b['shots_accounting_complete'])
                check(tag+':80_initial_inclusive_evaluations',b['max_evaluations_per_call_start'] is not None and b['max_evaluations_per_call_start']<=80)
    baseline=read(DOC/'BASELINE_HASHES.json')['files'];changed=[]
    for name,h in baseline.items():
        try:matches=digest(ROOT/name)==h
        except FileNotFoundError:matches=False
        if not matches:changed.append(name)
    preservation={'pass':not changed,'files_checked':len(baseline),'changed_or_missing':changed,
        'README_unchanged':'README.md' not in changed,'human_session_unchanged':'src/kmd_toc/human_comparison_v1/session.py' not in changed,
        'old_results_inputs_manifest_preserved':not any(x.startswith(('output/','configs/')) for x in changed)}
    atomic(DOC/'PRESERVATION_AFTER.json',preservation);check('protected_assets_preserved',preservation['pass'],changed)
    all_finished=s['not_started']==0 and s['unfinished']==0
    audit={'experiment_id':ID,'pass':all(c['pass'] for c in checks),'batch_list_finished':all_finished,
        'registered':75,'started':s['started'],'normally_ended':s['normally_ended'],'adopted':s['adopted'],'failed_settled':s['failed_settled'],
        'unfinished':s['unfinished'],'not_started':s['not_started'],'main_started':False,'main_decision':'HOLD',
        'formal_R_adopted':False,'additional_scale_attempts':0,'preservation':preservation,'checks':checks,
        'test_scope':'new fixture management/statistics tests and existing toc_termination_v1 only; not full repository regression',
        'legacy_regression':'previous report 127 pass/2 fail is historical, not claimed rerun or all-pass here'}
    atomic(root/'FINAL_AUDIT.json',audit);atomic(DOC/'FINAL_AUDIT.json',audit)
    lines=['# 非時間終了規則・新規予備反復と本実験候補', '',f'実験ID: `{ID}`。本実験は **HOLD / 未実行**。R・要求精度・主要比較の範囲は未採用。', '',
        f'登録75、開始{s["started"]}、正常終了{s["normally_ended"]}、採用{s["adopted"]}、確定失敗{s["failed_settled"]}、未完了{s["unfinished"]}、未実行{s["not_started"]}。r_pilot=5/条件。'+('固定予備一覧の回収が終了した。' if all_finished else '部分完了であり75件実行完了とはしない。'), '',
        '## 1. 固定内容', '',
        '既存終了規則・操作予算・訓練/最終10000shots・凍結需要/有向Route OD・物理制約・4物理コア（内部4枝各1コア/native1thread）・A凍結規則/AS4GiB・RSS32GiB・全枝回収後D0.1m→W秒→branch ID採択を維持。既存timed executeを変更しない。旧240/150秒制限を復活せず75件を逐次実行。旧15/90件は標本/費用へ不算入。入力各M=1、S1⊂S2⊂S3は1需要family。', '',
        'Tは親の入力hash確認/読込・fresh子起動/import・処理・全枝回収・転送/選択・最終二重検査を含む経過時間。CPU時間とは別。既存NFS/依存prefixを維持、意図的な暖機/cache操作/I/O高速化なし。共有ホスト変動は残る。', '',
        '## 2. 全15条件の実測', '',
        'D=総距離km、W=積込待機分、T=計画作成秒。平均±標本SD（この5件で観測した散らばり）。採用成功だけの品質・T。全trial ID/中央値/min/maxはSUMMARY_DATAとCONDITION_SUMMARYに保存。A品質は決定的参照で独立品質標本5件とはしない。', '',
        '|規模|手法|採用/開始|D 平均±SD|W 平均±SD|T 平均±SD|T中央値 [min,max]|', '|---|---|---:|---:|---:|---:|---:|']
    for g in s['conditions']:
        k=g['metrics'];t=k['T_program']
        lines.append(f'|{g["scale"]}|{g["method"]}|{g["adopted"]}/{g["started"]}|{number(k["D"]["mean"],4)}±{number(k["D"]["sample_SD"],4)}|{number(k["W"]["mean"],4)}±{number(k["W"]["sample_SD"],4)}|{number(t["mean"])}±{number(t["sample_SD"])}|{number(t["median"])} [{number(t["min"])},{number(t["max"])}]|')
    lines+=['','## 3. 0分散・状態・時間・候補由来', '',
        '標本SD=0は真の分散0・同等性・優越性・精度保証を示さない。両群0分散のWelch区間/品質必要Rは理由付きnull。通常bootstrapで未知の変動は復元できない。D−CとD−置換は独立群の成功条件付き差、同じ反復番号で対応解析せず、少数標本の正規/Welch近似。非有意は同等/非劣性ではない。S2距離D−Cを継承基準とし、他の比較は探索的。', '',
        '|規模|比較|距離平均差 km|95%区間 / null理由|W差 分|T差 秒|','|---|---|---:|---|---:|---:|']
    for sc in SCALES:
        for left in ('C','D_CLASSICAL_REPLACEMENT'):
            cs=[c for c in s['comparisons'] if c['scale']==sc and c['left']==left];by={c['metric']:c for c in cs};c=by['D']
            lines.append(f'|{sc}|D−{left}|{number(c["mean_difference"],4)}|{c["CI95"] or c["null_reason"]}|{number(by["W"]["mean_difference"],4)}|{number(by["T_program"]["mean_difference"])}|')
    lines+=['','|規模|C採用候補由来|CW訪問順集合一致 / 採用C|CP状態|','|---|---|---:|---|']
    for sc in SCALES:
        own=[r for r in s['rows'] if r['case_id']==sc and r['method']=='C' and r['adoptable']]
        sources=dict(__import__('collections').Counter(r['provenance'].get('source') for r in own));cp=sorted({x for r in own for x in r['provenance'].get('CP_states',[]) if x})
        lines.append(f'|{sc}|{sources}|{sum(r["provenance"].get("CW_visit_order_set_equal") is True for r in own)}/{len(own)}|{cp}|')
    lines+=['', '同じ訪問順集合でのW減少は完成計画の待機減少であり、Routingの順序改善・CP最適性・事前固定車両割当の証拠ではない。CPのFEASIBLEは可行解取得、OPTIMALの証明とは異なる（[OR-Tools公式](https://developers.google.com/optimization/cp/cp_solver)）。Routing由来の採用を成功条件にしていない。Dはstatevectorシミュレータであり実機QPU性能/優位性は測っていない。', '',
        '時間の長い記録も全て残し、主Tの補正・除外なし。旧A・S2の85.735秒や約63.4秒の記録遅れ増加の解釈はINTERPRETATION_NOTESを参照。新ログの測定時刻差/記録elapsed差はTELEMETRYへ保存したが原因・全Tへの寄与は未特定。perf_counterの経過時間とprocess_time/CPUは別（[Python公式](https://docs.python.org/3/library/time.html)）。', '',
        '取得/検証可行/既存目標の率はRATES_AND_CENSORINGに分子・分母・Wilson/Clopper–Pearson両側95%区間を保存。全成功でも失敗確率0ではない。未実行は分母外、未確定開始があれば全開始率区間保留。未取得は物理的不可行の証明ではない。既存目標未達と未取得を分離。親初到達時刻は未観測nullを維持。率区間は条件ごとの区間で全条件同時95%ではない（[NIST率CI](https://www.itl.nist.gov/div898/handbook/prc/section2/prc241.htm)）。', '',
        '## 4. 未採用の本実験候補', '',
        '距離差のCI半幅hは、平均差をどの幅で推定したいかという候補。必要成功数と失敗を含む総試行R_aは別。全3規模/全5手法の費用を含む。均等15条件案とC/D費用分散配分をMAIN_CANDIDATES.csvに併記。A品質参照1とA時間/率反復を区別。', '',
        '観測分散点推定、正の分散に正規性を仮定したchi-square上側感度、各群へ追加SD1/5/10kmを仮定する感度を分離。ゼロ分散へchi-square式の0を入れて上界とはしない。追加SDは観測ではなく未採用の仮定。成功数への総試行換算は新予備のexact成功率下限を将来pと仮定する二項モデル、各cell90%の計画感度で将来/全条件同時保証ではない。', '',
        '|率のWilson最悪半幅候補|各条件の率用試行数|15条件合計（距離精度は未保証）|','|---|---:|---:|']
    for hp in (.15,.1,.05):
        from kmd_toc.comparison_v1.design import rate_count
        n=rate_count(hp);lines.append(f'|±{hp*100:g}ポイント|{n}|{15*n}|')
    lines+=['','下表は率±15ポイントを組み合わせた均等15条件案。全候補のR配分、必要成功数、全3規模の期待費用はCSV/JSONにある。費用はT_attempt平均の積算（失敗も含む）で有限時間上界ではない。', '',
        '|比較範囲|分散の仮定|h km|条件ごとの均等R|全試行数|期待T費用 時間|','|---|---|---:|---:|---:|---:|']
    candidates=read(root/'MAIN_CANDIDATES.json')
    for c in candidates:
        if c['allocation']!='uniform_all_15' or c['rate_Wilson_worst_halfwidth']!=.15:continue
        if c['variance_mode']=='normal_variance_upper':continue
        r=c['R_a_by_scale']['S2']['D'];v='観測のみ' if c['variance_mode']=='observed' else f'各群追加SD={c["sigma_add_each_group_km"]}km'
        lines.append(f'|{"S2主要/他探索的" if c["scope"]=="inherited_S2_primary" else "3規模主要Bonferroni"}|{v}|{c["h_D_km"]}|{r}|{c["total_attempts_all_scales"]}|{number(c["estimated_T_attempt_wall_s"]/3600 if c["estimated_T_attempt_wall_s"] is not None else None,2)}|')
    cost=read(root/'COST_ACCOUNTING.json')
    lines+=['', '既存継承案はS2のD−C距離1比較を主要としS1/S3は探索的95%。3規模主要案は3距離比較のfamilyへBonferroni（各alpha=.05/3）を適用する候補。Holm検定補正と通常95%区間を混同しない。どちらも未採用。', '',
        f'本予備T_attempt合計={number(cost["T_attempt_total_s"])}秒、wrapperのT外合計={number(cost["wrapper_outside_T_s"])}秒、試行間gap平均={number(cost["gap_stats_s"]["mean"])}秒。登録/共通準備/集計/出力はCOST_ACCOUNTING/ANALYSIS_TIMINGに別記。将来のgap/wrapper費用感度もCSVへ別列で表示し、T内費用と二重加算しない。内部並列は測定Tに含まれ4で再除算しない。4×wallは予約core時間proxyでCPU時間ではない。旧240秒×件数capは作らない。1/4/24時間との比較は期待費用参考で承認予算/必ず収まる上界ではない。', '',
        '## 5. 本実験前の選択と限界', '',
        'ユーザーが選ぶ事項: h_D（1/5/10km等）、率半幅、主要比較範囲（既存継承/3規模主要）、分散・成功率・費用の計画仮定、配分と費用を踏まえた正式R。その後、正式seed/順序/A時間参照会員と停止一覧を新規登録する。本予備seed/会員を流用しない。', '',
        '現在のデータでは真のゼロ分散・小確率の失敗/変動・需要間分散・厳密wall上界・最適性・量子優位性を決められない。5回の十分性を認定せず、旧文献も当該shots/評価/件数の十分性を保証しない。本予備を見て主要指標を選び直したり追加実規模バッチを自動実行しない。', '',
        '## 監査・再現', '',
        f'監査pass={audit["pass"]}、保全pass={preservation["pass"]}。最終状態はFINAL_AUDIT.json、テスト結果はVALIDATION.log/xml。全リポジトリ回帰の全通過は主張しない。README/旧成果/凍結入力/OD/A/無関係human sessionを保全し、commit/pushなし。', '',
        f'出力正本: `output/toc_delivery/{ID}/`。REGISTERED/PILOT_MANIFEST/REGISTRATION_LOCK/SOURCE_SNAPSHOT/ENVIRONMENT、runs、PILOT_SUMMARY/CONDITION_SUMMARY、SUMMARY_DATA、TELEMETRY、RATES_AND_CENSORING、MAIN_CANDIDATES、VARIANCE_SENSITIVITY、MAIN_MANIFEST、FINAL_AUDITを保存。文書正本は本ディレクトリ、実行入口はpilot.py。再現はREPRODUCE.md。']
    (DOC/'FINAL_REPORT.md').write_text('\n'.join(lines)+'\n')
    atomic(DOC/'COMPLETION_STATUS.json',{k:v for k,v in audit.items() if k!='checks'})
    atomic(root/'FINALIZATION_TIMING.json',{'wall_s':time.perf_counter()-started,'outside_T':True,'scope':'preservation/snapshot/result audit and final report output'})
    print(json.dumps({k:v for k,v in audit.items() if k not in ('checks','preservation')}),flush=True)
if __name__=='__main__':finalize(Path(sys.argv[1]) if len(sys.argv)>1 else OUT)
