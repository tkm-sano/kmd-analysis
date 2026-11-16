"""Create proposed seed manifests and the unexecuted shots validation plan."""
import csv
import hashlib
import json
from pathlib import Path
import numpy as np

OUT = Path(__file__).resolve().parent
NS = [1024, 4096, 8192, 10000, 16384, 32768]
bank_path = OUT / 'S1_FROZEN_PARAMETER_BANK.json'
bank = json.loads(bank_path.read_text())
root_entropy = 202611130900
rows = []
for condition_id, n in enumerate(NS):
    for repetition in range(30):
        for kernel_id, kernel in enumerate(bank):
            key = (0, condition_id, repetition, kernel_id, 2)
            child = np.random.SeedSequence(root_entropy, spawn_key=key)
            words = child.generate_state(4, dtype=np.uint32)
            integer = sum(int(x) << (32 * i) for i, x in enumerate(words))
            rows.append({
                'series_id': 'F', 'scenario_id': 'S1', 'instance_id': 'frozen_S1_parameter_bank_diagnostic',
                'method': 'D_fixed_parameter_sampling_only', 'condition_id': f'Q{condition_id + 1}',
                'final_shots_per_kernel': n, 'repetition_id': repetition, 'kernel_id': kernel['call'],
                'demand_seed': None, 'demand_seed_reason': 'frozen deterministic SHA256 selection; no generation here',
                'training_solver_seed_provenance': kernel['config']['solver_seed'],
                'quantum_seed_hex': f'{integer:032x}', 'seed_sequence_spawn_key': ':'.join(map(str, key)),
                'validation_seed': None, 'status': 'PLANNED_NOT_EXECUTED',
            })
with (OUT / 'PILOT_SEEDS.csv').open('w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
plan = {
    'version': 'D-shots-validation-plan-20261113-v1',
    'scope': 'audit plan; no large sensitivity or full delivery experiment executed',
    'production_final_shots': None,
    'production_adoption_status': 'HOLD:measurement_and_total_time_evidence_required',
    'pilot_reference_candidate_final_shots': 8192,
    'current_effective_train_shots': 1000,
    'current_effective_final_shots': 4096,
    'final_sampling_conditions': NS,
    'initial_independent_repetitions_per_condition': 30,
    'post_selection_confirmatory_repetitions_proposal': 60,
    'frozen_parameter_bank_sha256': hashlib.sha256(bank_path.read_bytes()).hexdigest(),
    'parameter_bank_kernels': len(bank),
    'pilot_sampling_calls': len(rows),
    'pilot_total_final_shots': sum(x['final_shots_per_kernel'] for x in rows),
    'pilot_additional_training_shots': 0,
    'random_generator': 'NumPy 2.3.1 SeedSequence; Qiskit 2.1.1 Statevector sampling RNG',
    'root_entropy': root_entropy,
    'seed_bits': 128,
    'seed_encoding': 'hex string; convert to Python int(seed_hex,16)',
    'seed_axes': ['series_id', 'shots_condition', 'repetition', 'kernel', 'role'],
    'all_final_sampling_streams_independent_by_design': True,
    'independence_is_mathematical_proof': False,
    'shots_conditions_use_nested_same_seed_prefixes': False,
    'primary_value_events': ['new_feasible_day_column_with_true_negative_reduced_cost_at_frozen_dual',
                             'improved_complete_plan_against_matched_classical_control'],
    'raw_partial_route_negative_proxy_cost_is_primary_value_event': False,
    'observed_or_computed_current_S1_macro_shorter_route_count': 0,
    'current_S1_distance_improvement_trial_gate': 'STOP:finite_domain_has_no_shorter_route; diagnostic_only',
    'train_shots_series_separate': True,
    'required_before_full_run': ['effective_config_injection', 'explicit_final_measurement_seed',
                                 'stage_shot_and_time_ledger', 'improvable_positive_control',
                                 'matched_classical_completion_control', 'authorization_for_experiments'],
    'no_full_delivery_experiment_authorized_by_this_plan': True,
    'all_unmeasured_D_W_and_T_by_shots': None,
    'empirical_wall_time_budget_estimate': None,
}
(OUT / 'SHOT_EXPERIMENT_PLAN.json').write_text(json.dumps(plan, ensure_ascii=False, indent=2) + '\n')
checks = {
    '6120 planned sampling calls': len(rows) == 6120,
    'all quantum seeds distinct': len({x['quantum_seed_hex'] for x in rows}) == len(rows),
    'exact planned shots total': plan['pilot_total_final_shots'] == 73913280,
    'all seed rows unexecuted': all(x['status'] == 'PLANNED_NOT_EXECUTED' for x in rows),
    'no production shots committed': plan['production_final_shots'] is None,
    'no invented shots sensitivity D W T': plan['all_unmeasured_D_W_and_T_by_shots'] is None,
    'frozen bank has 34 kernels': len(bank) == 34,
}
first = rows[0]
key = tuple(int(x) for x in first['seed_sequence_spawn_key'].split(':'))
words = np.random.SeedSequence(root_entropy, spawn_key=key).generate_state(4, dtype=np.uint32)
integer = sum(int(x) << (32 * i) for i, x in enumerate(words))
checks['seed construction reproduced'] = f'{integer:032x}' == first['quantum_seed_hex']
result = {'checks': len(checks), 'passed': sum(checks.values()), 'details': checks,
          'random_samples_drawn_by_this_script': 0}
(OUT / 'PLAN_VALIDATION.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(result, indent=2))
assert all(checks.values())
