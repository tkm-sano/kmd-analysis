"""Evidence-preserving, stateful resource gates. No quantum/optimizer dependencies."""
import copy
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import time

GIB=1024**3
NA='NOT_AVAILABLE'
SPEC=dict(version='20260916_v1',temporary_comparison_only=True,scientific_standard_frozen=False,
    process=dict(nominal_limit_bytes=4*GIB,warning_fraction=.8,preventive_stop_fraction=.9,hard_stop_bytes=4*GIB),
    psi=dict(metric='full.avg10',warning_threshold_percent=0.,required_consecutive_observations=5,
        minimum_persistence_seconds=1.,maximum_observation_gap_seconds=.75,
        scope='supervisor and worker current cgroup paths plus all ancestors, deduplicated',
        reset='full avg10<=0, missing/unparseable PSI, absent scope, or gap>0.75s resets that path',
        rationale='Five observations and at least1s at target0.25s separate isolated readings while remaining conservative; these are operational choices, not proven safety thresholds.'),
    system_poll_seconds=.25,process_poll_seconds=.01,
    cgroup_headroom_bytes=GIB,host_available_min_bytes=4*GIB,
    cgroup_event_names=['high','max','oom','oom_kill'],host_psi_policy='warning/log only; host availability is a separate immediate stop',
    unchanged_limits=dict(run_wall_seconds=900,cumulative_wall_seconds=3600,condition_p_circuits=600,total_circuits=2000,
        total_shots=5000000,heartbeat_stall_seconds=300),
    unavailable_policy='Store NOT_AVAILABLE; missing process RSS or host MemAvailable stops monitoring; optional PSI/cgroup files warn and reset PSI persistence.',
    reason_policy='All triggered details preserved, deduplicated stop_reasons/warning_reasons, no primary-reason overwrite',
    stop_policy='Durable atomic STOP_SNAPSHOT.json written and fsynced before worker termination')


def parse_pairs(raw, integers=True):
    if raw==NA:return NA
    try:return {line.split()[0]:int(line.split()[1]) if integers else float(line.split()[1]) for line in raw.splitlines()}
    except (ValueError,IndexError,AttributeError):return NA


def parse_psi(raw):
    if raw==NA:return NA
    try:
        result={}
        for line in raw.splitlines():
            words=line.split();result[words[0]]={k:int(v) if k=='total' else float(v) for k,v in (x.split('=') for x in words[1:])}
        return result if all(k in result and 'avg10' in result[k] for k in ('some','full')) else NA
    except (ValueError,IndexError,AttributeError):return NA


def number(value):
    try:return int(value) if value not in (None,NA,'max') else None
    except (ValueError,TypeError):return None


class GateEngine:
    def __init__(self, baseline, spec=None):
        self.spec=copy.deepcopy(spec or SPEC);self.baseline=copy.deepcopy(baseline);self.psi_state={}

    def evaluate(self,s):
        cfg=self.spec;warnings=[];stops=[];now=s['monotonic']
        def event(target,label,scope,metric,observed,threshold,**extra):
            target.append(dict(label=label,scope=scope,metric=metric,observed=observed,threshold=threshold,**extra))
        p=s['process'];peak=number(p.get('peak_rss_bytes'));current=number(p.get('aggregate_rss_bytes'))
        limit=cfg['process']['nominal_limit_bytes']
        if peak is None or current is None:
            event(stops,'RESOURCE_MONITOR_UNAVAILABLE_STOP','process','rss',NA,'must be available')
        else:
            if peak>=cfg['process']['warning_fraction']*limit:
                event(warnings,'PROCESS_RSS_WARNING','process','peak_rss_bytes',peak,cfg['process']['warning_fraction']*limit)
            if peak>=cfg['process']['preventive_stop_fraction']*limit:
                event(stops,'PROCESS_RSS_STOP','process','peak_rss_bytes',peak,cfg['process']['preventive_stop_fraction']*limit,
                      mode='hard' if peak>=cfg['process']['hard_stop_bytes'] else 'preventive',configured_limit_bytes=limit,current_rss_bytes=current)
        paths=set(s['cgroups'])
        for absent in set(self.psi_state)-paths:del self.psi_state[absent]
        for path,cg in s['cgroups'].items():
            initial=self.baseline['cgroups'].get(path)
            if initial is None:
                self.baseline['cgroups'][path]=copy.deepcopy(cg);initial=cg
            usage=number(cg.get('memory.current'))
            for name in ('memory.max','memory.high'):
                capacity=number(cg.get(name))
                if usage is not None and capacity is not None and capacity-usage<cfg['cgroup_headroom_bytes']:
                    event(stops,'CGROUP_MEMORY_HEADROOM_STOP',path,f'{name}-memory.current',capacity-usage,cfg['cgroup_headroom_bytes'],capacity_bytes=capacity,current_bytes=usage)
            for file in ('memory.events','memory.events.local'):
                events=parse_pairs(cg.get(file,NA));before=parse_pairs(initial.get(file,NA))
                if isinstance(events,dict) and isinstance(before,dict):
                    changes={k:events.get(k,0)-before.get(k,0) for k in cfg['cgroup_event_names'] if events.get(k,0)>before.get(k,0)}
                    if changes:event(stops,'CGROUP_MEMORY_EVENT_STOP',path,file,changes,'any monitored counter increases')
            swap=number(cg.get('memory.swap.current'));prev=number(initial.get('memory.swap.current'))
            if swap is not None and prev is not None and swap>prev:
                event(stops,'CGROUP_SWAP_GROWTH_STOP',path,'memory.swap.current',swap,prev)
            pressure=parse_psi(cg.get('memory.pressure',NA))
            if pressure==NA:
                self.psi_state.pop(path,None)
                event(warnings,'CGROUP_METRIC_NOT_AVAILABLE',path,'memory.pressure',NA,'optional availability explicitly recorded')
                continue
            value=pressure['full']['avg10']
            if value<=cfg['psi']['warning_threshold_percent']:
                self.psi_state.pop(path,None)
                continue
            state=self.psi_state.get(path)
            if state is None or now-state['last']>cfg['psi']['maximum_observation_gap_seconds']:
                state=dict(first=now,last=now,count=1)
            elif now>state['last']:
                state=dict(first=state['first'],last=now,count=state['count']+1)
            self.psi_state[path]=state;duration=now-state['first']
            event(warnings,'CGROUP_PSI_WARNING',path,'full.avg10',value,0.,consecutive_observations=state['count'],persistence_seconds=duration)
            if state['count']>=cfg['psi']['required_consecutive_observations'] and duration>=cfg['psi']['minimum_persistence_seconds']:
                event(stops,'CGROUP_PSI_PERSISTENT',path,'full.avg10',value,0.,consecutive_observations=state['count'],
                    persistence_seconds=duration,required_observations=cfg['psi']['required_consecutive_observations'],required_seconds=cfg['psi']['minimum_persistence_seconds'])
        host=s['host'];available=number(host.get('MemAvailable'))
        if available is None:event(stops,'RESOURCE_MONITOR_UNAVAILABLE_STOP','host','MemAvailable',NA,'must be available')
        elif available<cfg['host_available_min_bytes']:
            event(stops,'HOST_MEMORY_HEADROOM_STOP','host','MemAvailable',available,cfg['host_available_min_bytes'])
        hp=parse_psi(host.get('memory.pressure',NA))
        if hp!=NA and hp['full']['avg10']>0:event(warnings,'HOST_PSI_WARNING','host','full.avg10',hp['full']['avg10'],0.)
        for key in ('sin','sout'):
            val=number(host.get('swap',{}).get(key));base=number(self.baseline['host'].get('swap',{}).get(key))
            if val is not None and base is not None and val>base:event(stops,'HOST_SWAP_ACTIVITY_STOP','host',key,val,base)
        for extra in s.get('external_stop_triggers',[]):stops.append(extra)
        return dict(warning_reasons=sorted({r['label'] for r in warnings}),stop_reasons=sorted({r['label'] for r in stops}),
            warnings=warnings,stops=stops,primary_reason=None,psi_state=copy.deepcopy(self.psi_state),stop=bool(stops))


def read_file(path):
    try:return path.read_text().strip()
    except (FileNotFoundError,PermissionError,ProcessLookupError):return NA


def process_memory(pid,previous_peak=0):
    import psutil
    if pid is None:return dict(worker_pid=None,worker_rss_bytes=0,worker_vms_bytes=0,child_pids=[],children=[],child_rss_bytes=0,aggregate_rss_bytes=0,peak_rss_bytes=previous_peak)
    try:
        proc=psutil.Process(pid);mem=proc.memory_info();children=[]
        for child in proc.children(recursive=True):
            try:children.append(dict(pid=child.pid,rss_bytes=child.memory_info().rss))
            except psutil.NoSuchProcess:pass
        total=mem.rss+sum(c['rss_bytes'] for c in children)
        return dict(worker_pid=pid,worker_rss_bytes=mem.rss,worker_vms_bytes=mem.vms,child_pids=[c['pid'] for c in children],
            children=children,child_rss_bytes=total-mem.rss,aggregate_rss_bytes=total,peak_rss_bytes=max(previous_peak,total))
    except psutil.NoSuchProcess:
        return dict(worker_pid=pid,worker_rss_bytes=NA,worker_vms_bytes=NA,child_pids=[],children=[],child_rss_bytes=NA,
                    aggregate_rss_bytes=NA,peak_rss_bytes=previous_peak,process_exited=True)


def snapshot(pid,process,context):
    import psutil
    start=time.monotonic();scopes={};memberships={}
    for label,pid_path in [('supervisor','self')]+([('worker',str(pid))] if pid else []):
        raw=read_file(Path('/proc')/pid_path/'cgroup');memberships[label]=raw
        if raw==NA:continue
        unified=[line[3:] for line in raw.splitlines() if line.startswith('0::')]
        if not unified:continue
        path=Path('/sys/fs/cgroup')/unified[0].lstrip('/')
        while str(path).startswith('/sys/fs/cgroup'):
            scopes.setdefault(str(path),[]).append(label+('_current' if str(path).endswith(unified[0]) else '_ancestor'))
            if path==Path('/sys/fs/cgroup'):break
            path=path.parent
    cgroups={}
    for path in scopes:
        cgroups[path]={name:read_file(Path(path)/name) for name in ('memory.current','memory.max','memory.high','memory.events','memory.events.local','memory.pressure','memory.swap.current')}
    meminfo={}
    for line in read_file(Path('/proc/meminfo')).splitlines():
        key,rest=line.split(':',1);parts=rest.split();meminfo[key]=int(parts[0])*1024 if len(parts)>1 and parts[1]=='kB' else int(parts[0])
    host=dict(MemTotal=meminfo.get('MemTotal',NA),MemAvailable=meminfo.get('MemAvailable',NA),
        **{'memory.pressure':read_file(Path('/proc/pressure/memory'))},swap=psutil.swap_memory()._asdict())
    return dict(timestamp_utc=datetime.now(timezone.utc).isoformat(),monotonic=start,**context,process=process,
        cgroup_memberships=memberships,cgroup_scope_roles=scopes,cgroups=cgroups,host=host,
        configured_process_limit=SPEC['process']['nominal_limit_bytes'],preventive_threshold=SPEC['process']['preventive_stop_fraction']*SPEC['process']['nominal_limit_bytes'],
        collection_seconds=time.monotonic()-start)


def durable_json(path,value):
    path.parent.mkdir(parents=True,exist_ok=True);temp=path.with_suffix(path.suffix+'.tmp')
    with temp.open('w') as f:json.dump(value,f,indent=2,allow_nan=False);f.write('\n');f.flush();os.fsync(f.fileno())
    temp.replace(path)


def stop_with_snapshot(path,snap,decision,terminate):
    assert decision['stop'] and decision['stop_reasons']
    durable_json(path,dict(snapshot=snap,decision=decision,specification=SPEC,termination_order='snapshot fsynced before terminate callback'))
    terminate()
