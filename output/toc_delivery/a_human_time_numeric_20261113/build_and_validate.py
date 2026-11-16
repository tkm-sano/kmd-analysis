"""Freeze evidence-backed numeric references without fabricating scenario results."""
import csv
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
CONFIG = REPO / 'configs/toc_delivery/a_human_time_numeric_adoption_v1.json'
DOC = REPO / 'docs/research/toc_delivery_a/A_HUMAN_T_NUMERIC_ADOPTION.md'
config = json.loads(CONFIG.read_text())
primary = config['primary_reference']
individual = config['individual_route_reference']
rows = [
    dict(metric='T_dispatch_external_reference', condition='center_day', min_s=primary['published_range_s'][0],
         reference_point_s=primary['adopted_reference_point_s'], max_s=primary['published_range_s'][1],
         unit=primary['unit'], value_kind='published_range_and_research_selected_midpoint',
         source_url=primary['url'], applicable_as_S1_full_human_T=False),
    dict(metric='T_human_route_creation', condition='experienced', min_s=individual['experienced_range_s'][0],
         reference_point_s=None, max_s=individual['experienced_range_s'][1], unit=individual['unit'],
         value_kind='published_case_range', source_url=individual['url'], applicable_as_S1_full_human_T=False),
    dict(metric='T_human_route_creation', condition='novice', min_s=individual['novice_range_s'][0],
         reference_point_s=None, max_s=individual['novice_range_s'][1], unit=individual['unit'],
         value_kind='published_case_range', source_url=individual['url'], applicable_as_S1_full_human_T=False),
]
with (ROOT / 'ADOPTED_VALUES.csv').open('w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
(ROOT / 'ADOPTED_VALUES.json').write_text(json.dumps(config, ensure_ascii=False, indent=2) + '\n')
table = '''<!-- BEGIN GENERATED NUMERIC REFERENCES -->
|用途|下端［秒］|採用代表点［秒］|上端［秒］|元の単位|
|---|---:|---:|---:|---|
'''
labels = ['拠点全体の配車・外部参照', '個別ルート作成・熟練者', '個別ルート作成・新人']
units = ['センター・日', '人手ルート作成1回', '人手ルート作成1回']
for row, label, unit in zip(rows, labels, units):
    point = format(row['reference_point_s'], ',') if row['reference_point_s'] is not None else '設定しない'
    table += f"|{label}|{row['min_s']:,}|{point}|{row['max_s']:,}|{unit}|\n"
table += '<!-- END GENERATED NUMERIC REFERENCES -->'
text = DOC.read_text()
pattern = r'<!-- BEGIN GENERATED NUMERIC REFERENCES -->.*?<!-- END GENERATED NUMERIC REFERENCES -->'
text, replacements = re.subn(pattern, lambda _: table, text, flags=re.S)
assert replacements == 1
DOC.write_text(text)

checks = []
def check(name, ok):
    checks.append({'name': name, 'passed': bool(ok)})
check('hours-to-seconds lower', primary['published_range_s'][0] == 7 * 3600)
check('hours-to-seconds upper', primary['published_range_s'][1] == 8 * 3600)
check('midpoint arithmetic', primary['adopted_reference_point_s'] == sum(primary['published_range_s']) / 2)
check('point is 7.5h', primary['adopted_reference_point_s'] / 3600 == 7.5)
check('point identified as research selection', primary['point_value_kind'] == 'research_selection_derived_from_published_range')
check('not observed mean', primary['point_is_observed_mean_or_median'] is False)
check('not measured S1 time', primary['point_is_measured_S1_time'] is False)
check('not unverified wall time', primary['definition_matched_human_wall_time_verified'] is False)
check('source population unknown retained', all(primary[k] is None for k in ['target_stops', 'target_vehicles', 'target_planners']))
source = REPO / 'output/toc_delivery/a_government_evidence_20261113/sources/mlit_it_guide.txt'
source_page = re.sub(r'\s+', '', source.read_text().split('\f')[6])
check('primary source original time and unit', '毎日7～8時間' in source_page and '1センター' in source_page)
reference = json.loads((REPO / individual['source_config']).read_text())
for key in ['experienced', 'novice']:
    old = reference['experience_conditions'][key]
    check('individual reference unchanged:' + key, individual[key + '_range_s'] == [old['min_s'], old['max_s']])
check('no combined different-scope total', individual['add_to_primary_reference'] is False)
check('no unjustified scenario time', all(v is None for v in config['full_A_human_T_s'].values()))
check('no unsupported scaling', config['scaling_by_stops_or_vehicles'] is None)
check('existing solvers not changed to use external time', config['automatically_used_by_existing_solvers'] is False)
check('generated table agrees', table in DOC.read_text())
check('config copy agrees', json.loads((ROOT / 'ADOPTED_VALUES.json').read_text()) == config)
with (ROOT / 'ADOPTED_VALUES.csv').open() as f:
    saved = list(csv.DictReader(f))
check('CSV main value agrees', saved[0]['reference_point_s'] == str(primary['adopted_reference_point_s']))
baseline = json.loads((ROOT / 'PRESERVATION_BEFORE.json').read_text())
changed = []
for name, expected in baseline['files'].items():
    path = REPO / name
    ok = path.exists() and hashlib.sha256(path.read_bytes()).hexdigest() == expected
    check('preserved:' + name, ok)
    if not ok: changed.append(name)
status = subprocess.check_output(['git', 'status', '--short', '--untracked-files=no'], cwd=REPO, text=True)
check('existing tracked changes preserved', status == baseline['git_status'])
result = dict(checks=len(checks), passed=sum(c['passed'] for c in checks),
              failed=[c for c in checks if not c['passed']], changed_existing_files=changed,
              new_numeric_reference_config=str(CONFIG.relative_to(REPO)),
              empirical_full_human_T_determined=False, details=checks)
(ROOT / 'VALIDATION.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({k: v for k, v in result.items() if k != 'details'}, ensure_ascii=False, indent=2))
raise SystemExit(bool(result['failed']))
