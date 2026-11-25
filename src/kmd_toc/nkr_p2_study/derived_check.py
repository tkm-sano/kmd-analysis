"""Compare closed-data analysis before/after observer-only reader changes."""
import csv
import json
from .study import OUT,read,dump,digest

NAMES=['GROUPS.csv','BRANCHES.csv','CALLS.csv','ITERATIONS.csv','CANDIDATES.csv','ALL54.csv']


def main(snapshot=False):
    saved=OUT/'previous_derived_analysis'
    if snapshot:
        if saved.exists():raise ValueError('DERIVED_SNAPSHOT_EXISTS')
        for job in (OUT/'groups').glob('*/branch_*/JOB.json'):
            if not (job.parent.parent/'GROUP.json').exists():raise ValueError('GROUP_STILL_ACTIVE')
        saved.mkdir()
        for name in NAMES+['ANALYSIS_PROVENANCE.json']:
            (saved/name).write_bytes((OUT/name).read_bytes())
        return
    with (saved/'GROUPS.csv').open() as f:baseline_groups={r['tag'] for r in csv.DictReader(f) if r['status']=='COMPLETE'}
    checks=[]
    for name in NAMES:
        with (saved/name).open() as f:before=list(csv.DictReader(f))
        with (OUT/name).open() as f:after=list(csv.DictReader(f))
        if name=='ALL54.csv':
            before=[r for r in before if r['status']=='COMPLETE']
            keys={(r['scale'],r['n'],r['K'],r['R']) for r in before}
            after=[r for r in after if (r['scale'],r['n'],r['K'],r['R']) in keys]
        else:
            before=[r for r in before if r['tag'] in baseline_groups]
            after=[r for r in after if r['tag'] in baseline_groups]
        assert len(before)==len(after),(name,len(before),len(after))
        for index,(a,b) in enumerate(zip(before,after)):
            assert all(b.get(k)==v for k,v in a.items()),(name,index,[k for k,v in a.items() if b.get(k)!=v])
        checks.append({'table':name,'rows_identical_on_all_previous_fields':len(before),'previous_sha256':digest(saved/name),'new_sha256':digest(OUT/name)})
    prior_choice=read(saved/'FOLLOWUP_SELECTION_V3.json')['chosen_from_A']
    current_choice=read(OUT/'FOLLOWUP_SELECTION_V3.json')['chosen_from_A']
    key=lambda r:(r['scale'],int(r['n']),int(r['K']),int(r['R']),int(r['outer_seed']))
    assert sorted(map(key,prior_choice))==sorted(map(key,current_choice))
    restart=read(OUT/'ANALYSIS_RESTART.json')
    assert all(digest(OUT/name)==expected for name,expected in restart['completed_group_hashes'].items())
    result={'status':'PASS_PREVIOUS_MEASURED_FIELDS_IDENTICAL','scope':'all prior completed-group rows on previous fields; newly completed groups checked separately by raw ledger audit','baseline_complete_groups':sorted(baseline_groups),'selected_comparison_settings_unchanged':True,'all_pre_restart_group_hashes_unchanged':True,'checks':checks,'previous_analysis':read(saved/'ANALYSIS_PROVENANCE.json'),'new_analysis':read(OUT/'ANALYSIS_PROVENANCE.json')}
    dump(OUT/'DERIVED_READER_CHECK.json',result)
    print(json.dumps({k:v for k,v in result.items() if k not in ('previous_analysis','new_analysis')},indent=2))


if __name__=='__main__':
    import sys
    main('--snapshot' in sys.argv)
