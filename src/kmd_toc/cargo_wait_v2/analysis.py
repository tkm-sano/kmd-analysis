"""Keep direct method comparisons separate from external reference levels."""
from itertools import combinations
from pathlib import Path
import json
from .evaluation import VERSION, Event, Exclusion, evaluate, load_model
from .reference import external_reference, compare_reference
from kmd_toc.common.config import fingerprint, digest_file, read_json


def compare_methods(reports):
    pairs = []
    seen = set()
    for r in reports:
        if r.get('evaluation_version') != VERSION or r.get('method') not in ('B', 'C', 'D'):
            raise ValueError('LEGACY_W_OR_A_PLAN_FORBIDDEN')
        if r['method'] in seen:
            raise ValueError('ONE_PLAN_PER_METHOD_PER_COMPARISON')
        seen.add(r['method'])
    for left, right in combinations(reports, 2):
        if any(left[k] != right[k] for k in ('problem_hash', 'od_hash', 'model_hash')):
            raise ValueError('DIRECT_COMPARISON_CONDITION_MISMATCH')
        def delta(k):
            a, b = left[k], right[k]
            return b - a if a is not None and b is not None else None
        pairs.append({'left': left['method'], 'right': right['method'],
                      'D_delta_km': delta('D_km'), 'W_total_delta_min': delta('W_total_min'),
                      'W_mean_delta_min_per_operation': delta('W_mean_min_per_operation'),
                      'role': 'descriptive_plan_comparison',
                      'equal_planning_time_comparison_established': False,
                      'reason': 'common budget, measurement scope and deadline adoption rule remain unregistered'})
    return pairs


def write_evaluation(input_dir, plan_paths, output, *, model_path=None, event_path=None):
    """Read saved plans; exclusive output creation and source hash audit."""
    from kmd_toc.common.models import load_problem, load_plan
    from .evaluation import MODEL_PATH
    from .policy import load_policy, POLICY_PATH
    policy = load_policy()
    source = Path(input_dir).resolve()
    paths = [Path(p).resolve() for p in plan_paths]
    model_path = Path(model_path or MODEL_PATH).resolve()
    event_path = Path(event_path).resolve() if event_path else None
    output = Path(output).resolve()
    inputs = [p for p in source.rglob('*') if p.is_file()] + paths + [model_path, POLICY_PATH]
    if event_path:
        inputs.append(event_path)
    if source == output or source in output.parents or output in source.parents or any(output == p or output in p.parents for p in inputs):
        raise ValueError('OUTPUT_MUST_BE_SEPARATE_FROM_INPUTS')
    if output.exists():
        raise FileExistsError('EXISTING_OUTPUT_PRESERVED')
    hashes = {str(p): digest_file(p) for p in inputs}
    p = load_problem(source)
    model = load_model(model_path)
    # A sidecar is keyed by plan_id, each containing events, other_coverage and
    # optional planning_time_s. Omitted event observations remain missing.
    sidecars = read_json(event_path) if event_path else {}
    reports, plan_ids = [], []
    for path in paths:
        plan = load_plan(path)
        if plan.plan_id in plan_ids:
            raise ValueError('DUPLICATE_PLAN_ID')
        plan_ids.append(plan.plan_id)
        data = sidecars.get(plan.plan_id, {})
        if set(data) - {'events', 'other_coverage', 'planning_time_s'}:
            raise ValueError('SIDECAR_FIELDS')
        records = []
        for row in data.get('events', []):
            row = dict(row)
            if row.get('exclusions') is not None:
                row['exclusions'] = tuple(Exclusion(**x) for x in row['exclusions'])
            records.append(Event(**row))
        result = evaluate(p, plan, model=model, events=records,
                          other_coverage=data.get('other_coverage', ()),
                          planning_time_s=data.get('planning_time_s'))
        result['plan_id'] = plan.plan_id
        result['plan_sha256'] = hashes[str(path)]
        result['result_id'] = fingerprint(result)
        reports.append(result)
    if set(sidecars) - set(plan_ids):
        raise ValueError('UNUSED_SIDECAR_PLAN')
    if not reports:
        raise ValueError('PLAN_REQUIRED')
    direct = compare_methods(reports)
    result = {'evaluation_version': VERSION, 'research_policy': policy,
              'external_A': external_reference(len(p.stops)),
              'plans': reports, 'direct_BCD_comparisons': direct,
              'external_reference_comparisons': [{'method': r['method'], **compare_reference(r, len(p.stops))} for r in reports],
              'main_experiment': 'HOLD', 'statistical_hypothesis': 'NOT_TESTED',
              'axes': {'D': '総走行距離 [km]', 'W_total': '1運行全体の荷待ち時間総和 [分]',
                       'W_mean': '1運行当たり平均荷待ち時間 [分／運行]'},
              'limitations': ['Aの距離とWは異なる調査であり同一実績計画の一組ではない。',
                              '全国一般貨物のWと大田区ToCモデルの母集団は異なり代表性を保証しない。',
                              'Aとの差は実配送計画に対する最適化改善率ではない。',
                              '仮定モデルの0分は観測された0分ではない。',
                              '計画ごとの記述比較であり同一計画作成時間の性能検証ではない。']}
    if any(digest_file(path) != value for path, value in hashes.items()):
        raise ValueError('SOURCE_CHANGED_DURING_EVALUATION')
    output.mkdir(parents=True, exist_ok=False)
    for name, value in [('EVALUATION.json', result), ('SOURCE_HASHES.json', hashes)]:
        with (output / name).open('x') as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.write('\n')
    lines = ['# 版付き荷待ち評価（本実験ではない）', '',
             '|方式|D km|荷待ち総和 分|平均 分／運行|積込側 分|荷卸し側 分|発生率 %|全運行|欠測運行|T 秒（補助）|',
             '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    def value(v):
        return '欠測／未記録' if v is None else str(v)
    for r in reports:
        lines.append('|' + '|'.join([r['method'], *[value(r[k]) for k in ('D_km', 'W_total_min',
            'W_mean_min_per_operation', 'loading_W_min', 'unloading_W_min', 'wait_incidence_pct',
            'operation_count', 'missing_operation_count', 'T_program_s')]]) + '|')
    lines += ['', '## Aとの外部水準照合', '',
              f"A: D_ref={result['external_A']['D_ref_km']} km、W_ref=60 分／運行。Aの計画・Tは存在しない。", '',
              '|方式|D/D_ref|平均W−60 分／運行|', '|---|---:|---:|']
    for r in result['external_reference_comparisons']:
        lines.append(f"|{r['method']}|{value(r['D_ratio'])}|{value(r['W_delta_min_per_operation'])}|")
    lines += ['', *result['limitations'], '', '本実験HOLD。研究仮説は未検証。', '']
    (output / 'REPORT.md').write_text('\n'.join(lines))
    return result
