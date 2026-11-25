"""Only measured final plans are compared; old/partial results stay separate."""
import csv
import json
from fractions import Fraction
from pathlib import Path

from .common import read,dump,legacy,ROOT


def proposal(rows):
    """Pre-registered parameter proposal, never a new optimizer objective."""
    grouped={}
    for r in rows:
        if r.get('status')!='COMPLETE' or r.get('selected',{}).get('I_dual_exact') is None:continue
        V={'S1':10,'S2':20,'S3':40}[r['scale']];key=(r['n'],r['K']/V,r['R'])
        grouped.setdefault(key,{})[r['scale']]=r
    choices=[]
    for key,scales in grouped.items():
        if len(scales)!=3:continue
        scores=[Fraction(r['selected']['I_dual_exact']) for r in scales.values()]
        wall=sum(r['parent_wall_s'] for r in scales.values())
        choices.append(((-min(scores),-sum(scores),wall,*key),key,scales))
    if not choices:return {'status':'HOLD_INSUFFICIENT_COMPLETE_COMMON_SETTING','common_candidate':None}
    _,key,scales=min(choices,key=lambda x:x[0])
    return {'status':'PROVISIONAL_SCREENING_PROPOSAL_NOT_FREEZE','common_candidate':list(key),
        'rule':'max worst-scale final I_dual, then sum final I_dual, then min summed measured wall, then n,K/V,R',
        'scale_evidence':{scale:{'I_dual':r['selected']['I_dual'],'delta_D':r['delta_D'],'delta_W':r['delta_W'],
                                  'wall_s':r['parent_wall_s']} for scale,r in scales.items()},
        'not_a_proof_of_optimality':True,'all_54_required_before_adoption_proposal':True,
        'two_confirmation_seeds_required':True,'freeze_requires_user_approval':True}


def write_csv(path,rows):
    fields=list(dict.fromkeys(k for r in rows for k in r)) or ['status']
    tmp=Path(str(path)+'.tmp')
    with tmp.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
        for r in rows:w.writerow({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(list,dict)) else v for k,v in r.items()})
    tmp.replace(path)


def update(out):
    from .controller import grid,tag
    out=Path(out);rows=[];branches=[];active=[];confirm=[]
    for c in grid():
        folder=out/'groups'/tag(c);path=folder/'GROUP.json'
        row={**c,'R_local':c['R'],'seed':9201,'status':'NOT_STARTED','D':None,'W':None,
             'delta_D':None,'delta_W':None,'I_dual':None,'wall_s':None,'CPU_s':None,'max_RSS_MiB':None,
             'quantum_calls':None,'feasible':None,'reason':None,'selected_branch_id':None,'initial_plan_generation_s':None}
        if path.exists():
            r=read(path);m=r.get('selected',{})
            row.update(status=r['status'],D=m.get('D_km'),W=m.get('W_total_loading_min'),I_dual=m.get('I_dual'),
                delta_D=r.get('delta_D'),delta_W=r.get('delta_W'),wall_s=r.get('parent_wall_s'),CPU_s=r.get('CPU_s'),
                max_RSS_MiB=r.get('sampled_tree_peak_RSS_MiB'),feasible=True if r['status']=='COMPLETE' else None,
                reason=r.get('reason'),selected_branch_id=r.get('selected_branch_id'))
            calls=0;sets=[];TV=[];training=0;final_shots=0;optimizer_limit_stops=0
            for b in range(4):
                bp=folder/f'branch_{b}/RESULT.json'
                if not bp.exists():continue
                br=read(bp);brrows=br.get('rows',[]);calls+=sum(v.get('quantum_calls',0) for v in brrows)
                for call in brrows:
                    q=call.get('quantum',{})
                    if q.get('max_TV_bound') is not None:TV.append(q['max_TV_bound'])
                    training+=q.get('training_shots_actual',0);final_shots+=q.get('final_shots_actual',0)
                    optimizer_limit_stops+=int(q.get('optimizer_success') is False)
                sets.extend(set(v['customer_ids']) for v in brrows if v.get('customer_ids'))
                branches.append({**c,'seed':9201,'branch':b,'status':br['status'],'D':br.get('after',{}).get('D_km'),
                    'W':br.get('after',{}).get('W_total_min'),'CPU_s':br.get('CPU_s'),'wall_s':br.get('wall_s'),
                    'max_RSS_MiB':br.get('RSS_highwater_MiB'),'quantum_calls':sum(v.get('quantum_calls',0) for v in brrows),
                    'reason':br.get('reason'),'not_independent_outer_trial':True})
            row.update(quantum_calls=calls,quantum_calls_started=len(list(folder.glob('branch_*/calls/*/attempt_*/CALL.json'))),
                quantum_calls_completed=len(list(folder.glob('branch_*/calls/*/attempt_*/RESULT.json'))),
                max_TV_bound_completed=max(TV) if TV else None,training_shots_actual=training,final_shots_actual=final_shots,
                optimizer_nonconvergence_calls=optimizer_limit_stops,
                **legacy.coverage(sets,{'S1':1000,'S2':2000,'S3':4000}[c['scale']]))
        elif folder.exists():
            row['status']='RUNNING_OR_CHECKPOINTED'
            for b in range(4):
                h=folder/f'branch_{b}/HEARTBEAT.json'
                if h.exists():active.append({'condition':tag(c),'branch':b,**read(h)})
        rows.append(row)
    for path in sorted((out/'groups').glob('*/GROUP.json')):
        if path.parent.name.endswith('seed9201'):continue
        r=read(path);confirm.append({'tag':path.parent.name,**r.get('condition',{}),'status':r['status'],**r.get('selected',{}),
            'delta_D':r.get('delta_D'),'delta_W':r.get('delta_W'),'wall_s':r.get('parent_wall_s'),'reason':r.get('reason')})
    write_csv(out/'ALL54.csv',rows);write_csv(out/'BRANCHES.csv',branches);write_csv(out/'CONFIRMATIONS.csv',confirm)
    counts={state:sum(r['status']==state for r in rows) for state in sorted({r['status'] for r in rows})}
    status={'screen_counts':counts,'screen_complete':sum(r['status']=='COMPLETE' for r in rows),'active':active,
        'confirmation_complete':sum(r['status']=='COMPLETE' for r in confirm),'confirmation_terminal':len(confirm),
        'parameter_freeze':False,'main_experiment':False,'no_time_caps_or_predicted_time_gate':True}
    dump(out/'STATUS.json',status)
    complete=[r for r in rows if r['status']=='COMPLETE']
    raw=[]
    for c in grid():
        p=out/'groups'/tag(c)/'GROUP.json'
        if p.exists():raw.append({**c,**read(p)})
    decision=proposal(raw);decision['screen_complete_count']=len(complete)
    decision['formal_status']='HOLD' # User approval is required even with all data.
    dump(out/'PARAMETER_PROPOSAL.json',decision)
    axes=[]
    for i,a in enumerate(complete):
        for b in complete[i+1:]:
            if a['scale']!=b['scale']:continue
            changed=[k for k in ('n','K','R') if a[k]!=b[k]]
            if len(changed)!=1:continue
            low,high=sorted([a,b],key=lambda r:r[changed[0]])
            axes.append({'scale':a['scale'],'axis':changed[0],'low':{k:low[k] for k in ('n','K','R')},
                'high':{k:high[k] for k in ('n','K','R')},'delta_D_high_minus_low':high['D']-low['D'],
                'delta_W_high_minus_low':high['W']-low['W'],'I_dual_gain':high['I_dual']-low['I_dual'] if low['I_dual'] is not None and high['I_dual'] is not None else None,
                'measured_wall_ratio':high['wall_s']/low['wall_s'] if low['wall_s'] else None})
    write_csv(out/'AXIS_COMPARISONS.csv',axes)
    pareto=[]
    for a in complete:
        dominators=[{k:b[k] for k in ('n','K','R')} for b in complete if b['scale']==a['scale'] and
            all(b[k]<=a[k] for k in ('D','W','wall_s')) and any(b[k]<a[k] for k in ('D','W','wall_s'))]
        pareto.append({**a,'quality_cost_nondominated':not dominators,'dominated_by':dominators})
    write_csv(out/'PARETO.csv',pareto)
    # Descriptive seed variability, never four internal branches as replicates.
    from kmd_toc.descriptive_v1.statistics import summary
    seed_groups={}
    for r in complete:
        seed_groups.setdefault((r['scale'],r['n'],r['K'],r['R']),[]).append({'seed':9201,'D':r['D'],'W':r['W'],'I_dual':r['I_dual']})
    for r in confirm:
        if r['status']=='COMPLETE':seed_groups.setdefault((r['scale'],r['n'],r['K'],r['R']),[]).append(
            {'seed':r['outer_seed'],'D':r['D_km'],'W':r['W_total_loading_min'],'I_dual':r['I_dual']})
    variance=[]
    for key,items in seed_groups.items():
        for metric in ('D','W','I_dual'):
            vals=[r[metric] for r in items if r[metric] is not None]
            variance.append({'scale':key[0],'n':key[1],'K':key[2],'R':key[3],'metric':metric,
                'seeds':[r['seed'] for r in items],'undefined_count':len(items)-len(vals),
                **summary(vals,independent=False),'scope':'fixed problem seed variability; formal J not selected'})
    write_csv(out/'SEED_VARIABILITY.csv',variance)
    plots(out,complete)
    report=['# 時間上限なし・現行条件のn/K/R予備検証','',
        f'実行状況: {counts}。seed確認完了 {status["confirmation_complete"]} 件。',
        '**パラメータ未Freeze。本実験ではない。未実行・途中計画を完了として扱わない。**','',
        'p2・最適化1000/最終10000 shots・COBYLA最大8評価を維持。最大8は収束保証ではない。',
        '総W、勤務/休憩・FCFS、量子決定保持の共通完成器、厳密な局所D/W非悪化、最終I_dual選択。',
        '休憩場所は許可済み研究仮定で未確認。実運行可行性の証明ではない。',
        'Δは現行仕様で明示再構成した保存初期B計画に対する値。C参照と初期を同一視しない。',
        '時間は保存初期計画からの改善処理。元の初期経路生成時間は未測定null。',
        '内部4枝の平均を最終計画の品質や独立4試行へ代用しない。',
        '旧6完了条件は別版として保持し、この表へ混在させない。','',
        '|S|n|K|R|状態|D km|総W 分|ΔD|ΔW|I_dual %|wall秒|',
        '|---|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|']
    for r in rows:
        report.append('|'+ '|'.join(str(r[k]) if r[k] is not None else '—' for k in ('scale','n','K','R','status','D','W','delta_D','delta_W','I_dual','wall_s'))+'|')
    report.extend(['','## 採用候補・残件',
        '全54条件と登録seed確認が終わるまでは共通採用候補HOLD。n10/K=V/2/R5を最適と決めつけない。',
        '終了後も可行性、D/W/I_dualの実測、被覆/重複、費用、seedの再現性を個別に比較する。',
        '品質差に対する恣意的なSESOIを設けず、両立改善の増分と費用増分を示す。',
        '正式J、MCSE許容基準、共通T、正式D・本実験全体のHOLDは今回自動解除しない。',
        '状態はSTATUS.json、枝明細はBRANCHES.csv、seed比較はCONFIRMATIONS.csv、各GROUP/RESULT/COMMITと全量子ログを参照。'])
    report.extend(['','事前登録の共通候補提案: '+json.dumps(decision,ensure_ascii=False),
        'AXIS_COMPARISONS.csvに単独n/K/R増加の実測品質差・時間比を保存。SEED_VARIABILITY.csvにseed別結果の標本SD等を保存。',
        'この提案は内部探索目的を変更せず、最小構成の費用対効果・品質改善と併記する。採用値を自動Freezeしない。'])
    tmp=out/'REPORT.md.tmp';tmp.write_text('\n'.join(report)+'\n');tmp.replace(out/'REPORT.md')
    print(json.dumps({k:v for k,v in status.items() if k!='active'},ensure_ascii=False),flush=True)
    return status


def plots(out,rows):
    if not rows:return
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    d=Path(out)/'figures';d.mkdir(exist_ok=True)
    for metric,label in [('delta_D','Distance change vs saved initial (km)'),('delta_W','Total loading wait change vs saved initial (min)')]:
        fig,axes=plt.subplots(1,3,figsize=(13,4))
        for ax,scale in zip(axes,('S1','S2','S3')):
            for n,color in [(10,'C0'),(12,'C1')]:
                values=[r for r in rows if r['scale']==scale and r['n']==n]
                if values:ax.scatter([r['wall_s'] for r in values],[r[metric] for r in values],color=color,label=f'n={n}')
                for r in values:ax.annotate(f'K{r["K"]}/R{r["R"]}',(r['wall_s'],r[metric]),fontsize=6)
            ax.set_title(scale);ax.set_xlabel('Measured improvement wall time (s)');ax.set_ylabel(label)
            if ax.collections:ax.legend()
        fig.suptitle('Current-condition final real plans only; incomplete conditions omitted');fig.tight_layout()
        for ext in ('png','pdf'):fig.savefig(d/f'{metric}_vs_time.{ext}',dpi=150)
        plt.close(fig)
