"""Finalize findings, preservation checks, and the audit-only artifact index."""
import csv
import hashlib
import json
import subprocess
from pathlib import Path

OUT = Path(__file__).resolve().parent
REPO = OUT.parents[2]
FINDINGS = [
    ('S09-01', 'High', 'D', 'src/kmd_toc/pipeline/hybrid.py', 151, 157,
     'Effective shots/p/round settings are literals, not injected from the JSON.',
     'Editing final_shots in the registered JSON alone does not alter executed sampling.',
     'Pass effective settings explicitly; record executed settings and hashes.',
     'Test two N values and check per-call count totals and unchanged frozen parameters.'),
    ('S09-02', 'High', 'D', 'src/kmd_toc/column_generation/aoa.py', 202, 279,
     'VALID and improving_shots include partial routes; true day-column resources are absent.',
     'The 97 negative-proxy shots are not 97 improvements to the full plan.',
     'Separate raw/partial/full/new/day-feasible/true-RC/selected events.',
     'Independently decode counts and compare true day-master reduced costs at a fixed dual.'),
    ('S09-03', 'High', 'D', 'src/kmd_toc/pipeline/hybrid.py', 149, 162,
     'Finite fixed fragments have no shorter route than their CW parent in this S1.',
     'More shots cannot improve the mathematical best D in the declared 102-route domain.',
     'Treat as structural scope limitation; register any expanded domain as a separate version.',
     'Independent full finite-domain costs and positive-control instances before sensitivity runs.'),
    ('S09-04', 'High', 'D', 'src/kmd_toc/column_generation/aoa.py', 226, 265,
     'Final measurement seed is derived after training RNG consumption; no independent quantum_seed API.',
     'Same-seed run repetitions are debugging repeats, not independent sampling trials.',
     'Separate initialization/training/final streams; persist final seed, role, and repetition.',
     'Frozen-parameter debug replay and distinct SeedSequence child streams for all planned cells.'),
    ('S09-05', 'Medium', 'D', 'src/kmd_toc/column_generation/aoa.py', 281, 305,
     'measured_shots reports final counts only; no explicit total training/final shot ledger.',
     'Using 139264 as total cost omits 1084000 training measurement-equivalent draws.',
     'Record per-evaluation stage/shots/seed/parameter hash and total each stage independently.',
     'Compare nfev times train_shots, saved evaluation length, and final count sums.'),
    ('S09-06', 'Medium', 'D/B/C', 'src/kmd_toc/pipeline/execution.py', 35, 52,
     'The final sample timer bundles preparation and decoding; extra second validation is outside saved T.',
     'Pure sampling cost and a complete final-check boundary cannot be inferred from one aggregate timer.',
     'Add exclusive stage clocks and explicitly version the same T end point for all methods.',
     'Clock-boundary checks and full pipeline wall-time accounting including classical completion.'),
    ('S09-07', 'Medium', 'D', 'src/kmd_toc/pipeline/hybrid.py', 169, 175,
     'Larger sampled route pools increase classical catalogue/LP/IP work under finite time budgets.',
     'More shots need not improve D/W or preserve finite-budget success probability.',
     'Record and retain baseline incumbent and failures; compare matched budgets.',
     'Per-condition candidate/column counts, full wall time, and all failures with no seed replacement.'),
    ('S09-08', 'Low', 'reproduction', 'docs/research/REPRODUCE.md', 15, 15,
     'The existing environment required PYTHONPATH=src for the documented test invocation.',
     'Initial test collection failed although dependencies were installed.',
     'Document/import the repository source path explicitly in future reproducibility instructions.',
     'Fresh shell command with PYTHONPATH=src; the audit rerun passed 21 selected tests.'),
]
headers = ['id', 'severity', 'method', 'file', 'line_start', 'line_end', 'evidence', 'impact', 'required_change_NOT_executed', 'verification_after_change']
with (OUT / 'FINDINGS.csv').open('w', newline='') as f:
    w = csv.writer(f); w.writerow(headers); w.writerows(FINDINGS)
(OUT / 'FINDINGS.json').write_text(json.dumps([dict(zip(headers, row)) for row in FINDINGS], indent=2) + '\n')

summary = json.loads((OUT / 'AUDIT_SUMMARY.json').read_text())
validation = json.loads((OUT / 'VALIDATION.json').read_text())
plan = json.loads((OUT / 'SHOT_EXPERIMENT_PLAN.json').read_text())
plan_validation = json.loads((OUT / 'PLAN_VALIDATION.json').read_text())
compatibility = json.loads((OUT / 'SEED_128BIT_COMPATIBILITY.json').read_text())
baseline = json.loads((OUT / 'PRESERVATION_BEFORE.json').read_text())
docs = [REPO / 'docs/research/D_SHOTS_AUDIT.md', REPO / 'docs/research/D_SHOTS_VALIDATION_PLAN.md']
changes = [rel for rel, expected in baseline['files'].items()
           if not (REPO / rel).exists() or hashlib.sha256((REPO / rel).read_bytes()).hexdigest() != expected]
status = subprocess.check_output(['git', 'status', '--short', '--untracked-files=no'], cwd=REPO, text=True)
checks = {
    'audit checks passed': validation['checks'] == validation['passed'] == 4126,
    'plan checks passed': plan_validation['checks'] == plan_validation['passed'] == 8,
    'all 34 counts exact replay': summary['all_saved_counts_reproduced'],
    'gold total shots': summary['S1_main']['total_measurement_equivalent_draws'] == 1223264,
    'macro total/new/pool': summary['exact_domain_count'] == 102 and summary['observed_complete_macro_routes'] == 70 and summary['S1_main']['new_quantum_routes'] == 58 and summary['S1_main']['union_route_pool'] == 75,
    'no quantum new route in final plan': summary['S1_main']['selected_new_AOA_routes'] == 0,
    'no shorter macro in exact finite domain': summary['shorter_parent_macro_routes_in_exact_domain'] == 0,
    'all current shortest routes are original count': summary['equal_parent_macro_routes_in_exact_domain'] == 17,
    'all frozen files protected': sum('/frozen_demand/v1/' in x for x in baseline['files']) == 8,
    'protected files unchanged': not changes,
    'tracked modifications not changed': status == baseline['tracked_git_status'],
    'no production N fabricated': plan['production_final_shots'] is None,
    'no sensitivity experiment performed': summary['new_D_W_T_sensitivity_experiment_executed'] is False,
    '128-bit-class seed supported by actual installed Qiskit': compatibility['same_seed_reproduces'] and compatibility['count_total'] == 32 and compatibility['seed_bits_actual'] > 64,
    '21 selected tests passed': '21 passed' in (OUT / 'PYTEST.log').read_text(),
    'report and plan explicitly HOLD': all('HOLD' in p.read_text() for p in docs),
    'report contains executed totals': all(x in docs[0].read_text() for x in ['1,223,264', '1,084,000', '139,264', '4,126', '58']),
    'plan total matches documented budget': f"{plan['pilot_total_final_shots']:,}" in docs[1].read_text(),
}
result = {'checks': len(checks), 'passed': sum(checks.values()), 'details': checks,
          'existing_protected_files': len(baseline['files']), 'changed_existing_files': changes,
          'existing_code_or_settings_changed': False, 'production_shots': None,
          'full_or_sensitivity_experiment_executed': False, 'small_kernel_checks_executed': True,
          'new_report_documents': 2}
(OUT / 'FINAL_VALIDATION.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
assert all(checks.values()), result
artifacts = docs + [p for p in OUT.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name != 'ARTIFACT_INDEX.json']
index = {str(p.relative_to(REPO)): {'sha256': hashlib.sha256(p.read_bytes()).hexdigest(), 'bytes': p.stat().st_size} for p in artifacts}
(OUT / 'ARTIFACT_INDEX.json').write_text(json.dumps({'files': index, 'new_audit_files_including_index': len(index) + 1,
                                                    'existing_files_changed': 0}, indent=2) + '\n')
print(json.dumps({k: v for k, v in result.items() if k != 'details'}, indent=2))
print('new audit files including index', len(index) + 1)
