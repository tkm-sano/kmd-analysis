"""Fixed trust anchors. Verification never adopts a digest from unchecked input."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
POLICY_PATH='docs/research/FCFS_OPERATING_POLICY_V1.md'
MANIFEST_PATH='docs/frozen/FCFS_V1_MANIFEST.json'
EXPECTED_SHA256='51ab348d893c2044ec0d48e77b74a7d669e012c470e969cf6f971e6863578cd3'
RESEARCH_PATH='docs/frozen/配送計画最適化_評価指標と実験条件_1-7.md'
RESEARCH_SHA256='297be6f6be2be000e627480af189bad1533a385bf269b25fc22dc4922b3de9be'


def _unique(pairs):
    result={}
    for k,v in pairs:
        if k in result:raise ValueError('DUPLICATE_MANIFEST_KEY:'+k)
        result[k]=v
    return result


def verify(root=ROOT):
    root=Path(root);errors=[];digests={};raw=None
    for file,expected in [(POLICY_PATH,EXPECTED_SHA256),(RESEARCH_PATH,RESEARCH_SHA256)]:
        try:
            data=(root/file).read_bytes();actual=hashlib.sha256(data).hexdigest();digests[file]=actual
            if file==POLICY_PATH:raw=data
            if actual!=expected:errors.append({'file':file,'reason':'SHA256_MISMATCH','expected':expected,'actual':actual})
        except OSError as error:errors.append({'file':file,'reason':'UNREADABLE','detail':str(error)})
    try:
        manifest=json.loads((root/MANIFEST_PATH).read_text(encoding='utf-8'),object_pairs_hook=_unique)
        expected={'policy_id':'FCFS_v1','version':'v1','freeze_date':'2026-11-20',
                  'file_path':POLICY_PATH,'sha256':EXPECTED_SHA256,'verification':'PASS',
                  'base_spec_path':RESEARCH_PATH,'base_spec_sha256':RESEARCH_SHA256,'main_experiment':'HOLD'}
        if not isinstance(manifest,dict):raise ValueError('MANIFEST_OBJECT_REQUIRED')
        for k,v in expected.items():
            if manifest.get(k)!=v:errors.append({'file':MANIFEST_PATH,'reason':'FIELD_MISMATCH','field':k})
        content=manifest.get('content_utf8')
        if not isinstance(content,str) or content.encode('utf-8')!=raw or hashlib.sha256(content.encode('utf-8')).hexdigest()!=EXPECTED_SHA256:
            errors.append({'file':MANIFEST_PATH,'reason':'CONTENT_MISMATCH'})
    except (OSError,ValueError,UnicodeError,TypeError) as error:
        errors.append({'file':MANIFEST_PATH,'reason':'MANIFEST_UNREADABLE','detail':str(error)})
    return {'status':'FAIL' if errors else 'PASS','policy_id':'FCFS_v1',
            'expected_sha256':EXPECTED_SHA256,'actual_sha256':digests,
            'files_requiring_attention':sorted({e['file'] for e in errors}),'errors':errors,
            'main_experiment':'HOLD'}


def require_frozen():
    result=verify()
    if result['status']!='PASS':raise ValueError('FCFS_FROZEN_POLICY_CHANGED:'+str(result['errors']))
