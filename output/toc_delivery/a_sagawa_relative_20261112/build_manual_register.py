"""Record published evidence and missing manual-before values; no route solver."""
from pathlib import Path
import csv
import hashlib
import json

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DOCS = ROOT / 'docs/research/toc_delivery_a'


def main():
    manifest = json.loads((HERE / 'SOURCE_MANIFEST.json').read_text())
    sources = {r['id']: r for r in manifest}
    groups = ['担当', '代走', '新人・応援']
    records = []
    for metric, unit in [('D', 'km'), ('W', 'min'), ('T', 's')]:
        for group in groups if metric != 'W' else ['未報告']:
            records.append({
                'id': f'LOOGIA202008_{metric}_{group}',
                'metric': metric, 'driver_group': group,
                'cohort_id': 'Sagawa_Loogia_field_202008',
                'operator': '佐川急便', 'planning_method': 'manual_before_Loogia',
                'before_absolute': None, 'after_absolute': None, 'unit': unit,
                'normalized_before': None, 'normalized_after': None,
                'improvement_percent': None, 'adopted_as_A_performance': False,
                'judgment': 'HOLD', 'access_status': 'UNVERIFIED',
                'unavailable_not_proven': True,
                'reason': {
                    'D': '差分表のみ。改善前の距離・訪問順・全車両ログが未取得。',
                    'W': '検証項目に含まれず、積込ready/start/バース記録が未取得。',
                    'T': '短縮量のみ。改善前のルート組み開始/終了と共通T境界が未取得。',
                }[metric],
                'source_ids': ['OPTIMIND_RELEASE', 'OPTIMIND_CHART', 'PRTIMES_RELEASE', 'PRTIMES_CHART'],
                'locator': 'これまでの取組実績1・検証内容及び条件・検証結果',
                'urls': [sources['OPTIMIND_RELEASE']['url'], sources['OPTIMIND_CHART']['url']],
                'value_kind': 'missing_target_value',
            })

    # Transcriptions from the two displayed source images, not measured outcomes of A.
    transcription_a = {
        'source_id': 'OPTIMIND_CHART', 'method': 'visual_read_original_JPEG',
        'column_order': groups,
        'route_planning_reduction_min': [10, 15, 30],
        'delivery_operations_reduction_min': [30, 60, 60],
        'distance_reduction_km': [10, 9, 11],
        'before_after_axis_present': False, 'percent_present': False,
        'interpretation': 'positive reduction magnitudes; source labels show minus signs',
    }
    transcription_b = {
        'source_id': 'PRTIMES_CHART', 'method': 'visual_read_separate_publisher_copy',
        'column_order': ['担当', '代走', '新人・応援'],
        'route_planning_reduction_min': [10, 15, 30],
        'delivery_operations_reduction_min': [30, 60, 60],
        'distance_reduction_km': [10, 9, 11],
        'before_after_axis_present': False, 'percent_present': False,
        'interpretation': 'same original experiment; NOT independent observations',
    }
    for name, value in [('TRANSCRIPTION_OPTIMIND.json', transcription_a),
                        ('TRANSCRIPTION_PRTIMES.json', transcription_b)]:
        (HERE / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')

    data = {
        'schema_version': '1.0', 'decision_version': 'Sagawa-manual-A-20261112-v1.0',
        'checked_on': '2026-11-12',
        'A_definition': '佐川急便のLoogia導入前の人手による配送計画',
        'latest_instruction': 'manual_before_only',
        'outbound_contact_executed': False, 'nonpublic_data_acquired': False,
        'large_scale_experiment_executed': False, 'alternative_baseline_adopted': False,
        'current_A_performance': {'D_km': None, 'W_min': None, 'T_s': None},
        'A_numeric_performance_judgment': 'HOLD',
        'A_definition_judgment': 'GO', 'A_qualitative_reference_judgment': 'CONDITIONAL GO',
        'same_condition_A_to_D_judgment': 'HOLD',
        'target_conditions': {
            'id': 'AD-common-20261111-v1.1',
            'config': 'configs/toc_delivery/common_conditions_v1_1.json',
            'sha256': hashlib.sha256((ROOT / 'configs/toc_delivery/common_conditions_v1_1.json').read_bytes()).hexdigest(),
        },
        'records': records,
        'cohort': {
            'id': 'Sagawa_Loogia_field_202008', 'month': '2020-08',
            'trial_days_reported': 14, 'parcels_reported': 80,
            'unique_stops': None, 'parcels_per_day_confirmed': False,
            'vehicle_count': None, 'trip_count': None, 'berth_count': None,
            'exact_dates': None, 'region': None,
            'customer_time_windows': True,
            'paired_demand_and_vehicle_conditions_confirmed': False,
            'later_500_driver_trial_is_same_cohort': False,
            'observed_routes': None, 'planned_manual_visit_sequences': None,
            'customer_service_event_logs': None, 'loading_event_logs': None,
            'manual_planning_event_logs': None,
        },
        'nonadopted_difference_evidence': {
            'adopted_as_A_performance': False,
            'source_kind': 'published_image_label_not_before_value',
            'transcription_file': 'TRANSCRIPTION_OPTIMIND.json',
            'independent_copy_check': 'TRANSCRIPTION_PRTIMES.json',
            'D_reduction_km': [10, 9, 11],
            'T_route_reduction_min': [10, 15, 30],
            'delivery_operations_reduction_min': [30, 60, 60],
            'unknown_before_and_after': True,
            'infer_after_zero_allowed': False,
        },
        'operation_illustration': {
            'source_id': 'OPTIMIND_OPERATION_IMAGE', 'kind': 'illustration',
            'clock_in': '08:30', 'depot_departure': '09:30',
            'clock_in_to_departure_min': 60,
            'manual_T_s': None, 'manual_T_3600_s_adopted': False,
            'reason': 'clock-in/departure are not planning start/end; not identified as before-only event log',
        },
        'separate_urban_distance_observation': {
            'source_id': 'SAGAWA_DISTANCE', 'observation_date': '2025-01-10',
            'published_date': '2025-02-06', 'truck_km': 13,
            'walking_approx_km': 14, 'scope': 'one urban driver one day',
            'planning_method': 'UNVERIFIED', 'pre_Loogia_manual_confirmed': False,
            'adopted_as_A_performance': False,
            'reason': 'different 2025 cohort, after national rollout announcement, method unknown',
        },
        'separate_interdepot_case': {
            'source_ids': ['KANTO_CASE', 'MLIT_CASE_REPRINT'],
            'KANTO_pdf_pages_1_based': [60, 61], 'KANTO_outer_printed_pages': [59, 60],
            'case_inner_printed_pages': [5, 6],
            'MLIT_reprint_pdf_pages_1_based': [338, 339], 'MLIT_reprint_printed_pages': [314, 315],
            'shipper': '佐川急便', 'carrier': '匿名X社',
            'business': 'interdepot_transport_not_ToC_last_mile',
            'exact_measurement_period': None, 'sample_size': None,
            'route_node_sequence': ['X社車庫', '木更津営業所', 'STLC', '東京C', '木更津営業所', '鴨川営業所', 'X社車庫'],
            'road_link_sequence': None, 'distance_km': None, 'T_s': None,
            'loading_wait_min_by_displayed_stage': [26, 26],
            'unloading_wait_min_by_displayed_stage': [72, 20],
            'loading_work_min_by_displayed_stage': [180, 229],
            'unloading_work_min_by_displayed_stage': [55, 37],
            'driving_min_by_displayed_stage': [25, 140, 105, 70],
            'duty_min_before_reported': 940,
            'departure_clock': '16:35', 'return_clock_next_day': '08:15',
            'sum_displayed_components_min': 985, 'unresolved_difference_min': 45,
            'ready_definition_matches_common_W': None,
            'W_after_loading_wait_min': None, 'W_improvement_percent': None,
            'adopted_as_A_performance': False,
            'reason': 'different business and cohort; loading ready undefined; averaged stages not consistent event logs',
        },
        'proposals': {
            'recommended_now': 'A qualitative reference with missing numeric values; same-condition quantitative B-C-D comparison',
            'four_way_human_option': 'A_human_new_research_observation_NOT_Sagawa_actual',
            'four_way_rule_option': 'A_rule_research_model_NOT_Sagawa_actual_or_human_time',
            'proposal_adopted': False,
            'future_relative_denominator_candidate': 'feasible B plan on same common problem',
            'baseline_W_zero_policy': 'ratio null; absolute difference only',
        },
    }
    (DOCS / 'A_SAGAWA_MANUAL_BASELINE.json').write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    fields = ['id', 'metric', 'driver_group', 'cohort_id', 'planning_method', 'before_absolute',
              'unit', 'after_absolute', 'normalized_before', 'normalized_after', 'improvement_percent',
              'adopted_as_A_performance', 'judgment', 'value_kind', 'reason', 'locator', 'source_ids', 'urls']
    with (DOCS / 'A_SAGAWA_MANUAL_BASELINE.csv').open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader()
        for record in records:
            row = {k: record[k] for k in fields}
            for k in ['source_ids', 'urls']: row[k] = '|'.join(row[k])
            w.writerow(row)
    print('7 target rows recorded; all manual-before D/W/T remain null; no optimization')


if __name__ == '__main__':
    main()
