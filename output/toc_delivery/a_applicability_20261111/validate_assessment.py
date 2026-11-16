"""Independent arithmetic, source assertions and non-comparability safeguards."""
from pathlib import Path
from decimal import Decimal
import contextlib
import hashlib
import importlib.util
import io
import json
import re

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


def main():
    data = json.loads((ROOT/'docs/research/toc_delivery_a/A_APPLICABILITY_ASSESSMENT.json').read_text())
    reference = json.loads((ROOT/'docs/research/toc_delivery_a/A_REFERENCE_VALUES.json').read_text())
    report = (ROOT/'docs/research/toc_delivery_a/A_APPLICABILITY_ASSESSMENT.md').read_text()
    checks = []
    def check(name, predicate):
        checks.append({'check': name, 'passed': bool(predicate)})
        if not predicate:
            raise AssertionError(name)
    check('twelve_candidates', len(data['candidates']) == 12)
    check('thirty_six_metric_assessments', sum(len(c['metrics']) for c in data['candidates']) == 36)
    check('declared_weights', data['weights'] == dict(zip(data['axes'], [30,25,20,15,10])))
    check('weights_sum_to_100', sum(data['weights'].values()) == 100)
    candidates = {c['evidence_id']: c for c in data['candidates']}
    for c in data['candidates']:
        for metric, rec in c['metrics'].items():
            name = c['evidence_id'] + '_' + metric
            check(name+'_levels_0_to_4', all(type(x) is int and 0 <= x <= 4 for x in rec['levels'].values()))
            # Decimal calculation is independent of the float generation/display path.
            score = sum(Decimal(data['weights'][axis]) * Decimal(level) / 4 for axis,level in rec['levels'].items())
            check(name+'_score_recalculated', score == Decimal(str(rec['score_100'])))
            check(name+'_all_reasons_present', all(rec['reasons'].get(a) for a in data['axes']))
            check(name+'_same_condition_not_claimed', not rec['common_definition_matched'] and not rec['scale_transfer_validated'] and not rec['can_populate_S1_S2_S3'] and rec['same_condition_status'] == 'HOLD')
            check(name+'_weight_sensitivity_contains_score', rec['weight_sensitivity_range'][0] <= float(score) <= rec['weight_sensitivity_range'][1])
            if rec['availability'] == 'not_obtained_in_reviewed_material':
                check(name+'_missing_is_null_not_zero', rec['value'] is None and score == 0 and rec['external_status'] == 'HOLD')
            if rec['external_role'] == 'primary_external':
                check(name+'_primary_absolute_and_metric_class', rec['absolute_observed_quantity'] and rec['minimum_metric_class_match'] and rec['operator_origin_supported'])
            if rec['external_role'] == 'development_only':
                check(name+'_potential_not_observed_value', rec['value'] is None and rec['external_status'] == 'HOLD')
        table_row = '|'+c['evidence_id']+' '+c['name']+'|'+'|'.join(c['metrics'][m]['score_display'] for m in ('D','T','W'))+'|'
        check(c['evidence_id']+'_markdown_table_matches_json', table_row in report)
    expected = {('E05','D'):Decimal('53.75'),('E07','T'):Decimal('47.5'),('E11','W'):Decimal('40'),('E14','D'):Decimal('37.5')}
    for (eid, metric), value in expected.items():
        check(eid+'_'+metric+'_independent_expected_score', Decimal(str(candidates[eid]['metrics'][metric]['score_100'])) == value)
    for name, record in data['source_artifacts'].items():
        check('artifact_hash_'+name, hashlib.sha256((ROOT/name).read_bytes()).hexdigest() == record['sha256'])
    # Keep the previous published-value checks, redirecting only their output to this new audit.
    spec = importlib.util.spec_from_file_location('previous_reference_validation', ROOT/'output/toc_delivery/a_baseline_20261111/validate_reference.py')
    previous = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(previous)
    previous.HERE = HERE
    with contextlib.redirect_stdout(io.StringIO()):
        previous.main()
    old_checks = json.loads((HERE/'REFERENCE_VALIDATION.json').read_text())
    check('existing_reference_validation_passed', old_checks['failed'] == 0)
    auxiliary = {r['id']:r for r in reference['auxiliary_references']}
    w = auxiliary['general_freight_waiting_context']
    check('general_waiting_60_separate_from_common_W', w['value'] == 60 and w['reported_n'] == 1032 and not w['common_W_boundary_matched'] and reference['missing_metrics']['W_min']['value'] is None)
    survey = (HERE/'sources/MLIT_SURVEY_2026.txt').read_text()
    check('survey_year_and_report_date', '2025年度' in survey and '令和８年７月 10 日' in survey)
    check('survey_components_and_total', '1:00' in survey and '0:48' in survey and '0:14' in survey and 60+48+14 == 122)
    facility = (HERE/'sources/MLIT_FACILITY_DX.txt').read_text()
    check('kawanishi_relative_only', '荷待ち時間30%軽減' in facility and not candidates['E12']['metrics']['W']['absolute_observed_quantity'])
    dx = (HERE/'sources/MLIT_OBJECTIVE_DX_2025.txt').read_text()
    check('receipt_70_and_rest_not_common_W', '平均70分' in dx and '分割休息' in dx and not candidates['E13']['metrics']['W']['minimum_metric_class_match'])
    schema = (HERE/'sources/amazon_schema.txt').read_text()
    check('amazon_real_order_time_not_distance_matrix', 'actual_sequences.json' in schema and 'travel_times.json' in schema and 'specified in seconds' in schema)
    check('amazon_timing_examples_not_T', 'model_apply_time.json' in schema and '3920' in schema and candidates['E14']['metrics']['T']['value'] is None)
    card = (HERE/'sources/LADE_CARD.md').read_text()
    paper = (HERE/'sources/LADE_PAPER.html').read_text()
    check('lade_license_disagreement_retained', 'apache-2.0' in card and 'CC BY-NC 4.0' in paper and candidates['E15']['metrics']['D']['data_reuse_cleared_for_this_scope'] is False)
    check('lade_projected_coordinate_example_not_degrees', '3.953700e+06' in card and '3.053400e+06' in card)
    quality = json.loads((HERE/'DATA_QUALITY_CHECKS.json').read_text())
    check('nine_actual_distance_inputs', len(quality['delivering_matrices']) == 9)
    for row in quality['delivering_matrices']:
        check('delivering_day_'+str(row['day'])+'_matrix_integrity', row['matrix_cells'] == row['nodes_including_depot']**2 and row['orders_equal_matrix_customers'] and row['order_count'] == row['unique_order_count'] and row['missing_or_nonfinite'] == row['negative'] == row['nonzero_diagonal'] == 0 and row['asymmetric_directed_pairs'] > 0)
    check('orders_observed_range_63_to_84', min(r['order_count'] for r in quality['delivering_matrices']) == 63 and max(r['order_count'] for r in quality['delivering_matrices']) == 84)
    check('delivering_OD_not_route_actual', quality['delivering_no_route_sequence_file'] and candidates['E16']['metrics']['D']['value'] is None)
    check('urbane_test_and_absent_loading_fields', quality['urbane_raw']['data_rows_including_tests'] == 1421 and quality['urbane_raw']['description_counts']['TEST'] == 1 and not quality['urbane_raw']['has_dedicated_vehicle_trip_or_loading_ready_columns'])
    prefix = quality['queue_prefix']
    check('queue_sample_explicit_partial_and_duplicates', prefix['bytes'] == 65536 and prefix['complete_rows'] == 247 and prefix['observed_unique_plan_ids'] == 129)
    check('queue_time_arithmetic_not_ready_mapping', abs(prefix['declared_queuing_time_first_row'] - prefix['calling_minus_queue_start_min_first_row']) < 1e-8 and prefix['entry_minus_queue_start_min_first_row'] == 4.15 and candidates['E17']['metrics']['W']['operator_origin_supported'] is False)
    for record in json.loads((HERE/'DATA_DOWNLOAD_LOG.json').read_text()):
        raw = (HERE/'sources'/record['file']).read_bytes()
        check('dataset_hash_'+record['file'], hashlib.sha256(raw).hexdigest() == record['sha256'])
    for filename in ('DELIVERING_ZENODO.json','URBANE_ZENODO.json'):
        for file in json.loads((HERE/'sources'/filename).read_text())['files']:
            raw = (HERE/'sources'/file['key']).read_bytes()
            check('publisher_md5_'+file['key'], 'md5:'+hashlib.md5(raw).hexdigest() == file['checksum'])
    check('unchanged_time_assumptions', data['unchanged_conditions'] == {'loading_s':1800,'customer_service_s':120,'return_preparation_s':0})
    check('no_joint_observation', data['joint_observation'] is False and reference['joint_observation'] is False)
    out = {'checks':checks,'passed':len(checks),'failed':0,'prior_reference_checks_passed':old_checks['passed'],
           'interpretation':'source/structure/arithmetic audit; not raw operational D/T/W measurement, scale proof or algorithm experiment'}
    (HERE/'VALIDATION_RESULTS.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    print(f"{len(checks)} assessment checks passed; {old_checks['passed']} reference checks passed; no optimization")


if __name__ == '__main__':
    main()
