"""Pure prospective rules. No quantum/optimizer imports or execution."""
import collections
import hashlib
import math

PROTOCOL = {
    'encoding': 'C_POSITION_PUBO_NO_ANCILLA', 'p': 1, 'logical_qubits': 16,
    'initial_state': 'H_ON_ALL_16_QUBITS', 'mixer': 'X_MIXER',
    'optimizer': 'COBYLA', 'initial_angles': [0.1, 0.1],
    'max_objective_evaluations': 100, 'shots_per_evaluation': 2048, 'final_shots': 4096,
    'gamma_domain': [0.0, 2*math.pi], 'beta_domain': [0.0, math.pi],
    'cobyla_options': {'maxiter': 100, 'rhobeg': 0.5, 'tol': 1e-3, 'catol': 1e-6},
    'constraints': ['gamma >= 0', '2*pi - gamma >= 0', 'beta >= 0', 'pi - beta >= 0'],
    'cost': 'MEAN_UNNORMALIZED_CANDIDATE_C_ENERGY_S_AS_IN_PILOT',
    'process_cap_bytes': 4294967296, 'raw_statevector_cap_bytes': 268435456,
    'concurrency': 1, 'wall_cap_seconds': 3600,
    'python': '/opt/miniconda/envs/qgpu/bin/python',
    'versions': {'qiskit': '2.1.1', 'numpy': '2.3.1', 'scipy': '1.16.0'},
    'thread_environment': {k: '1' for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']},
    'incumbent_rule': 'IN_DOMAIN_MAX_FEASIBLE_COUNT_THEN_MIN_MEAN_ENERGY_THEN_EARLIEST_INDEX',
    'no_feasible_fallback': 'IN_DOMAIN_MIN_MEAN_ENERGY_THEN_EARLIEST_INDEX',
    'optimal_count_used_for_selection': False,
    'final_route_authority': 'INDEPENDENT_FINAL_4096_SHOTS_ONLY',
    'automatic_retry': False, 'FULL_R1_RUN_ALLOWED': False,
}
STRATA = ['LOW_RESOURCE', 'MEDIAN_RESOURCE', 'HIGH_RESOURCE']
GATE = {
    'planned_instances': 9, 'seeds_per_instance': 3, 'planned_runs': 27,
    'minimum_successful_runs': 14, 'stable_instance_minimum_successful_seeds': 2,
    'minimum_stable_instances': 5, 'minimum_stable_instances_per_stratum': 1,
    'resource_cap_bytes': 4294967296, 'final_routes_independent_validation_fraction': 1.0,
    'A': 'All runs within resource/time caps; no integrity or hash mismatch.',
    'B': 'Every final route counted feasible independently validates.',
    'C': 'At least 14/27 runs have >=1 independently validated final feasible sample.',
    'D': 'At least 5/9 instances have acquisition on >=2/3 seeds.',
    'E': 'At least one stable instance in each resource stratum.',
    'F': 'Exact frozen rule/parameters across all 27; no rescue or deviations.',
    'rationale': '14/27=51.85% operational minimum approximately matching R0 40/78=51.28%; not a statistical assertion of equal acquisition probabilities.',
    'failure_precedence': ['FAILED for A/B/F integrity, validation or protocol deviation', 'INCOMPLETE_INFRASTRUCTURE for required infrastructure failure', 'INCOMPLETE_DATA for other missing runs', 'NOT_QUALIFIED_STABILITY for C/D/E failure', 'QUALIFIED only when all A-F pass'],
    'zero_results_status': 'PLANNED_NOT_EXECUTED',
    'FULL_R1_RUN_ALLOWED': False,
    'full_run_review': 'Qualification only permits a separate authorization review; never automatic full-run authorization.',
}

def seed_for(base_seed, pid, tag):
    return int(hashlib.sha256(f'{base_seed}|{pid}|{tag}'.encode()).hexdigest()[:8], 16)

def in_domain(gamma, beta):
    return 0.0 <= gamma <= 2*math.pi and 0.0 <= beta <= math.pi

def select_incumbent(evaluations):
    """Operational selection deliberately never reads optimal_count."""
    eligible = [r for r in evaluations if in_domain(r['gamma'], r['beta']) and math.isfinite(r['mean_energy_s'])]
    if not eligible:
        raise ValueError('NO_IN_DOMAIN_FINITE_EVALUATION')
    feasible = [r for r in eligible if r['feasible_count'] > 0]
    if feasible:
        return min(feasible, key=lambda r: (-r['feasible_count'], r['mean_energy_s'], r['evaluation_index'])), False
    return min(eligible, key=lambda r: (r['mean_energy_s'], r['evaluation_index'])), True

def evaluate_gates(planned, outcomes):
    """Outcomes keyed by exact run_id, already independently checked by summarizer."""
    known = {r['run_id'] for r in planned}
    if set(outcomes)-known:
        return {'status': 'FAILED', 'reason': 'UNPLANNED_RUNS', 'FULL_R1_RUN_ALLOWED': False}
    missing = sorted(known-set(outcomes))
    failed = [k for k,r in outcomes.items() if r['status'] in ['INTEGRITY_FAILURE','VALIDATION_FAILURE','PROTOCOL_FAILURE','RESOURCE_FAILURE']]
    infra = [k for k,r in outcomes.items() if r['status']=='INFRASTRUCTURE_FAILURE']
    passed = {k:r for k,r in outcomes.items() if r['status']=='PASS'}
    per_pid = collections.Counter()
    for p in planned:
        if p['run_id'] in passed and passed[p['run_id']]['final_feasible_count']>0:
            per_pid[p['physical_instance_id']] += 1
    stable = sorted(pid for pid,n in per_pid.items() if n>=2)
    strata = {s:sorted({p['physical_instance_id'] for p in planned if p['stratum']==s and p['physical_instance_id'] in stable}) for s in STRATA}
    acquired = sum(per_pid.values())
    gates = {'A': not failed and len(passed)==27, 'B': not failed and len(passed)==27,
             'C': acquired>=14, 'D': len(stable)>=5, 'E': all(strata[s] for s in STRATA),
             'F': not failed and len(passed)==27}
    if failed: status='FAILED'
    elif infra: status='INCOMPLETE_INFRASTRUCTURE'
    elif not outcomes: status='PLANNED_NOT_EXECUTED'
    elif missing or len(passed)!=27: status='INCOMPLETE_DATA'
    elif all(gates.values()): status='QUALIFIED'
    else: status='NOT_QUALIFIED_STABILITY'
    return {'status':status,'gates':gates,'successful_final_runs':acquired,'stable_instances':stable,
            'stable_by_stratum':strata,'missing_runs':missing,'failed_runs':failed,'infrastructure_failures':infra,
            'completed_runs':len(passed),'FULL_R1_RUN_ALLOWED':False}
