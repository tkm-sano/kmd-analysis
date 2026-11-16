"""Audit published values, unit conversions and non-comparability flags only."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


def main():
    data = json.loads((ROOT/'docs/research/toc_delivery_a/A_REFERENCE_VALUES.json').read_text())
    checks = []
    def check(name, condition):
        checks.append({'check':name,'passed':bool(condition)})
        if not condition:
            raise AssertionError(name)
    for sid, source in data['sources'].items():
        content = (ROOT/source['archive']).read_bytes()
        check(sid+'_original_hash',hashlib.sha256(content).hexdigest()==source['sha256'])
    distance_text = (ROOT/data['sources']['E05']['text']).read_text()
    jp_text = (ROOT/data['sources']['E07']['text']).read_text()
    records = {r['id']:r for r in data['external_references']}
    check('truck_not_walking_distance','トラック走行距離：13km' in distance_text and records['A_D_urban']['value']==13)
    check('distance_observation_date','2025年1月10日' in distance_text and records['A_D_urban']['observation_date']=='2025-01-10')
    check('JP_experienced_original','5分～10分' in jp_text)
    check('JP_novice_original','30分～1時間' in jp_text)
    check('JP_system_assisted_original','10分〜15分' in jp_text)
    check('JP_article_asof_2021','本記事は2021年時点' in jp_text)
    for name, minutes, seconds in [('A_T_experienced',[5,10],[300,600]),('A_T_novice',[30,60],[1800,3600])]:
        rec = records[name]
        check(name+'_minute_conversion',rec['original_range_minutes']==minutes and rec['range']==seconds
              and [x*60 for x in minutes]==seconds)
        check(name+'_common_boundary_not_claimed',rec['common_T_boundary_matched'] is False)
    check('missing_W_is_null',data['missing_metrics']['W_min']['value'] is None)
    check('no_joint_observation',data['joint_observation'] is False)
    for scenario,n,v,b in [('S1',1000,10,2),('S2',2000,20,4),('S3',4000,40,8)]:
        rec = data['scenarios'][scenario]
        check(scenario+'_same_scope_missing',all(rec[k] is None for k in ('D_km','W_min','T_s')))
        check(scenario+'_research_sizes_preserved',(rec['stops'],rec['vehicles'],rec['berths'])==(n,v,b))
    check('role_external_only',data['role']=='external_references_by_metric' and data['status']=='CONDITIONAL GO')
    check('time_value_kind_is_operator_report',all('operator_reported' in r['value_kind'] for r in data['external_references'] if r['metric']=='T_route_preparation_s'))
    check('no_optimization_required',data['method_A_optimization_required'] is False)
    out={'checks':checks,'passed':len(checks),'failed':0,'interpretation':'source assertions and arithmetic; not independent measurement of business operations'}
    (HERE/'REFERENCE_VALIDATION.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    print(f'{len(checks)} checks passed; no optimizer or demand generator called')


if __name__=='__main__':
    main()
