"""保存済みの検証結果から日本語の計算基盤説明を生成する。科学計算は行わない。"""
from pathlib import Path
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[3]
OUTPUTS = ROOT / 'reproducibility/outputs/traffic_simulation'
PREFLIGHT = OUTPUTS / 'r24_first_meaningful_multi_vehicle_preflight/20260927_v1'
STATE = OUTPUTS / 'r24_meaningful_multi_vehicle_state/20260928_v3'
SAMPLING = OUTPUTS / 'r24_meaningful_multi_vehicle_finite_shot/20260928_v1'
SOURCES = {}


def record(path):
    SOURCES[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    record(path)
    return json.loads(path.read_text())


instance = read(PREFLIGHT / 'SELECTED_INSTANCE.json')
candidate = read(PREFLIGHT / 'SELECTED_MULTI_VEHICLE_CANDIDATE.json')
audit = read(STATE / 'NUMERICAL_EQUIVALENCE_V2.json')['audit']
state_time = read(STATE / 'RUNTIME_POLICY_V2_ACCOUNTING.json')['accounting']
state_stop = read(STATE / 'STOP.json')
sampling_time = read(SAMPLING / 'RUNTIME_POLICY_V2_ACCOUNTING.json')['accounting']
sampling_stop = read(SAMPLING / 'STOP.json')
diagnostics = read(SAMPLING / 'FINITE_SHOT_DIAGNOSTICS.json')
dense = read(SAMPLING / 'DENSE_SAMPLING_RESULT.json')
mps = read(SAMPLING / 'MPS_SAMPLING_RESULT.json')
for path in (STATE / 'STATE_DECISION.json', SAMPLING / 'FINITE_SHOT_DECISION.json',
             SAMPLING / 'MEANINGFUL_MULTI_VEHICLE_OVERALL_DECISION.json'):
    assert read(path)['status'] == 'PASS'

values = {
    'depot_id': instance['depot']['depot_id'],
    'vehicle_count': candidate['M'], 'vehicle_capacity': candidate['Q'],
    'total_demand': candidate['D'], 'formulation_id': candidate['formulation_id'],
    'depot_opening': instance['depot']['opening_time'],
    'depot_closing': instance['depot']['closing_time'],
    'customers_table': '\n'.join(
        f"| 顧客{index} | `{customer['customer_id']}` | {customer['demand']} | "
        f"[{customer['earliest_service_time']}, {customer['latest_service_time']}] | "
        f"{customer['service_duration']} |"
        for index, customer in enumerate(instance['customers'], 1)
    ),
    'dense_normalization': format(audit['normalization_errors'][0], '.16g'),
    'mps_normalization': format(audit['normalization_errors'][1], '.16g'),
    'tvd': format(audit['tvd'], '.16g'),
    'event_difference': format(max(audit['event_differences'].values()), '.16g'),
    'expectation_difference': format(audit['normalized_qubo_expectation_difference'], '.16g'),
    'dense_state_seconds': state_time['dense_full_call_seconds'],
    'mps_state_seconds': state_time['mps_full_call_seconds'],
    'state_total_seconds': state_stop['total_task_seconds'],
    'dense_requested': dense['requested_shots'], 'dense_returned': dense['returned_shots'],
    'mps_requested': mps['requested_shots'], 'mps_returned': mps['returned_shots'],
    'dense_counts': sum(dense['counts'].values()), 'mps_counts': sum(mps['counts'].values()),
    'dense_feasible': diagnostics['feasible']['dense'],
    'mps_feasible': diagnostics['feasible']['mps'],
    'dense_optimal': diagnostics['optimal']['dense'],
    'mps_optimal': diagnostics['optimal']['mps'],
    'dense_sampling_seconds': sampling_time['dense_full_call_seconds'],
    'mps_sampling_seconds': sampling_time['mps_full_call_seconds'],
    'histogram_tvd': diagnostics['histogram_tvd'],
    'sampling_total_seconds': sampling_stop['total_task_seconds'],
}
template = Path(__file__).with_name('summary_ja.md.in')
record(template)
markdown = template.read_text().format_map(values)
for reference in re.findall(r'\]\(([^)]+)\)', markdown):
    if reference.startswith(('outputs/', '../CURRENT_EXECUTION.md')):
        record((ROOT / 'reproducibility' / reference).resolve())
(ROOT / 'reproducibility/COMPUTATION_PLATFORM_SUMMARY.md').write_text(markdown)
Path(__file__).with_name('SUMMARY_SOURCE_HASHES.json').write_text(json.dumps(SOURCES, indent=2) + '\n')
