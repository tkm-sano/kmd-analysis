"""Publication-readable record from new measurements only; no experiment launches."""
import csv
import gzip
import hashlib
import json
from pathlib import Path
from statistics import mean
import xml.etree.ElementTree as ET

from .study import OUT,DOC,read,dump
from .analyze import analyze,csvout,ANALYSIS_SOURCE_SHA256


def table(name):
    with (OUT/name).open() as stream:return list(csv.DictReader(stream))


def number(value, digits=5):
    return '—' if value in (None,'') else f'{float(value):.{digits}f}'


def main(reuse=False):
    if reuse:
        provenance=read(OUT/'ANALYSIS_PROVENANCE.json')
        current={str(p.relative_to(OUT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((OUT/'groups').glob('*/GROUP.json'))}
        if provenance['analysis_source_sha256']!=ANALYSIS_SOURCE_SHA256 or provenance['group_hashes']!=current or not provenance['figures_generated']:
            raise ValueError('CANNOT_REUSE_STALE_ANALYSIS')
        summary=read(OUT/'SUMMARY.json')
    else:summary=analyze(True)
    groups=table('GROUPS.csv');grid=table('ALL54.csv');branches=table('BRANCHES.csv');calls=table('CALLS.csv');iterations=table('ITERATIONS.csv')
    # csvout writes JSON null as an empty cell; only an explicit 0 is known zero.
    unknown_inflight=[c for c in calls if c['inflight_shots']!='0']
    end_rows=[];group_records={g['tag']:read(OUT/'groups'/g['tag']/'GROUP.json') for g in groups}
    for branch in branches:
        group=group_records[branch['tag']]
        recorded=next(b for b in group['branch_results'] if b['branch']==int(branch['branch']))
        effective='COMPLETE' if recorded['returncode']==0 and recorded['status']=='COMPLETE' else 'INCOMPLETE'
        end_rows.append({'tag':branch['tag'],'scale':branch['scale'],'branch':branch['branch'],
            'saved_checkpoint_status':branch['status'],'effective_branch_end_status':effective,
            'group_status':group['status'],'group_end_reason':group['reason'],'returncode':recorded['returncode']})
    csvout('BRANCH_END_STATUS.csv',end_rows)
    complete=[g for g in groups if g['status']=='COMPLETE' and g['P']=='4' and g['outer_seed']=='9201']
    candidate_status={scale:'CONDITIONAL' if any(g['scale']==scale and
        (float(g['delta_D_branch_mean'])<0 or float(g['delta_W_branch_mean'])<0) for g in complete) else 'HOLD'
        for scale in ('S1','S2','S3')}
    policy_drift=(DOC/'SOURCE_PIN_ALERT.json').exists()
    final_status='HOLD' if policy_drift else summary['decision']
    scale_status={scale:'HOLD' if policy_drift else status for scale,status in candidate_status.items()}
    gate_rows=[]
    for path in sorted((OUT/'gates').glob('*.json')):
        record=read(path)
        gate_rows.append({'tag':path.stem,'allowed':record.get('allowed'),'reason':record.get('reason'),
            'forecast_s_not_measurement':record.get('predicted_s_not_measurement',record.get('conservative_predicted_s')),
            'remaining_batch_s':record.get('remaining_batch_s'),
            'original_probe_forecast_s_not_measurement':record.get('original_probe_gate',{}).get('conservative_predicted_s'),
            'source':str(path.relative_to(OUT))})
    csvout('EXECUTION_GATES.csv',gate_rows,['tag','allowed','reason','forecast_s_not_measurement','remaining_batch_s','original_probe_forecast_s_not_measurement','source'])
    index={(g['scale'],int(g['n']),int(g['K']),int(g['R'])):g for g in complete}
    lines=['# p=2・固定shots下のn/K/R実証比較','',
        f"**正式採用判定：{final_status}。n/K/R採用値は未確定。** 登録済み旧版内の実測候補判定は{summary['decision']}で保持し、現在正本との版不一致を別に判定する。p2/最適化1,000/最終10,000の承認値は維持。本実験は未開始。",'',
        f"新ID `nkr_p2_20261120_v1`。54条件中、完了{summary['complete_54_conditions']}、未完{summary['incomplete_54_conditions']}、進行中{summary['in_progress_54_conditions']}、未実行{summary['not_run_54_conditions']}。終了群の集計では、別枠の単一枝probeを含む新規完了量子呼出し{summary['actual_quantum_calls_complete']}件、完了標本化を記録した最適化評価{summary['actual_objective_evaluations']}回。記録済み学習shots {summary['actual_optimization_shots']:,}、最終shots {summary['actual_final_shots']:,}。進行中の群とテスト内の小回路はこの集計に含めない。",'',
        f"未使用seed確認は54条件表の外に別群で保存した。完了{sum(g['P']=='4' and g['outer_seed']!='9201' and g['status']=='COMPLETE' for g in groups)}群、途中停止{sum(g['P']=='4' and g['outer_seed']!='9201' and g['status']!='COMPLETE' for g in groups)}群。量子呼出しが完了していても、全R・後処理を完走していない群を再現性確認の成功には数えない。",'',
        f"開始後の完了記録がなくin-flight shotsが不明な呼出しは{len(unknown_inflight)}件。該当がある場合、上記は完了記録に基づく既知のshots数であり、厳密な総消費数は未確定。途中callの標本化完了とoptimizer callbackの返却・収束を同一視せず、完了callのnfevはraw監査でscipy値と照合する。",'',
        '[監査](AUDIT.md)、[再現](REPRODUCE.md)、[論文用方法記述](PAPER_METHODS.md)。計算/安全/適応的順序の事前登録はoutputのPROTOCOL、FOLLOWUP_PROTOCOL_V3、FOLLOWUP_SELECTION_V3、gates。起動判定と予測（実測ではない）はEXECUTION_GATES.csvに分ける。V1も削除していない。新結果だけを解析し、旧p1/旧selectorを追加反復として混ぜない。','',
        '## 全54条件','',
        'D/Wは4内部枝の記述平均差（変更後−保存初期計画）。平均は一つの実計画ではない。個別の同一計画D/Wの組はBRANCHES/CANDIDATES.csv、可行非劣計画はNONDOMINATED_PLANS.csvと候補plan gzipに保存する。未完の差は途中の実測で、完了群の品質順位に入れない。秒は保存計画改善の親wallであり、本実験の総計画作成時間ではない。','',
        '|S|n|K|R|実E（4枝）|実U（集合和）|被覆率|重複率|ΔD平均 km|ΔW平均 min/運行|親秒|判定|',
        '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|']
    labels={'COMPLETE':'完了','INCOMPLETE':'途中停止','NOT_RUN':'未実行','IN_PROGRESS':'進行中'}
    for g in grid:
        lines.append('|'+ '|'.join([g['scale'],g['n'],g['K'],g['R'],g['E'] or '—',g['U'] or '—',number(g['coverage'],4),number(g['repeat_rate'],4),
            number(g['delta_D_branch_mean']),number(g['delta_W_branch_mean']),number(g['parent_wall_s'],2),labels[g['status']]])+'|')
    lines+=['','完全な表は`output/nkr_p2_20261120_v1/ALL54.csv`。E_plan=nKR（1枝）/4nKR（4枝）は理論数で、実E/Uの代用にしない。未実行値は0や予測で埋めない。','',
        '## 実使用量・可行性・資源','',
        '|群|状態|量子完了|実目的評価|最適化shots|最終shots|量子秒・枝合計|worker CPU秒合計|最大worker MiB|可行計画取得call率|可行/検査候補|採択call率|',
        '|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for g in groups:
        lines.append('|'+ '|'.join([g['tag'],g['status'],g['quantum_calls_completed'],g['optimizer_evaluations'],
            g['optimization_shots_actual'],g['final_shots_actual'],number(g['quantum_wall_workers_sum_s'],2),number(g['CPU_workers_sum_s'],2),
            number(g['max_worker_RSS_MiB'],2),number(g['plan_yield'],4),g['top3_feasible_candidates']+'/'+g['top3_checked_candidates'],number(g['adoption_rate'],4) if g['status']=='COMPLETE' else '—（未完）'])+'|')
    lines+=['','可行率は容量選別後に検査した最大3標本候補についての率であり、最終10,000全shotsの物理可行率は未測定null。未完群の可行率はassessmentが保存された呼出し内の条件付き値、採択率は未確定。GROUPS.csvの未完群のadoption_rateは未確定採否を含む暫定下限で、完了群の順位へ使わない。BRANCHES.statusは保存checkpoint時点の状態で、停止後の実終了はBRANCH_END_STATUS.csvのreturncode/群終了理由と照合する。量子秒・worker CPU秒の枝合計は親wallではない。全群の同時ピークRSS・親CPU・初期計画生成・本実験の総計画作成時間は未測定null。構築/最適化/最終抽出/復号/再構築/検証/DW/採択保存の内訳はCALLS/BRANCHES.csvに保持する。',
        f"optimizerがsuccessを返した完了呼出しは{sum(int(g['optimizer_reported_success_calls']) for g in groups)}件、success=Falseは{sum(int(g['optimizer_reported_unsuccessful_calls']) for g in groups)}件。停止messageと実評価数はCALLS.csvに保存する。評価予算で停止した量子実行の完了を、最適化収束の成功とは呼ばない。未完群の量子秒は完了CALLの記録合計で、途中で打ち切った処理の秒数は未計測。親wallは停止・回収・親検証までを含む。",'',
        '## 12問への回答','', '### 1・2：n10対n12の品質と追加費用','',
        '|S|K|R|ΔD n10|ΔD n12|ΔW n10|ΔW n12|親秒 n10|親秒 n12|時間比 n12/n10|',
        '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    pairs=[]
    for (scale,n,K,R),g in index.items():
        if n!=10 or (scale,12,K,R) not in index:continue
        h=index[scale,12,K,R];ratio=float(h['parent_wall_s'])/float(g['parent_wall_s'])
        pairs.append({'scale':scale,'K':K,'R':R,'n10':g,'n12':h,'ratio':ratio})
        lines.append('|'+ '|'.join([scale,str(K),str(R),number(g['delta_D_branch_mean']),number(h['delta_D_branch_mean']),number(g['delta_W_branch_mean']),number(h['delta_W_branch_mean']),number(g['parent_wall_s'],2),number(h['parent_wall_s'],2),number(ratio,3)])+'|')
    if not pairs:lines+=['','同じS/K/Rで両nが完了した比較はまだなく、一方の品質優越性は未判定。']
    lines+=['','表は同一外側seed9201・対応した内部branch/r/kの観測。DとWの相反を保ち、一方の距離だけでn12を採用しない。probeの局所秒/RSSもGROUPS.csvと図09に分ける。n12の追加費用を、同じ回数の実測比較と未実行組合せへの予測で混同しない。','',
        '### 3・4：KとRの単独増加','']
    contrasts=[]
    for scale,V in [('S1',10),('S2',20),('S3',40)]:
        for n in (10,12):
            base=index.get((scale,n,V//2,5))
            if not base:continue
            for axis,K,R in [('K',V,5),('K',2*V,5),('R',V//2,13),('R',V//2,25)]:
                other=index.get((scale,n,K,R))
                if not other:continue
                row={'scale':scale,'n':n,'axis':axis,'K':K,'R':R,
                    'additional_delta_D':float(other['delta_D_branch_mean'])-float(base['delta_D_branch_mean']),
                    'additional_delta_W':float(other['delta_W_branch_mean'])-float(base['delta_W_branch_mean']),
                    'additional_parent_s':float(other['parent_wall_s'])-float(base['parent_wall_s'])}
                contrasts.append(row)
                lines.append(f"- {scale}/n{n}：基準K={V//2},R5→K={K},R{R}。追加ΔD={row['additional_delta_D']:.6f}km、追加ΔW={row['additional_delta_W']:.6f}分/運行、追加親wall={row['additional_parent_s']:.2f}秒。")
    csvout('AXIS_COMPARISONS.csv',contrasts,['scale','n','axis','K','R','additional_delta_D','additional_delta_W','additional_parent_s'])
    if not contrasts:lines+=['完了した単独軸比較はなく、K/Rの優劣は未判定。']
    lines+=['','未実行のK2V/R25に効果を補完しない。同程度という統計的同等性の規則・許容差は新設せず、記述的D/W/時間のパレート候補を保持する。','',
        '### 5：追加改善は継続するか','',
        'ITERATIONS.csv/GROUP_ITERATIONS.csvと図05に、完了反復ごとの実際のD/W・採択・被覆・重複・時間を保存する。停滞した観測反復から未実行のR25以降を推定せず、改善していても一般的継続を保証しない。','']
    for g in complete:
        points=[r for r in iterations if r['tag']==g['tag']]
        quiet=[]
        for r in sorted({int(p['r']) for p in points}):
            selected=[p for p in points if int(p['r'])==r]
            if len(selected)==4 and all(float(p['delta_D_r'])==0 and float(p['delta_W_r'])==0 for p in selected):quiet.append(r)
        if quiet:lines.append(f"- {g['tag']}：全4枝で追加D/Wが0だった完了反復={quiet}。")
    lines+=['','### 6：K×Rの交互作用','']
    interactions=[]
    for scale,V in [('S1',10),('S2',20),('S3',40)]:
        for n in (10,12):
            keys=[(scale,n,V//2,5),(scale,n,V,5),(scale,n,V//2,13),(scale,n,V,13)]
            if not all(k in index for k in keys):continue
            a,k,r,b=[index[key] for key in keys]
            out={'scale':scale,'n':n,'K_low':V//2,'K_high':V,'R_low':5,'R_high':13,
                'interaction_D':float(b['delta_D_branch_mean'])-float(k['delta_D_branch_mean'])-float(r['delta_D_branch_mean'])+float(a['delta_D_branch_mean']),
                'interaction_W':float(b['delta_W_branch_mean'])-float(k['delta_W_branch_mean'])-float(r['delta_W_branch_mean'])+float(a['delta_W_branch_mean'])}
            interactions.append(out);lines.append(f"- {scale}/n{n}：実測4条件の記述交互作用I_D={out['interaction_D']:.6f}km、I_W={out['interaction_W']:.6f}分/運行。")
    csvout('INTERACTIONS.csv',interactions,['scale','n','K_low','K_high','R_low','R_high','interaction_D','interaction_W'])
    if not interactions:lines+=['完了した4条件の組がなく、交互作用は未確認。単独軸の効果を足し合わせてjointの実績としていない。']
    else:lines+=['','I=Y(K_high,R_high)−Y(K_high,R_low)−Y(K_low,R_high)+Y(K_low,R_low)。固定需要・1選別seedでの記述値で、母集団交互作用や統計的有意性の証明ではない。']
    lines+=['','### 7：nKR>Nのときの実探索数','']
    over=[b for b in branches if b['status']=='COMPLETE' and int(b['K'])*int(b['R'])*int(b['n'])>{'S1':1000,'S2':2000,'S3':4000}[b['scale']]]
    if over:
        for b in over:lines.append(f"- {b['tag']}/branch{b['branch']}：nKR={int(b['K'])*int(b['R'])*int(b['n'])}、実E={b['E']}、実U={b['U']}、coverage={float(b['coverage']):.4f}。")
    else:lines+=['1枝nKR>Nの完走条件は未実行で、該当時の実Uは未判定。4枝合計E>Nの例と取り違えない。']
    lines+=['','### 8・9：被覆・重複と改善','',
        '図06/07、CALLS.csvのnew/repeated_customer_slots、all_customers_repeated、adoptedを参照。集合和Uを使い、枝間重複を除く。被覆率は全体D/Wの代理目的ではなく、探索量の診断である。','']
    repeated=[c for c in calls if c['all_customers_repeated']=='True' and c['adopted'] not in ('','None')]
    lines.append(f"採否が保存された全件既探索IDの局所呼出し{len(repeated)}件のうち採択は{sum(c['adopted']=='True' for c in repeated)}件。これは重複を含む候補による観測であり、重複自体の因果効果ではない。選択・状態・seedを統制した反実仮想比較は行っていない。")
    lines+=['','今回の中央連続ブロック選択には到達範囲の制約がある。以下は初回CALLの全便中央ID集合と、全実測CALL・採択後の便別件数を照合した診断である。便別件数の変化や中央集合外の探索があれば、固定中央集合を普遍的な上界としない。候補方式を今後変える場合は別版として再比較し、今回のK/R効果に合算しない。','',
        '|群|初期中央ID集合|実U|中央集合外U|採択による便別件数変更数|','|---|---:|---:|---:|---:|']
    for g in complete:
        if g.get('initial_center_pool_size','')!='':
            lines.append('|'+ '|'.join([g['tag'],g['initial_center_pool_size'],g['U'],g['U_outside_initial_centers'],g['adopted_trip_cardinality_changes']])+'|')
    lines+=['','### 10：S1〜S3共通設定を正式採用できるか','',
        '正式値は未確定。観測上の非劣候補はPARETO_CONDITIONS.csv。全規模での必要な比較、未使用seed確認、未完条件の解決、時間契約が不足する限り共通n/K係数/Rを埋めない。規模別に効果・費用が異なる可能性も保持する。','',
        '### 11：観測範囲で最小費用の有効設定','']
    for scale in ('S1','S2','S3'):
        positive=[g for g in complete if g['scale']==scale and (float(g['delta_D_branch_mean'])<0 or float(g['delta_W_branch_mean'])<0)]
        if positive:
            g=min(positive,key=lambda r:float(r['parent_wall_s']))
            lines.append(f"- {scale}：観測した完了群内ではn={g['n']},K={g['K']},R={g['R']}が最小親wall={float(g['parent_wall_s']):.2f}秒。ΔD記述平均={float(g['delta_D_branch_mean']):.6f}km、ΔW={float(g['delta_W_branch_mean']):.6f}分/運行。正式採択ではない。")
        else:lines.append(f'- {scale}：有効な完了条件がなく未判定。')
    lines+=['','### 12：共通Tに不足する情報','',
        '初期計画生成を含む計時範囲の合意、正式optimizer評価予算、n/K/Rの採択、全体Dの実装統合、各規模/optimizer seed/需要に対する費用分布、未完量子呼出しの扱い、期限時点の可行計画採用・全枝停止規則、J/要求精度・統計支持規則が必要。今回の保存計画改善秒や安全停止上限をTへ置換しない。','',
        '## 未使用seedによる確認','',
        '|群|seed|ΔD枝平均|ΔW枝平均|親秒|状態|','|---|---:|---:|---:|---:|---|']
    for g in groups:
        if g['P']=='4' and g['outer_seed']!='9201':lines.append('|'+ '|'.join([g['tag'],g['outer_seed'],number(g['delta_D_branch_mean']),number(g['delta_W_branch_mean']),number(g['parent_wall_s'],2),g['status']])+'|')
    lines+=['','確認対象以外のK/R/nへの再現性を推定しない。4枝は独立4試行ではなく、外側seedの確認も固定需要内のoptimizer変動に限る。','',
        '## 正式採択表','', '|項目|S1|S2|S3|','|---|---|---|---|',
        '|配送先総数|1,000|2,000|4,000|','|採用n|未確定|未確定|未確定|','|採用K|未確定|未確定|未確定|','|採用R|未確定|未確定|未確定|',
        '|p|2|2|2|','|最適化shots|1,000|1,000|1,000|','|最終抽出shots|10,000|10,000|10,000|']
    for field in ['延べ探索対象数','実探索配送先数','探索被覆率','重複探索率','D改善量','W改善量','計算時間']:
        lines.append(f'|{field}（正式採用条件）|未確定|未確定|未確定|')
    lines+=[f"|判定|{scale_status['S1']}|{scale_status['S2']}|{scale_status['S3']}|",'',
        'この表の未確定は実測がないという意味ではなく、正式採用条件の値を埋める根拠が未完であることを示す。実測は上の54表と各CSVに保持する。','',
        '## 図と限界','']
    for stem,title in [('01_nkr_D','n/K/Rと距離'),('02_nkr_W','n/K/Rと荷待ち'),('03_K_time','Kと実測親時間'),('04_R_time','Rと実測親時間'),('05_R_cumulative_DW','反復の累積D/W'),('06_coverage_DW','被覆とD/W'),('07_repeats_adoption','重複と採択率'),('08_DW_time_pareto','D/W/時間'),('09_n_resources','n別probe資源')]:
        lines.append(f'- {title}：[PNG](../../../output/nkr_p2_20261120_v1/figures/{stem}.png) / [PDF](../../../output/nkr_p2_20261120_v1/figures/{stem}.pdf)。')
    lines+=['','D/Wの図は完了した4枝条件を使い、未実行に点を打たない。図03のK軸はR5固定、図04のR軸はK=V/2固定。反復図は全4枝が完了した反復までの平均で、打切り後を延長しない。branch平均は記述用で単一計画ではない。量子実機・p1優越性・母集団効果・同時間最適性を実証していない。', '',
        '## 正式採用に必要な最小追加検証','',
        '1. 正式なoptimizer評価予算をK/R比較とは別に検証・承認する。最大8評価は全条件共通の予備設定であり、収束した本実験設定ではない。',
        '2. まず資源実測を踏まえた新しい事前登録でS3の4枝最小条件を完走し、n10/12を同一K/Rで比較する。今回は安全上限を緩めて強行しない。',
        '3. 各規模の生存候補について未実行の単独K/R軸と実測jointを埋める。R25/K2Vを除外する場合にも、同じ候補方式での実測または明示した研究上の除外判断が必要で、未実行を性能劣位としない。',
        '4. 候補の選別に使わないoptimizer seedで、生存n候補とK/Rの差を対応付けて確認する。今回の確認済み対象以外へ再現性を一般化しない。',
        '5. 中央ブロックの限定的被覆が研究対象として十分か決定する。選択方式を広げるなら別版で構造検算から再開する。初期計画生成を含む共通計時範囲・期限採択・T/J/支持規則を別途確定する。','',
        '上記は未実行54条件をすべて無条件に実行する提案ではない。必要な差を識別する段階的な再登録を行い、本実験開始は別の承認事項として保持する。','',
        '全MPS更新/全評価の新規監視、原本入力/コードpin、失敗/中断、全枝の未選択計画を保存する。本作業の編集先は専用pilotディレクトリである。開始時との差分が検出された既存ファイルは保全監査を参照し、他の作業の変更を上書きして戻さない。commit/push・本実験なし。']
    alert=DOC/'PRESERVATION_ALERT.json'
    if alert.exists():
        drift=read(alert)
        lines[4:4]=[f"**保全監査はCONDITIONAL。** 開始時から既存ファイル{len(drift['changes'])}件のhash変化を検出した。これらを復元・上書きせず、[保全警告](PRESERVATION_ALERT.json)と[最終検証](VERIFICATION.md)に記録する。p/shots等の計算source pinと、作業ツリー全体の非干渉判定を分ける。",'']
        lines+=['','本実験採用前には、同時変更されたFCFS_v1関連経路と本比較の固定完成規則の関係も整理し、運用仕様を混在させない。影響監査は本pilotの検査経路に限定され、既存ファイル全件の不変を証明するものではない。']
    pin_alert=DOC/'SOURCE_PIN_ALERT.json'
    if pin_alert.exists():
        lines[4:4]=['**現在の作業ツリーで新規実行は拒否される。** 研究方針文書等の登録hash不一致を[SOURCE_PIN_ALERT.json](SOURCE_PIN_ALERT.json)へ記録した。今回の主要Wは開始時に指定された平均荷待ちv2であり、その後の正本案内の総W/FCFS_v1記述へ自動変換しない。開始時policyとhashが完全一致する実在backupを`frozen_baseline/DW_RESEARCH_POLICY.md`へ保全した。現在の正本を戻すことなく、本結果は登録済み旧版の実測として保持する。','']
    DOC.mkdir(exist_ok=True);(DOC/'REPORT.md').write_text('\n'.join(lines)+'\n')
    adopted={scale:{'N':N,'n':None,'K':None,'R':None,'p':2,'optimization_shots':1000,'final_extraction_shots':10000,
        'qaoa_depth_status':'FROZEN','shots_status':'FROZEN','status_scope':'formal_nKR_adoption','status':scale_status[scale],
        'measurement_candidate_status':candidate_status[scale],'current_policy_alignment':'NOT_CONFIRMED' if policy_drift else 'registered_baseline',
        'reason':'source policy hash drift and incomplete comparison evidence' if policy_drift else 'incomplete comparison evidence'}
        for scale,N in [('S1',1000),('S2',2000),('S3',4000)]}
    dump(OUT/'FINAL_SELECTION.json',adopted)
    print(json.dumps(summary,indent=2))


if __name__=='__main__':
    import sys
    main('--reuse-analysis' in sys.argv)
