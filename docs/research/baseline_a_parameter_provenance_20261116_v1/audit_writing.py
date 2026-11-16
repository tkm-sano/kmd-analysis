"""Audit this documentation dossier without importing or running delivery methods.

All existing assets are read only. Outputs must use a fresh directory in this dossier.
Mechanical checks establish value/link/hash consistency, not historical motives or fit.
"""
from pathlib import Path
import argparse, ast, datetime, hashlib, json, re, subprocess
from urllib.parse import unquote

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()

def read(path):
    return json.loads(path.read_text())

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out-dir',required=True)
    args=parser.parse_args()
    dest=Path(args.out_dir).resolve()
    if not dest.is_relative_to(OUT):raise ValueError('output must be in this new dossier')
    dest.mkdir(exist_ok=False)
    checks=[]
    def check(name,actual,expected=True):
        checks.append({'check':name,'actual':actual,'expected':expected,'passed':actual==expected})
    def dump(name,data):
        with (dest/name).open('x') as f:json.dump(data,f,ensure_ascii=False,indent=2)

    c=read(ROOT/'configs/toc_delivery/common_conditions_v1_1.json')
    expected={'demand_per_stop':1,'capacity_per_trip':60,'max_trips_per_vehicle':2,
              'service_s':120,'loading_s':1800,'preparation_s':0,'opening_s':28800,
              'closing_s':72000,'first_ready_span_s':3600}
    for key,value in expected.items():check('common.operations.'+key,c['operations'][key],value)
    check('operational_values_measured',c['provenance']['operational_values']['measured'],False)
    check('customer_time_windows',c['scope']['customer_time_windows'],False)
    check('unused_vehicles_allowed',c['scope']['unused_vehicles_allowed'])
    check('first_ready_rule',c['first_ready_rule'],'opening_s + (3600 * (2*v+1)) // (2*V)')
    previous=read(ROOT/'configs/toc_delivery/common_conditions_v1.json')
    check('v1_0_preparation',previous['operations']['preparation_s'],900)
    check('v1_1_changed_operations',[k for k in expected if previous['operations'][k]!=c['operations'][k]],['preparation_s'])
    inputs=[]
    for scale,N,V,B in [('S1',1000,10,2),('S2',2000,20,4),('S3',4000,40,8)]:
        check(scale+'.counts',c['scenarios'][scale],{'stops':N,'vehicles':V,'berths':B})
        base=ROOT/'output/toc_delivery/ad_pipeline_20261112_route_v2/roads/inputs'/scale
        p=read(base/'input.json'); od=read(base/'od/manifest.json')
        check(scale+'.input_counts',[len(p['stops']),len(p['vehicles']),len(p['berths'])],[N,V,B])
        check(scale+'.demand',all(s['demand']==1 for s in p['stops']))
        check(scale+'.vehicles',all((v['capacity'],v['max_trips'],v['return_deadline_s'],v['first_ready_s'])==
              (60,2,72000,28800+(3600*(2*i+1))//(2*V)) for i,v in enumerate(p['vehicles'])))
        check(scale+'.berths',all((b['opening_s'],b['closing_s'],b['loading_s'],b['preparation_s'])==
              (28800,72000,1800,0) for b in p['berths']))
        check(scale+'.Route',od['metadata']['table_distances_used'],False)
        check(scale+'.directed',od['metadata']['directed'])
        check(scale+'.static',od['metadata']['traffic_time_dependence'],False)
        check(scale+'.version',od['metadata']['osrm_version'],'5.27.1')
        check(scale+'.OSM_time',od['metadata']['osm_timestamp'],'2026-07-16T20:21:30Z')
        inputs.append({'scale':scale,'input_sha256':sha(base/'input.json'),
                       'OD_manifest_sha256':sha(base/'od/manifest.json'),'metadata':od['metadata']})
        # Closed-form arithmetic for initial trips only; no delivery runner is used.
        # V=5B, loading=1800, ready period=3600: wait in group m is m*(1800-720).
        arithmetic_minutes=B*sum(m*(1800-3600*B//V) for m in range(V//B))/60
        check(scale+'.FCFS_initial_only_arithmetic',arithmetic_minutes,{'S1':360,'S2':720,'S3':1440}[scale])
    dump('INPUT_READ_CHECKS.json',inputs)

    freeze=read(ROOT/'configs/toc_delivery/comparison_a_rule_v1_freeze_20261115.json')
    frozen=[]
    for name,expected_hash in freeze['files'].items():
        actual=sha(ROOT/name);check('frozen:'+name,actual,expected_hash)
        frozen.append({'path':name,'sha256':actual,'expected':expected_hash})
    dump('FROZEN_A_HASH_CHECKS.json',frozen)
    a=read(ROOT/'configs/toc_delivery/a_rule_v1_20261115.json')
    for key,value in {'initial_angle_deg':0,'max_moves':'V','objective':['O_s','H_s2'],
                      'acceptance':'first strict lexicographic improvement','orderer':'nearest_order','fcfs':True}.items():
        check('A.algorithm.'+key,a['algorithm'][key],value)
    code=(ROOT/'src/kmd_toc/baseline_a/rule_v1.py').read_text()
    ast.parse(code)
    for token in ['range(0, len(order), 60)','clock += 120','math.ceil(t)',
                  'for _ in range(len(p.vehicles))','candidate_state[\'objective\'] < state[\'objective\']']:
        check('source_token:'+token,token in code)

    attempts=read(ROOT/'docs/research/baseline_a_rule_v1_20261115/ALL_ATTEMPTS.json')
    s2=[r for r in attempts if r['scale']=='S2' and r['status']=='VALIDATED' and 'checks01' in r['run_id']]
    plan_records=[]
    for r in s2:
        p=ROOT/r['output']/r['run_id']/'plan.json';h=sha(p)
        check('saved_S2_plan:'+r['run_id'],h,'64114d3fed738a14198c0958a4c3cdd6bafb9c9d81926bdaf276250bd651f4d9')
        check('saved_S2_reported_hash:'+r['run_id'],h,r['plan_sha256'])
        plan_records.append({'run_id':r['run_id'],'path':str(p.relative_to(ROOT)),'sha256':h})
    check('saved_S2_count',len(plan_records),2)
    check('saved_attempt_count',len(attempts),6)
    check('saved_failure_retained',sum(r['status']=='NO_FEASIBLE_PLAN' for r in attempts),1)
    dump('SAVED_RESULT_READ_CHECKS.json',plan_records)

    text=(OUT/'PARAMETER_PROVENANCE.md').read_text()
    records=[];scope='common'
    for line in text.splitlines():
        if line.startswith('## A固有'):scope='A_specific'
        if line.startswith('## 測定上'):scope='measurement'
        if re.match(r'^\|P\d\d ',line):
            cells=line.strip('|').split('|')
            check('provenance_column_count:'+cells[0],len(cells),9)
            names=['item','current_value','classification','history','source','original_reason',
                   'current_model_role','empirical_correspondence','unknowns']
            rec=dict(zip(names,cells));rec.update(id=cells[0][:3],scope=scope)
            records.append(rec)
    check('provenance_ID_coverage',sorted(r['id'] for r in records),[f'P{i:02}' for i in range(1,24)])
    check('no_duplicate_parameter_IDs',len({r['id'] for r in records}),len(records))
    check('unknown_choice_reason_explicit',all('理由' in r['original_reason'] or '目的' in r['original_reason'] or '仕様' in r['original_reason'] or '明記' in r['original_reason'] or '指示' in r['original_reason'] or '記録' in r['original_reason'] for r in records))
    dump('PARAMETER_PROVENANCE.json',{'classification_note':'C/D role is not evidence of the original motive; E retains unknown original choice reasons','parameters':records})
    essay=(OUT/'BASELINE_A_EXPLANATION_REVISED_JA.md').read_text()
    check('six_main_sections',len(re.findall(r'^## [1-6]．',essay,re.M)),6)
    check('matrix_all_parameters',all(f'P{i:02}' in (OUT/'PARAMETER_EVIDENCE_MATRIX.md').read_text() for i in range(1,24)))
    check('essay_distinguishes_102_120','102秒' in essay and '120秒' in essay and '変更理由' in essay)
    check('essay_distinguishes_role_and_initial_reason','当初の理由' in essay and '算術的' in essay)

    required=['PARAMETER_PROVENANCE.md','BASELINE_A_EXPLANATION_REVISED_JA.md',
              'PARAMETER_EVIDENCE_MATRIX.md','WRITING_REVIEW.md','FINAL_REPORT_JA.md','SOURCES.md']
    read_assets={}
    for name in required:
        file=OUT/name;check('artifact_exists:'+name,file.is_file())
        if not file.is_file():continue
        for target in re.findall(r'\]\(([^)]+)\)',file.read_text()):
            if re.match(r'https?://',target):continue
            fragment=target.split('#',1)[1] if '#' in target else None
            local=(file.parent/unquote(target.split('#',1)[0])).resolve()
            check('local_link:'+name+':'+target,local.is_file())
            if local.is_file():
                if not local.is_relative_to(OUT):read_assets[str(local.relative_to(ROOT))]=sha(local)
                if fragment:check('anchor:'+target,f'id="{fragment}"' in local.read_text())
    dump('REFERENCED_EXISTING_ASSET_HASHES.json',read_assets)

    captures=read(OUT/'SOURCE_ACCESS_LOG.json')['sources']+read(OUT/'SOURCE_ACCESS_SUPPLEMENT.json')
    for rec in captures:
        if rec.get('file'):check('source_saved_hash:'+rec['id'],sha(OUT/rec['file']),rec['sha256'])
    check('job_tag_direct_body_not_claimed',next(r for r in captures if r['id']=='S05')['status'],
          'HTTP_SUCCESS_BODY_NOT_CONFIRMED_USE_WEB_VIEW')
    browser=(OUT/'sources/web_primary_2.txt').read_text()
    check('job_tag_browser_body_confirmed','宅配便配達員' in browser and '次の荷物が到着' in browser)

    before=read(OUT/'PRESERVATION_BEFORE.json'); changes=[]
    for name,h in before['files'].items():
        p=ROOT/name;actual=sha(p) if p.is_file() else None
        if actual!=h:changes.append({'path':name,'before':h,'after':actual})
    check('protected_asset_changes',changes,[])
    head=subprocess.run(['git','rev-parse','HEAD'],cwd=ROOT,capture_output=True,text=True,check=True).stdout.strip()
    check('HEAD_preserved',head,before['HEAD'])
    status=subprocess.run(['git','status','--short','--untracked-files=normal'],cwd=ROOT,capture_output=True,text=True,check=True).stdout
    (dest/'GIT_STATUS_AFTER.txt').write_text(status)
    dump('PRESERVATION_CHECK.json',{'protected_count':len(before['files']),'changes':changes,'HEAD':head})
    result={'purpose':'documentation provenance/value/link/preservation audit; NOT solver tests or empirical validation',
            'checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'checks':checks,
            'passed':sum(c['passed'] for c in checks),'failed':sum(not c['passed'] for c in checks),
            'manual_review_required':['claim-to-source meaning','original motivation versus present role','empirical applicability']}
    dump('CHECKS.json',result)
    print(json.dumps({'passed':result['passed'],'failed':result['failed'],
                      'failed_checks':[c['check'] for c in checks if not c['passed']]},ensure_ascii=False))
    raise SystemExit(bool(result['failed']))

if __name__=='__main__':main()
