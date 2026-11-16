"""Independent evidence/decision audit. Does not execute delivery algorithms."""
from pathlib import Path
from decimal import Decimal
from fractions import Fraction
from urllib.parse import unquote, urlsplit, urlunsplit
import csv
import hashlib
import json
import re
import subprocess
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DOCS = ROOT / 'docs/research/toc_delivery_a'
NAMES = ['A_SAGAWA_MANUAL_BASELINE.md', 'A_SAGAWA_EVIDENCE_AUDIT.md',
         'A_SAGAWA_COMPARISON_DESIGN.md', 'A_SAGAWA_FINAL_DECISION.md']
ENTRY_NAMES = ['A_BASELINE_DECISION.md', 'A_PUBLIC_ONLY_PLAN.md', 'A_DATA_ACQUISITION_DECISION.md']


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1048576), b''): h.update(block)
    return h.hexdigest()


def normalize(url):
    p = urlsplit(url)
    return urlunsplit((p.scheme, p.netloc, unquote(p.path).rstrip('/'), p.query, ''))


def main():
    started = time.perf_counter()
    checks = []
    def check(name, condition):
        checks.append({'check': name, 'passed': bool(condition)})
        if not condition: raise AssertionError(name)

    data = json.loads((DOCS / 'A_SAGAWA_MANUAL_BASELINE.json').read_text())
    manifest = json.loads((HERE / 'SOURCE_MANIFEST.json').read_text())
    sources = {r['id']: r for r in manifest}
    check('15_unique_public_source_archives', len(manifest) == len(sources) == 15)
    for r in manifest:
        check(r['id'] + '_public_GET_received', r.get('method') == 'GET' and r.get('status') == 200 and not r.get('error'))
        check(r['id'] + '_raw_hash', sha(ROOT / r['archive']) == r['sha256'])
        if 'text' in r: check(r['id'] + '_text_hash', sha(ROOT / r['text']) == r['text_sha256'])
    check('HTTP200_shell_not_treated_as_detail', 'JavaScript' in (ROOT / sources['SAGAWA_RELEASE_SHELL']['text']).read_text())
    release = (ROOT / sources['OPTIMIND_RELEASE']['text']).read_text()
    copy = (ROOT / sources['PRTIMES_RELEASE']['text']).read_text()
    for term in ['2020年8月', '14日間', '80個', '位置確認', 'ルート組み時間', '休憩時間', '約500名']:
        check('source_context_' + term, term in release and term in copy)
    check('source_image_url_bound_to_release', any('png2.jpg' in str(i.get('src')) for i in sources['OPTIMIND_RELEASE']['images']))

    a = json.loads((HERE / 'TRANSCRIPTION_OPTIMIND.json').read_text())
    b = json.loads((HERE / 'TRANSCRIPTION_PRTIMES.json').read_text())
    for key, values in [('route_planning_reduction_min', [10, 15, 30]),
                        ('delivery_operations_reduction_min', [30, 60, 60]), ('distance_reduction_km', [10, 9, 11])]:
        check('two_publication_transcriptions_' + key, a[key] == b[key] == values)
    check('no_axis_or_percent_to_digitize', not a['before_after_axis_present'] and not a['percent_present'])
    check('copy_not_claimed_independent_measurement', 'NOT independent' in b['interpretation'])
    for filename in ['OPTIMIND_CHART.jpg', 'PRTIMES_CHART.jpg', 'OPTIMIND_OPERATION_IMAGE.jpg',
                     'KANTO_PAGE-60.png', 'KANTO_PAGE-61.png', 'MLIT_REPRINT_PAGE-338.png']:
        check('visual_artifact_' + filename, (HERE / 'sources' / filename).is_file())

    check('manual_before_only', data['latest_instruction'] == 'manual_before_only')
    check('no_performance_imputation', all(v is None for v in data['current_A_performance'].values()))
    check('seven_target_records', len(data['records']) == 7)
    for r in data['records']:
        for key in ['before_absolute', 'after_absolute', 'normalized_before', 'normalized_after', 'improvement_percent']:
            check(r['id'] + '_' + key + '_missing', r[key] is None)
        check(r['id'] + '_not_A_point', not r['adopted_as_A_performance'] and r['judgment'] == 'HOLD')
        check(r['id'] + '_unavailability_not_inferred', r['access_status'] == 'UNVERIFIED' and r['unavailable_not_proven'])
        check(r['id'] + '_source_trace', all(s in sources for s in r['source_ids']))
    with (DOCS / 'A_SAGAWA_MANUAL_BASELINE.csv').open() as f: rows = list(csv.DictReader(f))
    check('CSV_same_records', [r['id'] for r in rows] == [r['id'] for r in data['records']])
    for row, r in zip(rows, data['records']):
        for key in ['before_absolute', 'after_absolute', 'normalized_before', 'normalized_after', 'improvement_percent']:
            check(row['id'] + '_CSV_null_' + key, row[key] == '')
        check(row['id'] + '_CSV_units_and_status', row['unit'] == r['unit'] and row['adopted_as_A_performance'] == 'False')

    check('operating_interval_not_T', data['operation_illustration']['manual_T_s'] is None and not data['operation_illustration']['manual_T_3600_s_adopted'])
    check('illustration_interval_unit_conversion', (9*60+30)-(8*60+30) == data['operation_illustration']['clock_in_to_departure_min'] == 60)
    observation = data['separate_urban_distance_observation']
    distance_text = (ROOT / sources['SAGAWA_DISTANCE']['text']).read_text()
    check('13km_original_label', '13km' in distance_text and observation['truck_km'] == 13)
    check('2025_not_manual_before', observation['observation_date'] == '2025-01-10' and not observation['pre_Loogia_manual_confirmed'] and not observation['adopted_as_A_performance'])
    case = data['separate_interdepot_case']
    check('26_min_loading_not_180_min_work', case['loading_wait_min_by_displayed_stage'] == [26, 26] and case['loading_work_min_by_displayed_stage'] == [180, 229])
    check('loading_and_unloading_separated', case['unloading_wait_min_by_displayed_stage'] == [72, 20])
    check('interdepot_not_ToC', case['business'] == 'interdepot_transport_not_ToC_last_mile' and not case['adopted_as_A_performance'])
    check('interdepot_event_definition_unknown', case['ready_definition_matches_common_W'] is None and case['T_s'] is None and case['distance_km'] is None)
    check('no_W_after_or_rate', case['W_after_loading_wait_min'] is None and case['W_improvement_percent'] is None)
    kanto_pages = (ROOT / sources['KANTO_CASE']['text']).read_text().split('\f')
    reprint_pages = (ROOT / sources['MLIT_CASE_REPRINT']['text']).read_text().split('\f')
    check('Kanto_locator', '荷役完全分離' in kanto_pages[59] and '佐川急便' in kanto_pages[59])
    check('reprint_locator', '荷役完全分離' in reprint_pages[337])
    check('results_not_W_outcome', '15時間40分' in kanto_pages[60] and '47%⇒39%' in kanto_pages[60])

    # Independent arithmetic formulations; these are audit calculations, not new operational estimates.
    minutes_decimal = Decimal(15)*60 + Decimal(40)
    minutes_fraction = Fraction(24*60+8*60+15) - Fraction(16*60+35)
    components = sum(case['driving_min_by_displayed_stage'] + case['loading_wait_min_by_displayed_stage'] +
                     case['unloading_wait_min_by_displayed_stage'] + case['loading_work_min_by_displayed_stage'] + case['unloading_work_min_by_displayed_stage'])
    check('independent_elapsed_calculations', minutes_decimal == minutes_fraction == case['duty_min_before_reported'] == 940)
    check('mismatch_preserved_not_fixed', components == case['sum_displayed_components_min'] == 985 and components-int(minutes_fraction) == case['unresolved_difference_min'] == 45)
    check('Kisarazu_interval_mismatch', 26+180 != (20-17)*60)
    check('Kamogawa_interval_mismatch', 20+37 != (7*60+5)-(6*60+45))
    for delta in data['nonadopted_difference_evidence']['D_reduction_km'] + data['nonadopted_difference_evidence']['T_route_reduction_min']:
        # Two synthetic possible pairs prove that one reduction does not identify its denominator.
        p1 = (2*delta, delta); p2 = (3*delta, 2*delta)
        check('delta_' + str(delta) + '_does_not_identify_before', p1[0]-p1[1] == p2[0]-p2[1] == delta and p1[0] != p2[0])
    check('never_assume_after_zero', not data['nonadopted_difference_evidence']['infer_after_zero_allowed'])
    check('no_alternative_adopted', not data['alternative_baseline_adopted'] and not data['proposals']['proposal_adopted'])
    check('no_contact_no_optimization', not data['outbound_contact_executed'] and not data['large_scale_experiment_executed'])

    known = {normalize(r['url']) for r in manifest} | {normalize(r.get('final_url', r['url'])) for r in manifest}
    for name in NAMES:
        text = (DOCS / name).read_text()
        check(name + '_version', data['decision_version'] in text)
        check(name + '_whitespace', all(l == l.rstrip() for l in text.splitlines()))
        for target in re.findall(r'\]\(([^)]+)\)', text):
            if target.startswith(('http://', 'https://')):
                check(name + '_primary_link_' + target, normalize(target) in known)
            else:
                check(name + '_local_link_' + target, (DOCS / target.split('#')[0]).exists())
    baseline_doc = (DOCS / NAMES[0]).read_text()
    check('documents_D_W_T_missing', all(s in baseline_doc for s in ['D：全車両総走行距離[km]|未取得', 'W：Σ(積込開始−積込準備完了)[分]|未取得', 'T：計画作成経過時間[秒]|未取得']))
    check('documents_record_26_and_13_exclusion', '平均26分' in baseline_doc and '13km' in baseline_doc and '今回のA条件では不採用' in baseline_doc)
    for name in ENTRY_NAMES:
        old = (HERE / 'before' / name).read_bytes()
        current = (DOCS / name).read_bytes()
        check(name + '_historical_body_preserved', current.endswith(old))
        check(name + '_new_decision_link', b'A_SAGAWA_FINAL_DECISION.md' in current[:1800])

    context = json.loads((HERE / 'CONTEXT_AUDIT.json').read_text())
    check('common_config_unchanged', sha(ROOT / data['target_conditions']['config']) == data['target_conditions']['sha256'] == context['common_conditions_sha256'] == 'bbb15417a4eee5072f8118056c90ab422d792b4cedc35a6a06bf6bc0497fe8d2')
    check('8_frozen_files', len(context['frozen_files']) == 8)
    for path, expected in context['frozen_files'].items(): check('frozen_' + path, sha(ROOT / path) == expected)

    before = json.loads((HERE / 'PRESERVATION_BEFORE.json').read_text())
    intended = {'docs/research/toc_delivery_a/' + s for s in ENTRY_NAMES}
    changes = []; missing = []
    for path, expected in before['files'].items():
        p = ROOT / path
        if not p.exists(): missing.append(path)
        elif sha(p) != expected: changes.append(path)
    check('no_unintended_existing_changes', not missing and set(changes) == intended)
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    check('no_commit', head == before['head'])
    preservation = {'checked_files': len(before['files']), 'unchanged_files': len(before['files'])-len(changes)-len(missing),
                    'intended_changed_files': changes, 'unexpected_changed_files': sorted(set(changes)-intended),
                    'missing_files': missing, 'frozen_unchanged': 8, 'head_unchanged': head == before['head'], 'scope': before['scope']}
    (HERE / 'PRESERVATION_RESULT.json').write_text(json.dumps(preservation, ensure_ascii=False, indent=2) + '\n')
    (HERE / 'VALIDATION_RESULTS.json').write_text(json.dumps({'passed': len(checks), 'failed': 0, 'checks': checks,
        'elapsed_wall_s': time.perf_counter()-started,
        'scope': 'public evidence and decision audit; no validation of unobserved operations; no solver experiment'}, ensure_ascii=False, indent=2) + '\n')
    print(f'{len(checks)} checks passed; {len(before["files"])} preexisting files checked; 8 frozen files unchanged')


if __name__ == '__main__':
    main()
