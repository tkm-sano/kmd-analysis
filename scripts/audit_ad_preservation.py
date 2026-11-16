"""Compare every initially recorded file, including untracked old results."""
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT=Path(os.environ.get('KMD_AD_OUTPUT_ROOT','output/toc_delivery/ad_pipeline_20261112'))
def digest(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()

def main():
    before=json.loads((ROOT/'PRESERVATION_BEFORE.json').read_text());changed=[];missing=[];unchanged=0;frozen=[]
    for name,old in before['files'].items():
        p=Path(name)
        if not p.exists():missing.append(name);continue
        new=digest(p)
        if new!=old:changed.append({'path':name,'before':old,'after':new,'intended':name=='src/kmd_toc/common/models.py'})
        else:unchanged+=1
        if 'frozen_demand/v1/' in name:frozen.append({'path':name,'sha256':new,'unchanged':new==old})
    result={'initial_files':len(before['files']),'unchanged':unchanged,'changed':changed,'missing':missing,'unexpected_changes':[x for x in changed if not x['intended']],
            'frozen_files':frozen,'frozen_eight_unchanged':len(frozen)==8 and all(x['unchanged'] for x in frozen),'old_head':before['head'],
            'new_head':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'no_commit':False}
    result['no_commit']=result['old_head']==result['new_head'];result['passed']=not missing and not result['unexpected_changes'] and result['frozen_eight_unchanged'] and result['no_commit']
    (ROOT/'PRESERVATION_RESULT.json').write_text(json.dumps(result,indent=2)+'\n')
    (ROOT/'GIT_STATUS_AFTER.txt').write_text(subprocess.check_output(['git','status','--short'],text=True))
    (ROOT/'GIT_DIFF_TRACKED.patch').write_text(subprocess.check_output(['git','diff'],text=True))
    patch=subprocess.run(['diff','-u',str(ROOT/'SOURCE_BEFORE/common_models.py'),'src/kmd_toc/common/models.py'],capture_output=True,text=True)
    (ROOT/'COMMON_MODEL_EXTENSION.patch').write_text(patch.stdout)
    files=[*Path('src/kmd_toc').rglob('*.py'),*Path('tests/toc_pipeline').glob('*.py')]
    files.extend(Path('configs/toc_delivery')/name for name in ['common_conditions_v1_1.json','a_rule_baseline_v1.json','ad_pipeline_v1.json','ad_pipeline_v2_route.json'])
    files.extend(Path('scripts')/name for name in ['build_common_road_od.py','build_route_pair_od.py','run_ad_method.py','run_ad_experiments.py','run_ad_reproducibility.py','audit_ad_results.py','audit_d_macro_scope.py','audit_ad_full_routes.py','audit_route_data.py','audit_ad_preservation.py','write_ad_reports.py','plot_ad_tradeoffs.py','wait_route_inputs_and_run.py','complete_ad_validation.py','bootstrap_local_osrm.py','review_road_connectivity.py','migrate_reviewed_od_cache.py'])
    files.extend(Path('scripts')/name for name in ['audit_d_attribution.py','summarize_ad_reproducibility.py','finish_d_lex_revision.py'])
    files.extend(ROOT/name for name in ['PREREGISTRATION.json','OD_RESOURCE_REVISION_1.json','D_LEX_POLICY_REVISION.json','EFFECTIVE_SETTINGS.json'])
    manifest={str(p):digest(p) for p in files};snapshot=ROOT/'SOURCE_SNAPSHOT'
    for p in files:
        q=snapshot/p;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(p.read_bytes())
    (ROOT/'SOURCE_HASHES.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('preservation',result['passed'],'unchanged',unchanged,'intended changed',len(changed),'frozen',len(frozen))

if __name__=='__main__':main()
