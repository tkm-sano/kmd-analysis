"""Compare the existing file population to its pre-task hashes."""
from pathlib import Path
from datetime import datetime, timezone
import difflib
import hashlib
import json
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def main():
    before = json.loads((HERE/'PRESERVATION_BEFORE.json').read_text())
    allowed = {'docs/research/toc_delivery_a/'+n for n in ('A_BASELINE_DECISION.md','A_EVIDENCE_REGISTER.md','A_REFERENCE_VALUES.md','A_REFERENCE_VALUES.json')}
    changed, deleted = [], []
    for name, rec in before['files'].items():
        p = ROOT/name
        if not p.is_file():
            deleted.append(name)
        elif digest(p) != rec['sha256']:
            changed.append(name)
    unexpected = sorted(set(changed)-allowed)
    head = subprocess.check_output(['git','rev-parse','HEAD'], cwd=ROOT, text=True).strip()
    (HERE/'GIT_STATUS_AFTER.txt').write_text(subprocess.check_output(['git','status','--short'], cwd=ROOT, text=True))
    diff = []
    docdir = ROOT/'docs/research/toc_delivery_a'
    for path in sorted(docdir.iterdir()):
        if not path.is_file():
            continue
        old = HERE/'before'/path.name
        old_text = old.read_text() if old.exists() else ''
        diff.extend(difflib.unified_diff(old_text.splitlines(keepends=True),path.read_text().splitlines(keepends=True),fromfile='before/'+path.name,tofile=str(path.relative_to(ROOT))))
    (HERE/'TASK_CHANGES.patch').write_text(''.join(diff))
    result = {'checked_at':datetime.now(timezone.utc).isoformat(),'existing_files_checked':len(before['files']),
              'unchanged_count':len(before['files'])-len(changed)-len(deleted),'intended_changed':sorted(set(changed)&allowed),
              'unexpected_changed':unexpected,'deleted':deleted,'head_unchanged':head==before['head'],
              'frozen_demand_paths_unchanged':all(n not in set(changed+deleted) for n in before['files'] if 'frozen_demand/v1/' in n),
              'old_evidence_unchanged':not any(n.startswith('output/toc_delivery/a_baseline_20261111/') for n in changed+deleted),
              'scope':'all files present in the saved baseline population; new evidence and two new assessment docs are additions'}
    (HERE/'PRESERVATION_RESULT.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    assert not unexpected and not deleted and result['head_unchanged']
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__ == '__main__':
    main()
