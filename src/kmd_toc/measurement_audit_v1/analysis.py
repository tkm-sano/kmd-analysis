"""Measurement-gated extension of frozen descriptive statistics.

The original descriptive_v1 is preserved. New B-based dual improvement is an
explicit direct-comparison diagnostic, not a change to C-based final selection.
"""
from copy import deepcopy
from kmd_toc.descriptive_v1.analysis import analyze as describe, _pairs
from kmd_toc.descriptive_v1 import statistics as s
from kmd_toc.descriptive_v1.inputs import Reader, load_rows
from .measurement import cross_evaluate


class AuditedReader(Reader):
    def __init__(self, registration):
        super().__init__(registration)
        self.measurements = {}

    def metrics(self, raw, case):
        d, w = super().metrics(raw, case)
        proof = self.json(raw['outer_evidence'])
        if (not isinstance(raw.get('configuration_id'), str) or not raw['configuration_id'] or
                proof.get('configuration_id') != raw['configuration_id']):
            raise ValueError('HASH_BOUND_CONFIGURATION_ID_REQUIRED')
        settings = self.json(raw['configuration_evidence'])
        if (settings.get('configuration_id') != raw['configuration_id'] or
                proof.get('configuration_sha256') != raw['configuration_evidence']['sha256']):
            raise ValueError('REGISTERED_CONFIGURATION_HASH_MISMATCH')
        p, version = self.case(raw['scale'], case)
        if (settings.get('operating_version') != version or
                settings.get('problem_hash') != p.fingerprint or settings.get('od_hash') != p.od.fingerprint):
            raise ValueError('CONFIGURATION_PHYSICAL_CONDITIONS_MISMATCH')
        if version == 'FCFS_v1':
            from kmd_toc.common.models import load_plan
        else:
            from kmd_toc.duty_break_v1.models import load_plan
        plan = load_plan((self.base/raw['plan']['path']).resolve())
        result = cross_evaluate(p, plan)
        self.measurements[raw['trial_id']] = result
        if result['status'] != 'PASS': raise ValueError('COMMON_MEASUREMENT_AUDIT_FAIL')
        return d, w


def gated_analyze(registration, rows, evidence):
    """Gate is mandatory even for preloaded rows; no FAIL/HOLD leakage."""
    registration = deepcopy(registration)
    for by_metric in registration.get('A_references', {}).values():
        for ref in by_metric.values():
            if ref.get('kind') in ('A_rule_v1', 'rule_proxy') or ref.get('implementation_id') == 'A_rule_v1':
                ref['comparability_audit'] = {}
                ref['hold_reason'] = 'LEGACY_A_PROXY_IS_NOT_ADMINISTRATIVE_REFERENCE'
    rows = deepcopy(rows)
    for r in rows:
        # Fixture status is never automatically granted by the production entry.
        reason = None
        if r.get('measurement_status') != 'PASS': reason = 'COMMON_MEASUREMENT_NOT_PASS'
        if not r.get('outer_attempt') or r.get('unit_type') != 'outer_trial':
            reason = 'NOT_OUTER_TRIAL'
        if r.get('retry_of') or 'branch_id' in r: reason = 'INTERNAL_OR_RETRY_UNIT'
        if reason:
            previous = r.get('exclusion_reason')
            r.update(eligible=False, D=None, W=None,
                     exclusion_reason=previous+'; '+reason if previous else reason)
    # Reject mixed configurations/versions instead of silently pooling a grid.
    for scale in ('S1', 'S2', 'S3'):
        for method in ('B', 'C', 'D'):
            cell = [r for r in rows if r['scale'] == scale and r['method'] == method and r['eligible']]
            profiles = {r.get('comparison_profile') for r in cell}
            settings = {r.get('configuration_id') for r in cell}
            if len(profiles) > 1 or len(settings) > 1: raise ValueError('MIXED_CONDITIONS_OR_PARAMETER_SETTINGS')
        valid = [r for r in rows if r['scale'] == scale and r['eligible']]
        if len({r.get('comparison_profile') for r in valid}) > 1:
            raise ValueError('CROSS_METHOD_PHYSICAL_PROFILE_MISMATCH')
    result = describe(registration, rows, evidence)
    byid = {r['trial_id']: r for r in rows}
    duals = []
    for scale in ('S1', 'S2', 'S3'):
        for base in ('B', 'C'):
            design = next((d for d in registration.get('comparison_designs', [])
                           if (d['scale'], d['baseline'], d['comparison']) == (scale, base, 'D')), None)
            row = {'scale': scale, 'baseline': base, 'comparison': 'D',
                   'unit': 'percent', 'canonical_final_selection_reference': base == 'C',
                   'I_dual_of_means_percent': None, 'I_dual_of_means_fraction': None,
                   'mean_trial_I_dual_percent': None, 'SD_trial_I_dual_percent': None,
                   'MCSE_trial_I_dual_percent': None, 'strict_dual_fraction': None,
                   'undefined_trial_count': None, 'trial_values_percent': None,
                   'status': 'HOLD_NO_VALID_TRIALS', 'pairing_status': 'HOLD_NOT_ESTABLISHED'}
            a = [r for r in rows if (r['scale'], r['method']) == (scale, base) and r['eligible']]
            b = [r for r in rows if (r['scale'], r['method']) == (scale, 'D') and r['eligible']]
            means = [s.summary([r[m] for r in group])['mean'] for group in (a, b) for m in ('D', 'W')]
            if all(x is not None for x in means):
                value = s.dual(*means)
                row.update(I_dual_of_means_percent=value,
                           I_dual_of_means_fraction=value/100 if value is not None else None,
                           status='DEFINED_GROUP_MEANS_ONLY' if value is not None else 'UNDEFINED_ZERO_BASELINE')
            if design and design['kind'] != 'independent_groups':
                x, y, independent = _pairs(design, byid, evidence)
                vals = [s.dual(u['D'], u['W'], v['D'], v['W']) for u, v in zip(x, y)]
                summary = s.summary([v for v in vals if v is not None], independent=independent)
                row.update(mean_trial_I_dual_percent=summary['mean'],
                           SD_trial_I_dual_percent=summary['SD'], MCSE_trial_I_dual_percent=summary['MCSE'],
                           trial_values_percent=vals, undefined_trial_count=sum(v is None for v in vals),
                           strict_dual_fraction=sum(v['D'] < u['D'] and v['W'] < u['W'] for u, v in zip(x, y))/len(x) if x else None,
                           pairing_status='VERIFIED_REGISTERED_DESIGN',
                           independent_pairs=independent, valid_pair_count=len(x),
                           MCSE_status=summary['MCSE_status'])
            duals.append(row)
    for f in result['failures']:
        n = f['registered_outer_attempts']
        f['success_rate_per_registered_outer_attempt'] = f['valid_outer_records']/n if n else None
    for row in result['summaries']:
        f = next(f for f in result['failures'] if (f['scale'], f['method']) == (row['scale'], row['method']))
        row.update(observed_valid_outer_records=row['J'],
                   confirmed_independent_J=row['J'] if f['independence_confirmed'] else None,
                   success_rate=f['success_rate_per_registered_outer_attempt'],
                   status_counts=f['status_counts'], independence_confirmed=f['independence_confirmed'])
    for c in result['comparisons']:
        c['delta_unit'] = 'km' if c['metric'] == 'D' else 'min_total_loading_wait'
        c['relative_unit'] = 'percent'
        if c['baseline'] != 'A':
            x = next(r['mean'] for r in result['summaries'] if (r['scale'], r['method'], r['metric']) == (c['scale'], c['baseline'], c['metric']))
            y = next(r['mean'] for r in result['summaries'] if (r['scale'], r['method'], r['metric']) == (c['scale'], c['comparison'], c['metric']))
            c['relative_rate_of_means_percent'] = s.relative(x, y) if x is not None and y is not None else None
        else: c['relative_rate_of_means_percent'] = c.get('relative_rate_of_means')
        c['mean_trial_relative_rate_percent'] = (c.get('relative_rate_summary') or {}).get('mean')
    result.update(direct_dual_improvement=duals, audited_rows=rows,
                  measurement_gate='PASS_REQUIRED', internal_units_counted_as_J=False,
                  parameter_grid_counted_as_J=False)
    return result


def load_audited(registration, reader):
    if registration['data_role'] != 'synthetic_statistics_fixture':
        for scale, by_metric in registration.get('A_references', {}).items():
            for metric, ref in by_metric.items():
                try:
                    proof = reader.evidence(ref.get('provenance'))
                    if (proof.get('kind') != 'administrative_external_reference' or
                            proof.get('scale') != scale or proof.get('metric') != metric or
                            proof.get('converted_value') != ref.get('value') or
                            not proof.get('administrative_source_url') or not proof.get('conversion') or
                            proof.get('comparability_audit') != ref.get('comparability_audit')):
                        raise ValueError('A_ADMINISTRATIVE_PROVENANCE_OR_CONVERSION_UNCONFIRMED')
                except (ValueError, KeyError, OSError) as error:
                    ref['comparability_audit'] = {}
                    ref['hold_reason'] = str(error)
    rows = load_rows(registration, reader)
    for r in rows:
        # Synthetic arithmetic fixtures are explicit, and must still supply gate PASS.
        if registration['data_role'] == 'synthetic_statistics_fixture':
            r['measurement_status'] = r.get('measurement_status', 'HOLD')
        else:
            check = reader.measurements.get(r['trial_id'], {})
            r['measurement_status'] = check.get('status', 'HOLD')
            r['comparison_profile'] = registration.get('cases', {}).get(r['scale'], {}).get('comparison_profile')
    return rows
