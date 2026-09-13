"""Read-only collection / artifact generation for the R23 remediation task."""
from __future__ import annotations
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
ART=ROOT/'reproducibility/outputs/traffic_simulation'
OUT=ART/'r23_n5_runtime_optimization_audit_remediation/20260913_v1'
AUDIT=ART/'r23_n5_runtime_optimization_code_audit/20260913_v2_independent'
BASE='33ae964bca0e61199621ee976a927cd4069e1723'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(name,value):
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/name).write_text(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
def git(*args):return subprocess.run(['git',*args],cwd=ROOT,check=True,capture_output=True,text=True).stdout.strip()
def initialize():
    if (OUT/'finding_authority.json').exists():raise RuntimeError('Initial evidence already frozen')
    raw=json.loads((AUDIT/'finding_register.json').read_text())
    mapping={'I01':['I01','I07'],'I02':['I02','I08'],'I03':['I03'],'I04':['I04'],
             'I05':['stopping-rule HIGH (independent DOF; not register I05)'],
             'I06':['optimizer MEDIUM (independent DOF; not register I06)'],
             'I07':['I09'],'I08':['I05','I10'],'I09':['I04'],'I10':['I02','I06','I08']}
    write('finding_authority.json',{'authority':str(AUDIT.relative_to(ROOT)),
        'authority_commit':BASE,'source_sha256':sha(AUDIT/'finding_register.json'),'findings_verbatim':raw['findings'],
        'request_section_to_original_finding':mapping,
        'rule':'Original I01-I10 IDs/severity remain authoritative. Requested filenames retain request numbering; closure register uses original IDs. No finding merged or weakened.'})
    table=['# Initial finding register','', '| ID | Finding | Severity | Affected files | Scientific impact | Required remediation | Status |','|---|---|---|---|---|---|---|']
    for f in raw['findings']:
        table.append('| '+' | '.join([f['id'],f['title'],f['severity'],'; '.join(f['evidence']),f['impact'],f['remediation'],'OPEN'])+' |')
    (OUT/'INITIAL_FINDINGS.md').write_text('\n'.join(table)+'\n')
    protected=[]
    for name in ['r23_n5_scaling','r23_n5_scaling_authority','r23_n5_runtime_optimization_code_audit','r23_n5_runtime_optimization_review','r23_n5_scaling_evidence_review']:
        for p in sorted((ART/name).rglob('*')):
            if p.is_file() and '__pycache__' not in str(p):
                st=p.stat(); protected.append({'path':str(p.relative_to(ROOT)),'sha256':sha(p),'mtime_ns':st.st_mtime_ns,'size':st.st_size})
    write('original_artifact_snapshot.json',{'captured_at':dt.datetime.now(dt.timezone.utc).isoformat(),'files':protected})
    write('start_state.json',{'HEAD':git('rev-parse','HEAD'),'branch':git('branch','--show-current'),'git_status':git('status','--short'),
        'host':platform.node(),'user':__import__('getpass').getuser(),'shell_python':subprocess.run(['which','python'],capture_output=True,text=True).stdout.strip(),
        'collector_python':sys.executable,'conda':{k:os.environ.get(k) for k in ['CONDA_PREFIX','CONDA_DEFAULT_ENV','VIRTUAL_ENV']},
        'initial_classifications':['CODE_AUDIT_FAIL','CODE_AUDIT_RESULT_NOT_REPRODUCED','R23_N5_SCALING_EVIDENCE_ACCEPTED_WITH_LIMITATIONS'],
        'rank02_rank03':'retained, not reauthorized pending lineage/resource provenance','R24':'NOT_AUTHORIZED_PENDING_R23_REMEDIATION'})
    print(json.dumps({'initial_finding_count':len(raw['findings']),'protected_files':len(protected)}))
def reconstruct():
    logs=[Path('/home/takuma/.codex/sessions/2026/09/11/rollout-2026-09-11T22-10-44-01a09097-87ec-7030-a272-51e5226064ab.jsonl'),
          Path('/home/takuma/.codex/sessions/2026/09/13/rollout-2026-09-13T23-13-09-01a09b1d-6268-7f62-9ded-1e5606cba10f.jsonl')]
    runner='05_src/traffic_simulation/r23_n5_scaling/run_n5_scaling.py'
    qaoa='05_src/traffic_simulation/r23_qaoa_aer/qaoa.py'
    helper='05_src/traffic_simulation/r23_qaoa_aer/optimized_metrics_v4.py'
    events=[]; snippets=[]; snapshots={}
    for log in logs:
        for lineno,line in enumerate(log.open(),1):
            record=json.loads(line);stamp=record.get('timestamp','')
            if stamp>'2026-09-13T15:31:00Z':continue
            payload=record.get('payload',{});item=payload.get('item',{})
            if item.get('type')=='FileChange':
                for path,change in item.get('changes',{}).items():
                    rel=path.removeprefix(str(ROOT)+'/')
                    if rel not in (runner,qaoa,helper):continue
                    events.append({'log':str(log),'line':lineno,'timestamp':stamp,'path':rel,'change':change})
                    if rel==runner and change.get('type')=='add':snapshots['rank01_runner']=change['content']
            if item.get('type')=='CommandExecution':
                cmd=' '.join(item.get('command',[]));stdout=item.get('stdout','')
                relevant=[]
                for output_line in stdout.splitlines():
                    if (re.match(r'^\s*\d+\s+',output_line) and 'run_n5_scaling.py routing_v18_n5_rank' in output_line and '/bin/python' in output_line):relevant.append(output_line)
                    elif output_line.startswith('{"instance_id": "routing_v18_n5_rank') and 'P_feasible' in output_line:relevant.append(output_line)
                    elif 'Maximum resident set size' in output_line or 'Elapsed (wall clock)' in output_line:relevant.append(output_line)
                # Source/launch commands only; do not archive unrelated shell history or user conversations.
                if ('run_n5_scaling.py routing_v18_n5_rank' in cmd and ('/usr/bin/time' in cmd or ('python' in cmd and 'ps ' not in cmd and 'sed ' not in cmd and 'git ' not in cmd))) or relevant:
                    snippets.append({'log':str(log),'line':lineno,'timestamp':stamp,'command':cmd if len(cmd)<2000 else 'long command; see original log locator',
                        'stdout_scoped':relevant,'status':item.get('status')})
            if payload.get('type')=='custom_tool_call' and 'exec_command' in payload.get('input',''):
                inp=payload['input']
                if 'run_n5_scaling.py routing_v18_n5_rank' in inp and '/usr/bin/time' in inp and 'ps ' not in inp and len(inp)<2500:
                    snippets.append({'log':str(log),'line':lineno,'timestamp':stamp,'launch_tool_input':inp})
    if 'rank01_runner' not in snapshots:raise RuntimeError('runner creation evidence unavailable')
    def apply_diff(source,diff):
        # Replay only recorded unified text patches in memory; historical files stay immutable.
        lines=diff.splitlines(keepends=True);hunks=[];old=[];new=[]
        for line in lines:
            if line.startswith('@@'):
                if old or new:hunks.append((''.join(old),''.join(new)))
                old=[];new=[]
            elif line.startswith(' '):old.append(line[1:]);new.append(line[1:])
            elif line.startswith('-'):old.append(line[1:])
            elif line.startswith('+'):new.append(line[1:])
        if old or new:hunks.append((''.join(old),''.join(new)))
        for before,after in hunks:
            if source.count(before)!=1:raise RuntimeError('historical patch does not match uniquely')
            source=source.replace(before,after,1)
        return source
    current={runner:snapshots['rank01_runner'],qaoa:git('show',f'ff1d579:{qaoa}')+'\n'}
    for event in sorted(events,key=lambda e:e['timestamp']):
        if event['timestamp']<'2026-09-13T14:00:00Z' or event['timestamp']>'2026-09-13T14:17:17Z':continue
        if event['path'] in current and event['change']['type']=='update':
            current[event['path']]=apply_diff(current[event['path']],event['change']['unified_diff'])
    snapshots.update(rank02_rank03_runner=current[runner],rank02_rank03_qaoa=current[qaoa],historical_helper=git('show',f'ff1d579:{helper}')+'\n')
    folder=OUT/'reconstructed_sources';folder.mkdir(exist_ok=True)
    src_info={}
    for name,content in snapshots.items():
        dest=folder/(name+'.py.txt');dest.write_text(content)
        src_info[name]={'archive':str(dest.relative_to(OUT)),'sha256':sha(dest)}
    src_info['rank02_rank03_runner']['matches_0e149ed']=current[runner]==git('show',f'0e149ed:{runner}')+'\n'
    src_info['rank02_rank03_qaoa']['matches_0e149ed']=current[qaoa]==git('show',f'0e149ed:{qaoa}')+'\n'
    assert src_info['rank02_rank03_runner']['matches_0e149ed'] and src_info['rank02_rank03_qaoa']['matches_0e149ed']
    for name in ('rank01_runner','rank02_rank03_runner'):
        assert 'maxiter=300, max_evaluations=300' in snapshots[name]
        assert 'wall_time_seconds=None' in snapshots[name]
    history=Path('/home/takuma/.bash_history')
    history_matches=[line for line in history.read_text().splitlines() if 'run_n5_scaling' in line or 'routing_v18_n5_rank' in line] if history.exists() else []
    write('execution_log_evidence.json',{'collection_timestamp':dt.datetime.now(dt.timezone.utc).isoformat(),
        'log_files':[{'path':str(p),'sha256':sha(p)} for p in logs],'source_events':events,'process_and_launch_evidence':snippets,
        'reconstructed_sources':src_info,'shell_history':{'available':history.exists(),'scoped_match_count':len(history_matches),'matches':history_matches},
        'scheduler':{'sacct':shutil.which('sacct'),'squeue':shutil.which('squeue'),'qstat':shutil.which('qstat'),'evidence':'direct command execution; no scheduler ID recorded'},
        'limitations':['Logs are local contemporaneous records, not signed process-memory attestations.','No run-time hash of the full imported source closure or final optimizer trace retained.','Filesystem mtime is current evidence, not immutable creation time.']})
    byrun=[]
    for rank in ('01','02','03'):
        directory=ART/f'r23_n5_scaling/20260911_v1/runs/routing_v18_n5_rank{rank}'
        record=json.loads((directory/'scientific_result.json').read_text())
        archived=OUT/'historical_run_snapshots'/directory.name;archived.mkdir(parents=True,exist_ok=True)
        fileinfo=[]
        for p in sorted(directory.glob('*.json')):
            dest=archived/p.name;dest.write_bytes(p.read_bytes())
            fileinfo.append({'path':str(p.relative_to(ROOT)),'sha256':sha(p),'archive':str(dest.relative_to(OUT)),
                'mtime_utc':dt.datetime.fromtimestamp(p.stat().st_mtime,dt.timezone.utc).isoformat(),
                'filesystem_birth':subprocess.run(['stat','-c','%w',str(p)],capture_output=True,text=True).stdout.strip()})
        byrun.append({'rank':rank,'level':'STRONGLY_INFERRED','recorded_commit':record['source_commit'],
            'started_at':record['started_at'],'ended_at':record['ended_at'],'host':'hayate (resource/process context)',
            'runner':runner,'helper':None if rank=='01' else helper,'environment':'/home/takuma/.conda/envs/evrp-quantum-temp',
            'reconstruction':src_info['rank01_runner' if rank=='01' else 'rank02_rank03_runner'],
            'contradiction':'EXECUTION_PROVENANCE_METADATA_INCONSISTENCY',
            'explanation':'source_commit is repository HEAD; execution used an uncommitted runner'+(' and uncommitted qaoa V4 wiring' if rank!='01' else '')+'. Timestamped FileChange records reconstruct the bytes later committed at 0e149ed.',
            'files':fileinfo,'formal_acceptance':'NOT_REAUTHORIZED',
            'rerun_requirement':'RERUN_REQUIRED_FOR_FORMAL_ACCEPTANCE' if rank!='01' else 'RERUN_RECOMMENDED',
            'reason':'Historical trajectory/final parameters and complete process source attestation absent; resource peak metric contradicts logged RSS for remaining runs. Retained observations remain usable with explicit limitations.'})
    write('provenance_status_by_run.json',{'runs':byrun,'new_scientific_runs':0})
    print(json.dumps({'source_replay':'matches 0e149ed','source_events':len(events),'process_records':len(snippets),'levels':[r['level'] for r in byrun]}))

LEGACY_GENERATORS=[
    'reproducibility/outputs/traffic_simulation/r23_n5_runtime_optimization_review/20260913_v2/build_artifact.py',
    'reproducibility/outputs/traffic_simulation/r23_n5_runtime_optimization_review/20260913_v2/run_equivalence.py',
    'reproducibility/tools/r23_n5_scaling_evidence_review.py',
    'reproducibility/tools/r23_n5_runtime_optimization_code_audit.py',
]
def archive_generators():
    folder=OUT/'historical_generator_sources';folder.mkdir(exist_ok=True)
    rows=[]
    for i,path in enumerate(LEGACY_GENERATORS):
        p=ROOT/path;dest=folder/(str(i+1)+'_'+p.name+'.txt')
        if dest.exists():raise RuntimeError('Archive already exists')
        dest.write_bytes(p.read_bytes())
        rows.append({'path':path,'original_sha256':sha(p),'archive':str(dest.relative_to(OUT)),
            'reason':'Unconditional validation summaries / inaccurate coverage or benchmark proxy. Historical outputs immutable; executable legacy entrypoint replaced with fail-closed retirement notice.'})
    write('legacy_generator_retirement.json',{'generators':rows})

if __name__=='__main__':
    if '--reconstruct' in sys.argv:reconstruct()
    elif '--archive-generators' in sys.argv:archive_generators()
    else:initialize()
