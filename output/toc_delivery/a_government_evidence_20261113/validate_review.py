"""Offline checks of evidence, arithmetic, provenance, and preservation.

Does not invoke the planning algorithms, mutate their configs, or rerun experiments.
"""
import csv
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
DOC = REPO / 'docs/research/toc_delivery_a'
checks = []


def check(name, condition):
    checks.append({'check': name, 'passed': bool(condition)})


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


evidence = json.loads((ROOT / 'EVIDENCE.json').read_text())
rows = {r['evidence_id']: r for r in evidence}
sources = json.loads((ROOT / 'SOURCE_MANIFEST.json').read_text())
src = {s['id']: s for s in sources}
check('18 unique evidence rows', len(evidence) == len(rows) == 18)
with (ROOT / 'EVIDENCE.csv').open() as f:
    csv_rows = list(csv.DictReader(f))
check('CSV/JSON row count', len(csv_rows) == len(evidence))
check('docs CSV equals output CSV', (ROOT / 'EVIDENCE.csv').read_bytes() ==
      (DOC / 'A_GOVERNMENT_EVIDENCE_REGISTER.csv').read_bytes())
required = ['url', 'publisher', 'business', 'reported_value', 'reported_unit',
            'scope', 'measurement_boundary', 'adoption', 'reason', 'page_or_section']
for row, csv_row in zip(evidence, csv_rows):
    check(row['evidence_id'] + ': required fields', all(row[k] for k in required))
    check(row['evidence_id'] + ': no full A T fabricated', row['full_A_T_s'] is None and
          row['used_in_existing_experiments'] is False)
    check(row['evidence_id'] + ': CSV scalar values equal', all(
        csv_row[k] == str(row[k]) for k in required))
    check(row['evidence_id'] + ': source reference', row['source_id'] in src and
          src[row['source_id']]['url'] == row['url'])
    if row['verification_status'] == 'retained_original':
        check(row['evidence_id'] + ': source semantic status', src[row['source_id']].get('semantic_content_verified') is True)

for s in sources:
    for path_key, hash_key in [('path', 'sha256'), ('text_path', 'text_sha256')]:
        if s.get(path_key):
            p = REPO / s[path_key]
            check(s['id'] + ':' + path_key + ' hash', p.exists() and sha(p) == s[hash_key])


def page(sid, number):
    return (REPO / src[sid]['text_path']).read_text().split('\f')[number - 1]


compact = lambda s: re.sub(r'\s+', '', s)
kyoei = compact(page('mlit_it_guide', 7))
check('Kyoei original center/day and before/after', all(t in kyoei for t in
      ['協栄流通', '1センター', '毎日7～8時間', '2～3時間']))
check('Kyoei seconds independently recomputed', rows['G06']['before_time_s'] == [7 * 3600, 8 * 3600])
check('Kyoei target N/V/P not borrowed from corporate totals', all(
      rows['G06'][k] is None for k in ['planning_stops', 'planning_vehicles', 'planning_workers']))
tamano = compact(page('mlit_tamano', 31))
check('Tamano primary separates receipt and planning', '予約受付：５分→３分' in tamano and '配車計画作成：20分→５分' in tamano)
check('Tamano minutes converted independently', rows['G08']['before_time_s'] == [20 * 60, 20 * 60])
check('Tamano V remains unknown, no Kumenan 5-vehicle transfer', rows['G08']['planning_vehicles'] is None)
miura = compact(page('mlit_agri_miura', 55))
check('Miura primary body has 8h', '人手では８時間' in miura)
check('Miura conflict retained and no merged seconds', '5～6時間' in rows['G07']['reported_value'] and
      rows['G07']['before_time_s'] is None and rows['G07']['adoption'].startswith('HOLD'))
logitem = compact(page('maff_logitem', 7))
check('Logitem paper/veteran/manual/below-half primary', all(x in logitem for x in ['日本ロジテム', '紙', 'ベテラン', '手作業', '半分以下']))
check('Logitem no invented absolute', rows['G04']['before_time_s'] is None)
check('Logitem publication deduplication', rows['G04']['duplicate_group'] == rows['G05']['duplicate_group'])
check('METI latest remains unverified', rows['G05']['verification_status'] == 'indexed_only_http403')
check('Hayashi absolute not adopted from search', rows['G10']['adoption'].startswith('HOLD') and rows['G10']['before_time_s'] is None)
jp = compact((REPO / src['nihonyubin']['text_path']).read_text())
check('Japan Post original before ranges', all(x in jp for x in ['ベテランが5分～10分', '新人は30分～1時間', '紙の地図']))
check('Japan Post planning unit N/V/P unknown', all(rows['V01'][k] is None for k in
      ['planning_stops', 'planning_vehicles', 'planning_workers']))
suwa = compact((REPO / src['suwa']['text_path']).read_text())
check('Suwa detailed boundary and duration', all(x in suwa for x in ['2時間30分から3時間', '100〜150件', '6〜7台', '重量のチェック']))
check('Suwa independent conversion', rows['V02']['before_time_s'] == [150 * 60, 180 * 60])
ctc = compact((REPO / src['ctc_trivalue']['text_path']).read_text())
check('CTC primary actual before and scale', all(x in ctc for x in ['92件', '10台', '手組で3時間']))
check('CTC before not improved time', rows['V03']['before_time_s'] == [3 * 3600, 3 * 3600])
smrj = compact(page('smrj_billing', 1))
check('SMRJ wrong boundary identified from primary', '配車入力～請求金額確定' in smrj)
check('SMRJ not classified as ministry', rows['Q01']['source_priority'] is None)
check('MHLW HTTP200 challenge is not successful source body', src['mhlw_jobtag']['semantic_content_verified'] is False)
check('METI copy not claimed original-URL byte match', rows['G03']['verification_status'] == 'ministry_document_third_party_copy')
for filename in ['mlit_it_guide_page7.png', 'mlit_agri_miura_page55.png',
                 'mlit_tamano_page31.png', 'mlit_dispatch_page19.png']:
    check('visually reviewed page retained:' + filename, (ROOT / 'sources' / filename).stat().st_size > 10000)

decision = json.loads((ROOT / 'ADOPTION_DECISION.json').read_text())
check('Full A manual T S1/S2/S3 remains unknown', all(v is None for v in decision['full_A_human_T_s'].values()))
check('No empirical calibration or existing experiment overwrite',
      decision['applied_to_existing_experiments'] is False and decision['research_rules_or_coefficients_modified'] is False)
check('Route reference not replaced', decision['individual_route_reference_replaced'] is False)
reference = json.loads((REPO / decision['individual_route_reference_config']).read_text())
check('Existing route config remains external only', reference['kind'] == 'external_literature_reference_only')
check('Existing route config not automatically active', reference['automatically_used_in_existing_experiments'] is False)
for name in ['A_GOVERNMENT_EVIDENCE_AUDIT.md', 'A_METHOD_AND_HUMAN_T_EVIDENCE_DECISION.md']:
    text = (DOC / name).read_text()
    check(name + ': seconds and evidence', '25,200' in text and 'CONDITIONAL GO' in text and 'HOLD' in text)

preserved = json.loads((ROOT / 'PRESERVATION_BEFORE.json').read_text())
changes = []
for rel, original in preserved['files'].items():
    path = REPO / rel
    ok = path.exists() and sha(path) == original
    check('preservation:' + rel, ok)
    if not ok:
        changes.append(rel)
status = subprocess.check_output(['git', 'status', '--short', '--untracked-files=no'], cwd=REPO, text=True)
check('tracked git status unchanged', status == preserved['git_status'])
frozen = [p for p in preserved['files'] if '/frozen_demand/v1/' in p]
check('eight frozen demand artifacts preserved', len(frozen) == 8 and not any(x in changes for x in frozen))
result = {'scope': 'offline evidence and preservation verification; no algorithm test or experiment',
          'checks': len(checks), 'passed': sum(c['passed'] for c in checks),
          'failed': [c for c in checks if not c['passed']], 'details': checks,
          'preserved_existing_files': len(preserved['files']), 'changed_existing_files': changes,
          'frozen_files': len(frozen), 'evidence_rows': len(evidence)}
(ROOT / 'VALIDATION.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({k: v for k, v in result.items() if k != 'details'}, ensure_ascii=False, indent=2))
raise SystemExit(bool(result['failed']))
