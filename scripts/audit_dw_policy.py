#!/usr/bin/env python3
"""Audit the D/W migration without running experiments or changing old data."""
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
from xml.etree import ElementTree as ET
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from kmd_toc.dw import HYPOTHESIS, RQ, digest, load_policy, read
from kmd_toc.contracts import load_study

AUDIT = ROOT/'docs/audits/dw_policy_20261117_v1'
CURRENT_DOCS = ('DW_RESEARCH_POLICY.md', 'TOC_DELIVERY_SPEC.md', 'A_TO_D_COMPARISON.md',
    'A_TO_D_COMMON_INTERFACE.md', 'BASELINE_A_DESIGN.md', 'CPU_PARALLEL_EXECUTION.md',
    'DWT_EXPERIMENT_DESIGN.md', 'DWT_MULTI_OBJECTIVE_FORMULATION.md', 'DWT_PILOT_DESIGN.md',
    'DWT_STATISTICAL_PROTOCOL.md', 'DWT_SAMPLE_SIZE_PIPELINE.md', 'DWT_7_FIGURES_SPEC.md', 'REPRODUCE.md')
GUARDED = ('run_dwt.py', 'run_dwt_bundle.py', 'run_comparison_v1.py', 'run_comparison_design.py',
    'run_comparison_design_supplement.py', 'run_termination_rules.py', 'run_human_comparison_v1.py',
    'render_dwt.py', 'finalize_dwt.py')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true', help='Write derived audit files only')
    args = parser.parse_args()
    checks = {}
    policy = load_policy(ROOT/'configs/toc_delivery/dw_policy_20261117_v1.json')
    study = load_study(ROOT/'configs/toc_delivery/study.json')
    checks['policy_and_initial_scope_are_two_objective'] = set(policy['objectives']) == {'D','W'} and study['figures']['count'] == 4
    active = [ROOT/'README.md', ROOT/'AGENTS.md', ROOT/'BASELINE_A_METHOD.md']
    active += [ROOT/'docs/research'/name for name in CURRENT_DOCS]
    links, stale = [], []
    old_rq = read(AUDIT/'before/configs/toc_delivery/study.json')['rq']
    for path in active:
        text = path.read_text()
        if old_rq in text:
            stale.append(str(path.relative_to(ROOT)))
        for target in re.findall(r'\]\(([^)]+)\)',text):
            if re.match(r'\w+://|#',target):
                continue
            clean = target.split('#',1)[0]
            if clean and not (path.parent/clean).resolve().exists():
                links.append({'file':str(path.relative_to(ROOT)),'target':target})
    checks['active_local_links_exist'] = not links
    checks['old_rq_not_in_current_documents'] = not stale
    for name in ('README.md','docs/research/DW_RESEARCH_POLICY.md','docs/research/BASELINE_A_DESIGN.md'):
        text = (ROOT/name).read_text()
        checks['exact_rq_hypothesis:'+name] = RQ in text and HYPOTHESIS in text
    checks['old_cli_requires_explicit_history'] = all('HISTORICAL_ENTRYPOINT' in (ROOT/'scripts'/name).read_text() for name in GUARDED)
    protected = read(AUDIT/'PRESERVATION_BEFORE.json')
    changed = [name for name,h in protected.items() if not (ROOT/name).exists() or digest(ROOT/name) != h]
    allowed = {'README.md','configs/toc_delivery/study.json'}
    unexpected = [name for name in changed if name not in allowed]
    checks['protected_data_results_and_old_registrations_unchanged'] = not unexpected
    docx = ROOT/'research_plan_toc_two_objectives_20261117.docx'
    with ZipFile(docx) as archive:
        checks['docx_zip_integrity'] = archive.testzip() is None
        for name in archive.namelist():
            if name.endswith(('.xml','.rels')):
                ET.fromstring(archive.read(name))
        document = ET.fromstring(archive.read('word/document.xml'))
    ns = {'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    text = '\n'.join(''.join(t.text or '' for t in p.findall('.//w:t',ns)) for p in document.findall('.//w:p',ns))
    checks['docx_exact_rq_hypothesis'] = RQ in text and HYPOTHESIS in text
    checks['docx_has_no_legacy_figures'] = not document.findall('.//w:drawing',ns)
    data = read(ROOT/'output/toc_delivery/dw_policy_20261117_v1/DW_ANALYSIS.json')
    checks['all_saved_pilot_attempts_included'] = len(data['rows']) == 75 and len({r['run_id'] for r in data['rows']}) == 75
    checks['analysis_projects_only_quality_and_status'] = all(not any(k.startswith('T') or k=='J' for k in r) for r in data['rows'])
    checks['composite_remains_undefined'] = data['J_DW'] is None and policy['composite']['weights'] is None
    checks['main_remains_unexecutable'] = policy['main']['executable'] is False and policy['main']['runs'] == []
    checks['diff_whitespace_valid'] = subprocess.run(['git','diff','--check'],cwd=ROOT,capture_output=True).returncode == 0
    tests = {}
    for name in ('UNIT_VALIDATION.xml','REGRESSION_VALIDATION.xml'):
        path = AUDIT/name
        if not path.exists():
            tests[name] = {'status':'MISSING'}
            checks['tests:'+name] = False
            continue
        tree = ET.parse(path)
        suites = [e for e in tree.iter() if e.tag=='testsuite']
        counts = {k:sum(int(s.get(k,0)) for s in suites) for k in ('tests','failures','errors','skipped')}
        tests[name] = counts
        if name == 'REGRESSION_VALIDATION.xml' and (counts['failures'] or counts['errors']):
            followup = AUDIT/'REGRESSION_FOLLOWUP.xml'
            failed = {(c.get('classname'),c.get('name')) for c in tree.iter('testcase')
                      if c.find('failure') is not None or c.find('error') is not None}
            passing = set()
            followup_clean = False
            if followup.exists():
                followtree = ET.parse(followup)
                passing = {(c.get('classname'),c.get('name')) for c in followtree.iter('testcase')
                           if c.find('failure') is None and c.find('error') is None and c.find('skipped') is None}
                followup_clean = all(c.find('failure') is None and c.find('error') is None for c in followtree.iter('testcase'))
            unresolved = sorted(failed-passing)
            tests[name]['initial_failures'] = sorted(failed)
            tests[name]['unresolved_after_followup'] = unresolved
            tests[name]['followup_file'] = 'REGRESSION_FOLLOWUP.xml'
            checks['tests:'+name] = bool(counts['tests']) and followup_clean and not unresolved
        else:
            checks['tests:'+name] = counts['tests'] > 0 and counts['failures'] == counts['errors'] == 0
    result = {'policy_id':policy['policy_id'], 'policy_date':'2026-11-17','audit_completed_date':'2026-11-18',
              'checks':checks,'passed':sum(checks.values()),'total':len(checks),
              'protected_files':len(protected),'authorized_changed_protected_files':changed,
              'unexpected_changed_protected_files':unexpected,'broken_current_links':links,
              'stale_rq_in_current_files':stale,'tests':tests,
              'new_experiments_executed':False,'new_demand_or_OD_generated':False,
              'README_authority':'explicit user response: READMEも更新する',
              'limits':['historical documents, snapshots and old source APIs retain timing for reproduction',
                        'DOCX package and native text checked; visual rendering unavailable in this environment',
                        'composite definition and formal experimental design remain HOLD']}
    if args.write:
        def save(name,value):
            (AUDIT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
        save('AUDIT.json',result)
        save('PRESERVATION_AFTER.json',{'checked':len(protected),'authorized_changes':changed,'unexpected_changes':unexpected})
        paths = read(AUDIT/'TRACKED_SCOPE.json')
        current = {str(p.relative_to(ROOT)) for p in active} | {
            'configs/toc_delivery/study.json','configs/toc_delivery/dw_policy_20261117_v1.json',
            'src/kmd_toc/contracts.py','src/kmd_toc/dw.py','scripts/analyze_dw.py',
            'scripts/audit_dw_policy.py','tests/test_dw_policy.py','tests/test_toc_contracts.py',
            'research_plan_toc_two_objectives_20261117.docx'}
        entries = []
        for name in sorted(set(paths)|current):
            if name in current:
                role = 'current_DW_policy_contract_or_analysis'
            elif name in {'scripts/'+n for n in GUARDED}:
                role = 'guarded_historical_entrypoint'
            elif name.startswith(('output/','results/','review_outputs/','06_outputs/','legacy/','investigations/')):
                role = 'historical_results_or_evidence_preserved'
            elif name.startswith(('03_data/','data/')):
                role = 'input_data_preserved'
            elif name.startswith('docs/research/') and '/' not in name[len('docs/research/'):]:
                role = 'historical_report_or_previous_study_preserved'
            elif name.startswith(('docs/','configs/')) or name.endswith(('.docx','.pptx','.pdf')):
                role = 'dated_or_prior_specification_preserved_current_policy_overrides'
            else:
                role = 'shared_implementation_or_legacy_code_not_a_current_analysis_entrypoint'
            entries.append({'path':name,'role':role})
        save('ARTIFACT_SCOPE.json',{'meaning':'classification of tracked artifacts plus current new entrypoints; not a claim to rerun every historical study',
                                   'entries':entries})
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 0 if all(checks.values()) else 1


if __name__ == '__main__':
    sys.exit(main())
