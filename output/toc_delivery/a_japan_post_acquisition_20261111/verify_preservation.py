from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import subprocess

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for part in iter(lambda:f.read(1024*1024),b''):
            h.update(part)
    return h.hexdigest()


def main():
    before=json.loads((HERE/'PRESERVATION_BEFORE.json').read_text())
    changed=[];deleted=[]
    for name,rec in before['files'].items():
        p=ROOT/name
        if not p.is_file():
            deleted.append(name)
        elif sha(p)!=rec['sha256']:
            changed.append(name)
    current_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    (HERE/'GIT_STATUS_AFTER.txt').write_text(subprocess.check_output(['git','status','--short'],cwd=ROOT,text=True))
    frozen=[n for n in before['files'] if 'frozen_demand/v1/' in n]
    result={'checked_at':datetime.now(timezone.utc).isoformat(),'existing_files_checked':len(before['files']),
            'unchanged_count':len(before['files'])-len(changed)-len(deleted),'changed':changed,'deleted':deleted,
            'head_unchanged':current_head==before['head'],'frozen_files_checked':len(frozen),
            'frozen_eight_files_unchanged':len(frozen)==8 and not any(n in changed+deleted for n in frozen),
            'new_docs':[f'docs/research/toc_delivery_a/{n}' for n in ('A_JAPAN_POST_DATA_AVAILABILITY.md','A_DATA_ACQUISITION_PLAN.md','A_DATA_ACQUISITION_DECISION.md')],
            'scope':'existing saved population unchanged; three requested documents and this new evidence directory added'}
    (HERE/'PRESERVATION_RESULT.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    assert not changed and not deleted and result['head_unchanged'] and result['frozen_eight_files_unchanged']
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
