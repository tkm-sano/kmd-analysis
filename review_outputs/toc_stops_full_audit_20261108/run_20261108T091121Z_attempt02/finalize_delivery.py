"""Final artifact completeness, source protection, and hash verification."""
from pathlib import Path
import csv
import hashlib
import json
import subprocess

O=Path(__file__).resolve().parent
ROOT=Path('/home/takuma/kmd-analysis')
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def j(name):return json.loads((O/name).read_text())
def main():
    required=['ALL_STOPS_AUDIT.csv','AUDIT_SUMMARY.json','REGIONAL_COVERAGE.csv','AUDIT_EXCEPTIONS.csv','FINAL_AUDIT_REPORT_JA.md','INDEPENDENT_AUDIT_VALIDATION.json','PROTECTION_CHECK.json','REPRODUCE.md']
    for f in required:assert (O/f).is_file() and (O/f).stat().st_size>0,f
    manifest=j('INPUT_MANIFEST.json')+j('OD_SCOPE_AUDIT.json')['inputs']+[j('SUPPLEMENTARY_SUMMARY.json')['mesh_readback']]
    changed=[r['path'] for r in manifest if sha(r['path'])!=r['sha256']]
    before=j('REPOSITORY_BEFORE.json')
    changed_tracked=[p for p,h in before['tracked_sha256'].items() if sha(ROOT/p)!=h]
    old=set(filter(None,before['status_porcelain_z'].split('\0')))
    now=set(filter(None,subprocess.check_output(['git','status','--porcelain=v1','-z'],cwd=ROOT).decode().split('\0')))
    unexpected=[r for r in now-old if not r[3:].startswith('review_outputs/toc_stops_full_audit_20261108')]
    with (O/'ALL_STOPS_AUDIT.csv').open() as f:rows=list(csv.DictReader(f))
    assert len(rows)==39956
    counts={s:sum(r['overall_status']==s for r in rows) for s in ['PASS','CONDITIONAL','HOLD','FAIL']}
    assert counts==j('SUPPLEMENTARY_SUMMARY.json')['status_counts_all_categories']
    assert j('INDEPENDENT_AUDIT_VALIDATION.json')['all_checks_pass']
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip()
    result={'required_artifacts_present':True,'ledger_rows':len(rows),'status_counts_all_categories':counts,'source_inputs_checked':len(manifest),'changed_source_inputs':changed,'changed_tracked_files':changed_tracked,'preexisting_status_entries_removed':sorted(old-now),'unexpected_new_status_entries':unexpected,'head_unchanged':head==before['head'],'all_checks_pass':not(changed or changed_tracked or old-now or unexpected) and head==before['head'],'scientific_simulation_or_optimization_run':False}
    with (O/'DELIVERY_VERIFICATION.json').open('x') as f:json.dump(result,f,ensure_ascii=False,indent=2)
    assert result['all_checks_pass']
    hashes={p.name:{'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(O.iterdir()) if p.is_file() and p.name!='OUTPUT_HASHES.json'}
    with (O/'OUTPUT_HASHES.json').open('x') as f:json.dump(hashes,f,ensure_ascii=False,indent=2)
    print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':main()
