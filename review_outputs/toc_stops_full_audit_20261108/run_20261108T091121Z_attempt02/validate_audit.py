"""Independent CSV readback of completed audit outputs; never runs study tests."""
import collections
import csv
import hashlib
import json
from pathlib import Path
import re

O=Path(__file__).resolve().parent
ROOT=O.parents[2]
rank={'PASS':0,'CONDITIONAL':1,'HOLD':2,'FAIL':3}
def rows(name):
    with (O/name).open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
    ledger=rows('ALL_STOPS_AUDIT.csv');exc=rows('AUDIT_EXCEPTIONS.csv');regions=rows('REGIONAL_COVERAGE.csv')
    summary=json.loads((O/'AUDIT_SUMMARY.json').read_text())
    byid={r['audit_row_id']:r for r in ledger};checks={}
    checks['all_39956_rows_unique_audit_record']=len(ledger)==len(byid)==39956
    checks['all_original_ids_unique']=len({r['stop_id'] for r in ledger})==len({r['building_id'] for r in ledger})==39956
    checks['source_row_order_preserved']=all(int(r['audit_row_id'])==i+1 and int(r['source_csv_line'])==i+2 for i,r in enumerate(ledger))
    checks['all_building_id_formats_valid']=all(re.fullmatch(r'13111-bldg-\d+',r['building_id']) for r in ledger)
    checks['all_stop_id_formats_valid']=all(re.fullmatch(r'\d{4}-\d{2}-\d{2}-13111-bldg-\d+',r['stop_id']) for r in ledger)
    checks['status_counts_from_csv_match_json']=dict(collections.Counter(r['overall_status'] for r in ledger))==summary['status_counts']
    domain_cols=[c+'_status' for c in summary['per_domain_counts']]
    checks['overall_status_is_worst_domain']=all(r['overall_status']==max((r[c] for c in domain_cols),key=rank.get) for r in ledger)
    ex_by=collections.defaultdict(set)
    for e in exc:
        assert e['audit_row_id'] in byid
        ex_by[e['audit_row_id']].add(e['reason_code'])
    checks['all_reason_codes_have_exception_evidence']=all(set(filter(None,r['reason_codes'].split(';')))==ex_by[r['audit_row_id']] for r in ledger)
    checks['regional_counts_recomputed']=True
    groups=collections.defaultdict(collections.Counter)
    for r in ledger:groups[r['chocho_code']][r['overall_status']]+=1
    for r in regions:
        if sum(groups[r['chocho_code']].values())!=int(r['original_count']):checks['regional_counts_recomputed']=False
        for s in rank:
            if groups[r['chocho_code']][s]!=int(r[s]):checks['regional_counts_recomputed']=False
    checks['no_row_has_missing_verdict']=all(all(r[c] in rank for c in domain_cols+['overall_status','location_status','road_status']) for r in ledger)
    quota=rows('STRATIFIED_QUOTA_CHECK.csv')
    quota_groups=collections.defaultdict(list)
    for r in quota:quota_groups[(r['N'],r['policy'])].append(r)
    checks['quota_sums_equal_N']=all(sum(int(r['quota_preserving_original_share']) for r in group)==int(k[0]) for k,group in quota_groups.items())
    checks['quota_shortages_recomputed']=all(int(r['shortage'])==max(0,int(r['quota_preserving_original_share'])-int(r['available_count'])) for r in quota)
    manifest=json.loads((O/'INPUT_MANIFEST.json').read_text())
    checks['all_consumed_inputs_unchanged']=all(sha(Path(r['path']))==r['sha256'] for r in manifest if r['exists'])
    unique_reason_counts=collections.Counter()
    for codes in ex_by.values():unique_reason_counts.update(codes)
    result={'checks':checks,'all_checks_pass':all(checks.values()),'rows_read':len(ledger),'exception_records':len(exc),'unique_stop_reason_counts':dict(unique_reason_counts),'code_sha256':sha(Path(__file__)),'not_a_simulation_or_solver_test':True}
    with (O/'INDEPENDENT_AUDIT_VALIDATION.json').open('x') as f:json.dump(result,f,ensure_ascii=False,indent=2)
    print(json.dumps(result,ensure_ascii=False))
    assert result['all_checks_pass']
if __name__=='__main__':main()
