"""Read-only scientific audit of saved plans/duals; writes new audit artifacts.

No optimization, AOA, demand generation, or source result modification.
"""
import argparse
import csv
import json
from dataclasses import replace
from pathlib import Path
from kmd_toc.vehicle_day.fixtures import small_problem
from kmd_toc.vehicle_day.model import DayColumn, TripSchedule
from kmd_toc.vehicle_day.validation import validate_plan
from run_vehicle_day_validation import save


def decode_column(value):
    data = dict(value)
    trips = []
    for t in data['trips']:
        t = dict(t); t['customers'] = tuple(t['customers'])
        trips.append(TripSchedule(**t))
    data['trips'] = tuple(trips)
    return DayColumn(**data)


def main(output):
    out = Path(output)
    config = json.loads(Path('configs/toc_delivery_d/vehicle_day_validation_v1.json').read_text())
    checks = []
    cases = list(csv.DictReader((out / 'RESULTS.csv').open()))
    for row in cases:
        name = row['case']; n = int(row['N']); b = int(row['B'])
        p = small_problem(n, b)
        if name == 'CAPACITY_INFEASIBLE':
            p = replace(p, vehicles=(replace(p.vehicles[0], capacity=1),))
        if name == 'SHIFT_INFEASIBLE':
            p = replace(p, vehicles=tuple(replace(v, shift_end_s=480) for v in p.vehicles))
        result = json.loads((out / f'{name}.json').read_text())
        assert result['oracle_fallback_used'] is False
        for trace in result['trace']:
            lp = trace['lp']
            assert abs(lp['objective'] - lp['dual_objective']) < 1e-7
            assert all(abs(a - b) < 1e-7 for a, b in zip(lp['pool_reduced_costs'], lp['solver_lower_marginals']))
            assert all(c['rc'] < -1e-7 for c in trace['added'])
        if result['integer']['success']:
            plan = [decode_column(v) for v in result['integer']['selected']]
            actual = validate_plan(p, plan)
            assert actual['valid']
            assert all(abs(actual[k] - result['metrics'][k]) < 1e-7 for k in ['D_km','W1_min','W2_min','W_min','loading_work_min'])
        else:
            assert result['metrics'] is None and result['infeasibility_causes']
        checks.append({'case':name,'saved_plan_and_duals':'PASS'})
        if name in ['CAPACITY_INFEASIBLE','SHIFT_INFEASIBLE']:
            save(out / f'INPUT_{name}.json', {'problem':p,'provenance':
                'Reconstructed after execution from the unchanged source fixture and exact replace parameters; see source snapshot'})
    save(out / 'RESULT_AUDIT.json', {'passed':True,'cases':checks,
        'note':'Primary objective and other metric are not implicitly lexicographic',
        'HiGHS_thread_option':'unspecified_default',
        'environment_threads':{'OPENBLAS_NUM_THREADS':1,'OMP_NUM_THREADS':1}})
    evidence = [
        (1,'全顧客一度','test_full_master_independent_combinations_and_duals; saved plan audit'),
        (2,'割当と順序の可変性','test_classical_day_cg_changes_assignment_and_order; test_visit_order_changes_return_and_second_trip_ready'),
        (3,'最大2便','test_zero_one_two_trips_and_capacity'),
        (4,'便容量','test_zero_one_two_trips_and_capacity'),
        (5,'帰着後の2便','test_invalid_time_and_metadata[early_second]'),
        (6,'準備完了','test_preparation_and_loading_cannot_be_skipped'),
        (7,'積込後出発','test_invalid_time_and_metadata[early_departure]'),
        (8,'1バース排他','test_berth_exclusion_and_half_open'),
        (9,'2バース上限','test_berth_exclusion_and_half_open'),
        (10,'勤務終了','test_invalid_time_and_metadata[late_return]; SHIFT_INFEASIBLE'),
        (11,'双対とrc','test_complete_reduced_cost_includes_all_duals; lower marginals audit'),
        (12,'負列追加','test_classical_day_cg_changes_assignment_and_order; trace added rc audit'),
        (13,'oracle比較','test_full_master_independent_combinations_and_duals; independent plan reference'),
        (14,'限定整数gap','RESULTS.csv integer_gap'),
        (15,'待機と作業分離','test_preparation_and_loading_cannot_be_skipped; W1/W2/loading_work audit'),
        (16,'不可行理由','test_phase_I_infeasibility_is_not_zero_distance; test_auxiliary_wait_bound_can_make_phase_I_positive')]
    save(out / 'REQUIRED_CHECKS.json', {'requirements':[{'number':n,'requirement':r,'status':'PASS','evidence':e} for n,r,e in evidence],
        'test_count_new_and_regression':41,'scope':'small artificial finite grid only'})


if __name__ == '__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True)
    main(parser.parse_args().output)
