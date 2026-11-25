import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from kmd_toc.fcfs_v1 import policy


@pytest.fixture
def copy_root(tmp_path):
    for name in (policy.POLICY_PATH,policy.MANIFEST_PATH,policy.RESEARCH_PATH):
        target=tmp_path/name;target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(policy.ROOT/name,target)
    return tmp_path


def test_real_freeze_and_base_spec_pass():
    assert policy.verify()['status']=='PASS'


@pytest.mark.parametrize('target',[policy.POLICY_PATH,policy.RESEARCH_PATH,policy.MANIFEST_PATH])
def test_missing_files_fail(copy_root,target):
    (copy_root/target).unlink()
    result=policy.verify(copy_root)
    assert result['status']=='FAIL' and target in result['files_requiring_attention']


@pytest.mark.parametrize('target',[policy.POLICY_PATH,policy.RESEARCH_PATH])
def test_modification_fails(copy_root,target):
    p=copy_root/target;p.write_bytes(p.read_bytes()+b'changed\n')
    assert policy.verify(copy_root)['status']=='FAIL'


def test_manifest_and_body_cannot_redefine_anchor(copy_root):
    p=copy_root/policy.POLICY_PATH;p.write_bytes(p.read_bytes()+b'changed\n')
    m=copy_root/policy.MANIFEST_PATH;data=json.loads(m.read_text())
    data.update(sha256=hashlib.sha256(p.read_bytes()).hexdigest(),content_utf8=p.read_text())
    m.write_text(json.dumps(data))
    assert policy.verify(copy_root)['status']=='FAIL'


def test_CLI_fails_nonzero_identifying_modified_file(copy_root):
    (copy_root/policy.POLICY_PATH).unlink()
    result=subprocess.run([sys.executable,'-B',str(policy.ROOT/'scripts/verify_fcfs_policy_v1.py'),
                           '--root',str(copy_root)],text=True,capture_output=True)
    assert result.returncode==1
    assert policy.POLICY_PATH in json.loads(result.stdout)['files_requiring_attention']
