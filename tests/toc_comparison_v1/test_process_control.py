import json
import os
from pathlib import Path
import signal
import sys
import time

import pytest

from kmd_toc.comparison_v1.execution import supervise


@pytest.mark.parametrize('checkpoint',[False,True])
def test_real_deadline_reaps_child_and_grandchild(tmp_path,checkpoint):
    # Explicit, short registered test budget; not a 300s/memory stress test.
    budget=1.5
    (tmp_path/'REGISTRATION.json').write_text(json.dumps({'test':'real_process_timeout','wall_s':budget,
        'checkpoint':checkpoint,'synthetic_fixture':True}))
    probe=tmp_path/'probe.py'
    probe.write_text('''import json,os,subprocess,sys,time
from pathlib import Path
out=Path(sys.argv[1])
child=subprocess.Popen([sys.executable,'-c','import time;time.sleep(30)'])
(out/'pids.json').write_text(json.dumps([os.getpid(),child.pid]))
if sys.argv[2]=='yes':
 (out/'message.json').write_text(json.dumps({'kind':'synthetic_verified_checkpoint'}))
time.sleep(30)
''')
    got=[];start=time.perf_counter()
    result=supervise([sys.executable,str(probe),str(tmp_path),'yes' if checkpoint else 'no'],tmp_path,
                     start+budget,lambda m:got.append((m,time.perf_counter()-start)))
    assert result['termination_reason']=='OUTER_WALL_LIMIT'
    assert result['cleanup']['session_empty']
    assert len(got)==int(checkpoint)
    if got:assert got[0][1]<budget
    for pid in json.loads((tmp_path/'pids.json').read_text()):
        assert not Path(f'/proc/{pid}').exists()


def test_real_child_error(tmp_path):
    (tmp_path/'REGISTRATION.json').write_text(json.dumps({'test':'real_child_exit','wall_s':2,'synthetic_fixture':True}))
    result=supervise([sys.executable,'-c','raise RuntimeError("fixture child error")'],tmp_path,
                     time.perf_counter()+2,lambda m:None)
    assert result['termination_reason']=='CHILD_PROCESS_ERROR'
    assert result['cleanup']['session_empty']


@pytest.mark.parametrize('mode',['checkpoint_timeout','empty_timeout','invalid_plan','child_error','invalid_input','input_timeout'])
def test_parent_result_real_control_and_physical_validation(tmp_path,monkeypatch,mode):
    from dataclasses import asdict,replace
    from kmd_toc.baseline_a.fixtures import artificial_problem
    from kmd_toc.baseline_a.rule_v1 import generate
    from kmd_toc.common.models import save_problem
    from kmd_toc.comparison_v1.contract import input_inventory,dump
    from kmd_toc.dwt.parallel import cpu_profile
    from kmd_toc.comparison_v1 import execution
    # Reuse the contract fixture, but feed a real saved, hash-checked Problem.
    from test_contract_and_evaluation import manifest
    m=manifest();p=artificial_problem(12,4,1);plan,_=generate(p)
    source=tmp_path/'input';save_problem(p,source)
    # This path includes NFS input reads, child interpreter startup and physical
    # checks; 1.5s is reserved for the direct watchdog/input-timeout witnesses.
    budget=1.5 if mode=='input_timeout' else 10.
    case=m['cases'][0];case['input']=input_inventory(source);case['budget_wall_s']=budget
    if mode=='input_timeout':
        case['input']['preflight_physical_validation']='VALID'
        import kmd_toc.common.models as models
        original_loader=models.load_problem
        def slow_load(*args,**kwargs):
            time.sleep(3)
            return original_loader(*args,**kwargs)
        monkeypatch.setattr(models,'load_problem',slow_load)
    profile=cpu_profile({'threads':4,'cpu_parallel':{'workers':4,'native_threads_per_branch':1,
        'cpu_ids':None,'coordinator_reserve_fraction':.2}})
    m['cpu_profile']=profile
    if mode=='invalid_input':case['input']['files']['input.json']='bad'
    if mode=='invalid_plan':
        t=plan.trips[0];plan=replace(plan,trips=(replace(t,waiting_s=-1),*plan.trips[1:]))
    raw=tmp_path/'fixture_plan.json';dump(raw,asdict(plan))
    probe=tmp_path/'probe.py'
    probe.write_text('''import hashlib,json,os,sys,time
from pathlib import Path
out=Path(sys.argv[1]);source=Path(sys.argv[2]);mode=sys.argv[3]
if mode=='child_error':raise RuntimeError('fixture crash after valid parent input')
if mode!='empty_timeout':
 data=source.read_bytes();(out/'candidate_plan.json').write_bytes(data)
 (out/'message.json').write_text(json.dumps({'kind':'candidate','sha256':hashlib.sha256(data).hexdigest(),
   'native_status':'VALIDATED','native_stop_reason':'MOVE_LIMIT'}))
if mode in ('checkpoint_timeout','empty_timeout'):time.sleep(30)
''')
    original=execution.supervise
    def control(command,out,deadline,receive):
        return original([sys.executable,str(probe),str(out),str(raw),mode],out,deadline,receive)
    monkeypatch.setattr(execution,'supervise',control)
    available=os.sched_getaffinity(0)
    try:
        result=execution.execute(m,m['runs'][0],tmp_path/'actual_parent_result')
    finally:os.sched_setaffinity(0,available)
    if mode=='checkpoint_timeout':
        assert result['termination_reason']=='OUTER_WALL_LIMIT'
        assert result['adoptable'] and result['validation_state']=='VALIDATED'
        assert result['T_program']<budget<=result['T_attempt']
    elif mode in ('empty_timeout','input_timeout'):
        assert result['termination_reason']=='OUTER_WALL_LIMIT'
        assert not result['adoptable'] and result['validation_state']=='NO_PLAN'
        if mode=='input_timeout':
            assert result['input_state']=='VALID'
            from kmd_toc.comparison_v1.evaluation import summarize
            assert summarize([result])[0]['valid_input_executed']==1
    elif mode=='invalid_plan':
        assert result['validation_state']=='INVALID_PLAN' and not result['adoptable']
        assert (tmp_path/'actual_parent_result/rejected_plan.json').exists()
    elif mode=='child_error':
        assert result['termination_reason']=='CHILD_PROCESS_ERROR' and result['input_state']=='VALID'
    else:
        assert result['input_state']=='INVALID' and result['termination_reason']=='INPUT_INVALID'
    if not result['adoptable']:
        assert result['T_program'] is result['D'] is result['W'] is None
    assert result['T_attempt']>0
