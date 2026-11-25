"""A is two external administrative reference levels, never a generated plan."""
DISTANCE_SOURCE = 'https://www.mlit.go.jp/common/001106397.pdf'
WAIT_SOURCE = 'https://www.mlit.go.jp/report/press/content/002011131.pdf'
METHOD_SOURCE = 'https://www.revised-logistics-act-portal.mlit.go.jp/method/'


def external_reference(n):
    if type(n) is not int or n <= 0:
        raise ValueError('POSITIVE_DELIVERY_POINT_COUNT_REQUIRED')
    return {'reference_id': 'administrative-A-20261119-v2', 'role': 'external_reference',
            'D_ref_km': 0.58 * n, 'W_ref_min_per_operation': 60,
            'distance_source': DISTANCE_SOURCE, 'wait_source': WAIT_SOURCE,
            'definition_source': METHOD_SOURCE,
            'one_point_one_parcel': 'research_assumption',
            'same_observed_plan_pair': False,
            'distance_population': 'national_parcel_carriers',
            'wait_population': 'national_general_freight_actual_carriers',
            'representative_of_ota_toc': False,
            'gap_is_optimization_improvement_rate': False}


def compare_reference(result, n):
    ref = external_reference(n)
    mean = result['W_mean_min_per_operation']
    return {'reference_id': ref['reference_id'], 'D_ratio': result['D_km'] / ref['D_ref_km'],
            'W_delta_min_per_operation': mean - 60 if mean is not None else None,
            'interpretation': 'external_level_comparison_only_not_optimization_improvement'}
